import os
import re
import math
from collections import Counter
from typing import List, Dict, Any, Set

# Regex patterns for deterministic secret matching
SECRET_PATTERNS = {
    "AWS Access Key ID": r"\b(?:AKIA|ASCA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA)[A-Z0-9]{16}\b",
    "AWS Secret Access Key": r"(?i)aws_(?:secret|key|secret_key)?\s*[:=]\s*['\"]?([a-zA-Z0-9/+=]{40})['\"]?",
    "OpenAI API Key": r"\bsk-(?:proj-)?[a-zA-Z0-9]{32,}\b",
    "Google API Key": r"\bAIzaSy[a-zA-Z0-9-_]{35}\b",
    "Stripe API Key": r"\bsk_(?:live|test)_[0-9a-zA-Z]{24}\b",
    "Slack Token": r"\bxox[baprs]-[0-9a-zA-Z]{10,}-?[0-9a-zA-Z]{10,}-?[0-9a-zA-Z]{10,}\b",
    "Slack Webhook URL": r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,11}/B[a-zA-Z0-9_]{8,11}/[a-zA-Z0-9_]{24}",
    "GitHub Personal Access Token": r"\bghp_[a-zA-Z0-9]{36}\b",
    "GitHub OAuth Access Token": r"\bgho_[a-zA-Z0-9]{36}\b",
    "Database Connection String": r"\b(?:postgres|postgresql|mongodb|mysql|redis)://[a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+:\d+/[a-zA-Z0-9_.-]+\b",
    "Generic Private Key": r"-----BEGIN (?:RSA|EC|DSA|GPG|OPENSSH|PRIVATE) KEY-----",
    "Twilio Account SID": r"\bAC[a-fA-F0-9]{32}\b",
    "Firebase Config URL": r"https://[a-zA-Z0-9-]+\.firebaseio\.com",
    "Heroku API Key": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
}

# Directories and files to always ignore
DEFAULT_IGNORED_DIRS = {
    ".git", ".github", ".vscode", "node_modules", "venv", ".venv", "env",
    "target", "build", "dist", "out", "coverage", ".idea", ".pytest_cache"
}

DEFAULT_IGNORED_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "cargo.lock", 
    "poetry.lock", "mix.lock", "composer.lock", "Gemfile.lock"
}

# Image, binary, and document extensions to skip
IGNORED_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    # Binaries/Archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".pdf", ".exe", ".dll", ".so", ".dylib", ".class", ".pyc",
    # Audio/Video
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    # Fonts
    ".woff", ".woff2", ".ttf", ".eot"
}

