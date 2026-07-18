import os
import tempfile
import pytest
from app.scanner.engine import SecretScanner, calculate_entropy, get_severity

def test_calculate_entropy():
    # Low entropy strings (repeated characters)
    assert calculate_entropy("aaaaaaa") == 0.0
    # High entropy strings (random-like)
    assert calculate_entropy("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789") > 4.5
    assert calculate_entropy("") == 0.0

def test_get_severity():
    assert get_severity("Generic Private Key") == "critical"
    assert get_severity("AWS Access Key ID") == "high"
    assert get_severity("Slack Token") == "medium"
    assert get_severity("Unknown Secret Type") == "low"

def test_scanner_engine_regex_matching():
    # Setup temporary directory for test scan
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file containing mock secrets
        test_file = os.path.join(temp_dir, "config.py")
        with open(test_file, "w") as f:
            f.write("# AWS credentials\n")
            f.write("AWS_KEY = \"AKIAIOSFODNN7EXAMPLE\"\n")
            f.write("AWS_SECRET = \"aws_secret_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\"\n")
            f.write("# OpenAI API Key\n")
            f.write("OPENAI_KEY = \"sk-proj-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF1234\"\n")
            f.write("# Database link\n")
            f.write("CONN_STRING = \"postgres://db_user:my_secret_pass@127.0.0.1:5432/my_database\"\n")
            f.write("# Safe code line\n")
            f.write("port = 8080\n")
            
        scanner = SecretScanner(root_dir=temp_dir)
        findings = scanner.scan_directory()
        
        # Verify findings
        found_types = {f["secret_type"] for f in findings}
        assert "AWS Access Key ID" in found_types
        assert "OpenAI API Key" in found_types
        assert "Database Connection String" in found_types
        
        # Verify specific counts and fields
        assert len(findings) >= 3
        for f in findings:
            assert f["file_path"] == "config.py"
            assert f["masked_value"] != f["raw_secret"]
            assert len(f["detected_value_hashed"]) == 64  # SHA256 hex string length
            assert "raw_secret" in f

def test_scanner_entropy_credential_detection():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "auth_keys.yaml")
        with open(test_file, "w") as f:
            # High entropy custom key assignment
            f.write("custom_token: \"zX19$pL@92K!qP8#mN5*bV3&yT7^rE1\"\n")
            # Low entropy values should be ignored
            f.write("env: \"development\"\n")
            
        scanner = SecretScanner(root_dir=temp_dir)
        findings = scanner.scan_directory()
        
        assert len(findings) == 1
        assert findings[0]["secret_type"] == "High Entropy Credential"
        assert findings[0]["file_path"] == "auth_keys.yaml"
        assert findings[0]["entropy"] > 3.8
