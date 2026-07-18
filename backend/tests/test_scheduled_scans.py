import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app import models
from app.tasks.scan_tasks import check_scheduled_scans

@pytest.fixture
def mock_db_repos(db):
    user = models.User(
        email="test_scheduler@example.com",
        hashed_password="fakehashpassword",
        first_name="Test",
        last_name="User",
        is_active=True,
        role="developer"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 1. Daily repo
    repo_daily = models.Repository(
        user_id=user.id,
        name="daily-repo",
        clone_url="https://github.com/test/daily.git",
        provider="github",
        scan_schedule="daily",
        is_active=True
    )
    # 2. Weekly repo
    repo_weekly = models.Repository(
        user_id=user.id,
        name="weekly-repo",
        clone_url="https://github.com/test/weekly.git",
        provider="github",
        scan_schedule="weekly",
        is_active=True
    )
    # 3. Manual repo
    repo_manual = models.Repository(
        user_id=user.id,
        name="manual-repo",
        clone_url="https://github.com/test/manual.git",
        provider="github",
        scan_schedule="manual",
        is_active=True
    )
    
    db.add(repo_daily)
    db.add(repo_weekly)
    db.add(repo_manual)
    db.commit()
    
    # Create default branches for them
    b_daily = models.Branch(repository_id=repo_daily.id, name="main", is_default=True)
    b_weekly = models.Branch(repository_id=repo_weekly.id, name="main", is_default=True)
    b_manual = models.Branch(repository_id=repo_manual.id, name="main", is_default=True)
    db.add(b_daily)
    db.add(b_weekly)
    db.add(b_manual)
    db.commit()
    
    return {
        "daily": repo_daily,
        "weekly": repo_weekly,
        "manual": repo_manual
    }

@patch("app.tasks.scan_tasks.run_repository_scan.delay")
@patch("app.tasks.scan_tasks.SessionLocal")
def test_check_scheduled_scans_triggers(mock_session_local, mock_delay, db, mock_db_repos):
    # Override SessionLocal inside task to use our test DB connection
    mock_session_local.return_value = db
    
    # First run: daily and weekly should trigger (as no scans exist)
    check_scheduled_scans()
    
    # Assert delay task was called twice (for daily and weekly)
    assert mock_delay.call_count == 2
    
    # Reset mock and assert running again does not trigger (scans were just created)
    mock_delay.reset_mock()
    check_scheduled_scans()
    mock_delay.assert_not_called()

@patch("app.tasks.scan_tasks.run_repository_scan.delay")
@patch("app.tasks.scan_tasks.SessionLocal")
def test_check_scheduled_scans_respects_intervals(mock_session_local, mock_delay, db, mock_db_repos):
    mock_session_local.return_value = db
    
    daily_repo = mock_db_repos["daily"]
    weekly_repo = mock_db_repos["weekly"]
    
    # Add a completed scan from 12 hours ago for daily_repo
    scan_daily_recent = models.Scan(
        repository_id=daily_repo.id,
        branch_id=1,
        status="completed",
        created_at=datetime.utcnow() - timedelta(hours=12)
    )
    db.add(scan_daily_recent)
    
    # Add a completed scan from 8 days ago for weekly_repo (should trigger scan)
    scan_weekly_old = models.Scan(
        repository_id=weekly_repo.id,
        branch_id=2,
        status="completed",
        created_at=datetime.utcnow() - timedelta(days=8)
    )
    db.add(scan_weekly_old)
    db.commit()
    
    check_scheduled_scans()
    
    # Only weekly_repo scan should be triggered (1 call)
    assert mock_delay.call_count == 1