def calculate_entropy(text: str) -> float:
    """Calculate Shannon Entropy of a string to identify random high-entropy strings."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    counts = Counter(text)
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def get_severity(secret_type: str) -> str:
    """Return severity based on secret type."""
    critical_types = {"Generic Private Key", "AWS Secret Access Key", "Database Connection String"}
    high_types = {"AWS Access Key ID", "OpenAI API Key", "Stripe API Key", "GitHub Personal Access Token"}
    medium_types = {"Google API Key", "Slack Token", "Slack Webhook URL", "Twilio Account SID", "Heroku API Key"}
    
    if secret_type in critical_types:
        return "critical"
    elif secret_type in high_types:
        return "high"
    elif secret_type in medium_types:
        return "medium"
    return "low"

class SecretScanner:
    def __init__(self, root_dir: str, ignore_rules: Set[str] = None):
        self.root_dir = root_dir
        self.ignore_rules = ignore_rules or set()
        
    def should_ignore(self, path: str) -> bool:
        """Verify if a path or file should be ignored based on global rules and custom ignores."""
        parts = os.path.split(path)
        # Check if any path segment matches ignored directories
        for part in parts:
            if part in DEFAULT_IGNORED_DIRS:
                return True
        
        filename = os.path.basename(path)
        if filename in DEFAULT_IGNORED_FILES:
            return True
            
        _, ext = os.path.splitext(filename)
        if ext.lower() in IGNORED_EXTENSIONS:
            return True
            
        # Custom ignore rules (simple substring matches for paths)
        for rule in self.ignore_rules:
            if rule and rule in path:
                return True
                
        return False

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a single file for secret patterns and high entropy strings."""
        findings = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                
            for line_idx, line in enumerate(lines):
                # 1. Regex scanning
                for secret_type, pattern in SECRET_PATTERNS.items():
                    matches = re.finditer(pattern, line)
                    for m in matches:
                        matched_str = m.group(0)
                        start_col = m.start() + 1
                        
                        # Double check entropy for certain generic matches to reduce false positives
                        entropy = calculate_entropy(matched_str)
                        if secret_type == "AWS Secret Access Key" and entropy < 3.0:
                            continue
                            
                        # Generate masked display value
                        masked = matched_str
                        if len(matched_str) > 8:
                            masked = matched_str[:4] + "..." + matched_str[-4:]
                        else:
                            masked = "****"
                            
                        # Context generation: clean line and mask matched secret
                        context_line = line.replace(matched_str, masked).strip()
                        
                        # Hashed value for DB tracking
                        # We use simple SHA256 or prefix matching, let's store a hash (SHA256 representation)
                        import hashlib
                        hashed = hashlib.sha256(matched_str.encode("utf-8")).hexdigest()
                        
                        rel_path = os.path.relpath(file_path, self.root_dir)
                        findings.append({
                            "file_path": rel_path,
                            "line_number": line_idx + 1,
                            "column_number": start_col,
                            "secret_type": secret_type,
                            "raw_secret": matched_str, # Keep it temporarily for worker, worker will hash it
                            "detected_value_hashed": hashed,
                            "masked_value": masked,
                            "entropy": round(entropy, 2),
                            "severity": get_severity(secret_type),
                            "raw_context": context_line
                        })
                        
                # 2. Variable assignment entropy scan for potential custom keys
                # Matches patterns like api_key = "...", db_password = "..."
                entropy_match = re.search(r"\b[a-zA-Z0-9_-]*(?:api_key|apikey|secret|password|passwd|private_key|token|access_key)[a-zA-Z0-9_-]*\s*[:=]\s*['\"]([^'\"]{16,})['\"]", line, re.IGNORECASE)
                if entropy_match:
                    val = entropy_match.group(1)
                    entropy = calculate_entropy(val)
                    # High entropy (typically > 3.8 for base64/hex keys)
                    if entropy > 3.8 and not any(finding["raw_secret"] == val for finding in findings):
                        start_col = line.find(val) + 1
                        masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "****"
                        context_line = line.replace(val, masked).strip()
                        
                        import hashlib
                        hashed = hashlib.sha256(val.encode("utf-8")).hexdigest()
                        
                        rel_path = os.path.relpath(file_path, self.root_dir)
                        findings.append({
                            "file_path": rel_path,
                            "line_number": line_idx + 1,
                            "column_number": start_col,
                            "secret_type": "High Entropy Credential",
                            "raw_secret": val,
                            "detected_value_hashed": hashed,
                            "masked_value": masked,
                            "entropy": round(entropy, 2),
                            "severity": "medium",
                            "raw_context": context_line
                        })
                        
        except Exception as e:
            # Fallback if file read fails
            pass
            
        return findings

    def scan_directory(self) -> List[Dict[str, Any]]:
        """Walk the directory and scan all valid files."""
        all_findings = []
        for root, dirs, files in os.walk(self.root_dir):
            # Prune directories in place to avoid visiting ignored paths
            dirs[:] = [d for d in dirs if not self.should_ignore(os.path.join(root, d))]
            
            for file in files:
                full_path = os.path.join(root, file)
                if not self.should_ignore(full_path):
                    file_findings = self.scan_file(full_path)
                    all_findings.extend(file_findings)
                    
        return all_findings
