import os
import shutil
import tempfile
import logging
from datetime import datetime, timezone
import git
from celery import shared_task
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.scan import Scan
from app.models.secret import Secret
from app.models.repository import Repository
from app.scanner.engine import SecretScanner

logger = logging.getLogger("sentinel.tasks")

def calculate_scan_risk_score(secrets_found_list) -> float:
    """Calculate risk score from 0 (very insecure) to 100 (secure)."""
    score = 100.0
    for sec in secrets_found_list:
        sev = sec.get("severity", "medium").lower()
        if sev == "critical":
            score -= 10.0
        elif sev == "high":
            score -= 5.0
        elif sev == "medium":
            score -= 2.0
        else:
            score -= 0.5
    return max(0.0, score)

# Since we need celery_app.task decorator, we import the celery_app
from app.tasks.worker import celery_app

@celery_app.task(name="app.tasks.scan_tasks.run_repository_scan")
def run_repository_scan(scan_id: int, repository_id: int, clone_url: str, branch_name: str, access_token: str = None):
    logger.info(f"Starting scan task {scan_id} for repository {repository_id} on branch {branch_name}")
    db: Session = SessionLocal()
    
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        logger.error(f"Scan {scan_id} not found in database.")
        db.close()
        return False
        
    scan.status = "running"
    scan.started_at = datetime.now(timezone.utc)
    db.commit()
    
    # Create temporary directory inside the workspace/tmp
    temp_dir = tempfile.mkdtemp(prefix="sentinel_scan_", dir=os.getcwd())
    
    try:
        # 1. Clone repository
        logger.info(f"Cloning {clone_url} into {temp_dir}")
        
        # Support local folder mock scanning for testing: "local:///path/to/folder"
        if clone_url.startswith("local://"):
            local_path = clone_url.replace("local://", "")
            if not os.path.exists(local_path):
                raise ValueError(f"Local path {local_path} does not exist.")
            # Copy all files to temp_dir to simulate a clone
            shutil.copytree(local_path, temp_dir, dirs_exist_ok=True)
        else:
            # Inject token in HTTP/HTTPS URLs if present
            url = clone_url
            if access_token and clone_url.startswith("https://"):
                url = clone_url.replace("https://", f"https://oauth2:{access_token}@")
                
            # Clone with GitPython
            git.Repo.clone_from(url, temp_dir, branch=branch_name, depth=1)
            
        # 2. Count total files to scan
        total_files = 0
        for root, dirs, files in os.walk(temp_dir):
            # Ignore standard ignored dirs in counting
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules"}]
            total_files += len(files)
            
        # 3. Instantiate and run scanner
        scanner = SecretScanner(root_dir=temp_dir)
        findings = scanner.scan_directory()
        
        # 4. Save secrets to database
        db_secrets = []
        for finding in findings:
            secret_entry = Secret(
                scan_id=scan.id,
                repository_id=repository_id,
                file_path=finding["file_path"],
                line_number=finding["line_number"],
                column_number=finding["column_number"],
                secret_type=finding["secret_type"],
                detected_value_hashed=finding["detected_value_hashed"],
                masked_value=finding["masked_value"],
                entropy=finding["entropy"],
                severity=finding["severity"],
                raw_context=finding["raw_context"],
                status="active"
            )
            db_secrets.append(secret_entry)
            
        db.add_all(db_secrets)
        
        # 5. Update scan statistics
        scan.status = "completed"
        scan.finished_at = datetime.now(timezone.utc)
        scan.total_files = total_files
        scan.secrets_found = len(findings)
        scan.risk_score = calculate_scan_risk_score(findings)
        
        # Update Repository last sync metadata
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        if repo:
            repo.last_synced_at = datetime.now(timezone.utc)
            
        db.commit()
        logger.info(f"Scan task {scan_id} finished successfully. Found {len(findings)} secrets.")
        
    except Exception as e:
        logger.exception(f"Scan task {scan_id} failed with error: {str(e)}")
        db.rollback()
        scan.status = "failed"
        scan.finished_at = datetime.now(timezone.utc)
        scan.error_message = str(e)[:500]
        db.commit()
        
    finally:
        db.close()
        # Clean up cloned folder
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error removing temp scan dir {temp_dir}: {str(e)}")
                
    return True


@celery_app.task(name="app.tasks.scan_tasks.check_scheduled_scans")
def check_scheduled_scans():
    logger.info("Running scheduled scans check...")
    db: Session = SessionLocal()
    try:
        repos = db.query(Repository).filter(
            Repository.is_active == True,
            Repository.scan_schedule != "manual"
        ).all()
        
        for repo in repos:
            # Check latest completed/failed scan to know when the last check happened
            latest_scan = db.query(Scan).filter(
                Scan.repository_id == repo.id
            ).order_by(Scan.created_at.desc()).first()
            
            should_scan = False
            now = datetime.now(timezone.utc)
            
            if not latest_scan:
                should_scan = True
            else:
                last_scan_time = latest_scan.created_at
                # Ensure last_scan_time has timezone info (SQLite/MySQL usually naive)
                if last_scan_time.tzinfo is None:
                    last_scan_time = last_scan_time.replace(tzinfo=timezone.utc)
                    
                diff = now - last_scan_time
                if repo.scan_schedule == "daily" and diff.total_seconds() >= 86400:
                    should_scan = True
                elif repo.scan_schedule == "weekly" and diff.total_seconds() >= 604800:
                    should_scan = True
            
            if should_scan:
                logger.info(f"Triggering scheduled {repo.scan_schedule} scan for repository {repo.id} ({repo.name})")
                # Look for default branch or first branch record
                from app.models.repository import Branch
                branch = db.query(Branch).filter(
                    Branch.repository_id == repo.id,
                    Branch.is_default == True
                ).first()
                if not branch:
                    branch = db.query(Branch).filter(
                        Branch.repository_id == repo.id
                    ).first()
                
                branch_name = branch.name if branch else "main"
                if not branch:
                    branch = Branch(repository_id=repo.id, name=branch_name, is_default=True)
                    db.add(branch)
                    db.commit()
                    db.refresh(branch)
                
                # Create Scan record
                scan = Scan(
                    repository_id=repo.id,
                    branch_id=branch.id,
                    status="pending",
                    total_files=0,
                    secrets_found=0,
                    risk_score=0.0
                )
                db.add(scan)
                db.commit()
                db.refresh(scan)
                
                # Enqueue scanner run
                run_repository_scan.delay(
                    scan.id,
                    repo.id,
                    repo.clone_url,
                    branch.name,
                    repo.access_token
                )
    except Exception as e:
        logger.error(f"Error checking scheduled scans: {str(e)}")
    finally:
        db.close()
    return True
