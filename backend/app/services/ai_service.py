import logging
import requests
import json
from typing import Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger("sentinel.ai")

class AIService:
    @staticmethod
    def _call_llm(prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Unified LLM client calling Ollama, OpenAI, Gemini or falling back to high-fidelity mock.
        """
        # Try OpenAI if API key configured
        openai_key = getattr(settings, "OPENAI_API_KEY", None)
        gemini_key = getattr(settings, "GEMINI_API_KEY", None)
        ollama_url = getattr(settings, "OLLAMA_URL", "http://localhost:11434")

        # 1. Try Gemini API
        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                contents = []
                if system_instruction:
                    contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_instruction}"}]})
                contents.append({"role": "user", "parts": [{"text": prompt}]})
                
                payload = {"contents": contents}
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    logger.warning(f"Gemini API returned error code {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to call Gemini API: {str(e)}")

        # 2. Try OpenAI API
        if openai_key:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}"
                }
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                payload = {
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.2
                }
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"OpenAI API returned error code {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to call OpenAI API: {str(e)}")

        # 3. Try Ollama API
        if ollama_url:
            try:
                url = f"{ollama_url}/api/generate"
                payload = {
                    "model": "codellama",
                    "prompt": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2
                    }
                }
                response = requests.post(url, json=payload, timeout=15)
                if response.status_code == 200:
                    return response.json().get("response", "")
            except Exception as e:
                logger.debug(f"Ollama local endpoint not available: {str(e)}")

        # 4. High-fidelity Mock Fallback (so development works smoothly without setup)
        return ""

    @classmethod
    def explain_secret(cls, secret_type: str, context: str) -> Dict[str, Any]:
        """
        Generate details on danger description, risk level, exploitation scenario, and business impact.
        """
        prompt = (
            f"Analyze a leaked secret of type '{secret_type}' with this surrounding code context:\n"
            f"```\n{context}\n```\n"
            f"Explain: 1. Danger Description, 2. Exploit Scenario, 3. Business Impact.\n"
            f"Return your answer as a JSON object with keys: 'danger_description', 'risk_level' (critical/high/medium/low), 'exploitation_scenario', 'business_impact'."
        )
        
        system_instruction = "You are a senior DevSecOps scanner agent. You must respond ONLY with a raw JSON object containing the fields: danger_description, risk_level, exploitation_scenario, business_impact. Do not wrap in markdown code blocks."

        raw_response = cls._call_llm(prompt, system_instruction)
        
        # Clean response from markdown blocks if any
        if raw_response:
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            try:
                return json.loads(cleaned.strip())
            except Exception as e:
                logger.warning(f"Failed to parse LLM JSON: {cleaned}. Error: {str(e)}")

        # High-Fidelity Mock fallback structure
        mock_data = cls._generate_mock_explanation(secret_type)
        return mock_data

    @classmethod
    def generate_remediation(cls, secret_type: str, file_path: str, context: str) -> Dict[str, Any]:
        """
        Generate safe replacement code, env variable template, and rotation steps.
        """
        prompt = (
            f"Generate remediation for a leaked '{secret_type}' in file '{file_path}'.\n"
            f"Context:\n```\n{context}\n```\n"
            f"Provide: 1. Safe replacement code (e.g. reading from environment), 2. Safe Env file example, 3. Steps to rotate the key.\n"
            f"Return your answer as a JSON object with keys: 'safe_code', 'env_template', 'rotation_steps'."
        )
        
        system_instruction = "You are a security remediation assistant. Respond ONLY with a raw JSON object with keys: safe_code, env_template, rotation_steps. Do not include any markdown wrapper or explanation."

        raw_response = cls._call_llm(prompt, system_instruction)
        if raw_response:
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            try:
                return json.loads(cleaned.strip())
            except Exception as e:
                logger.warning(f"Failed to parse LLM JSON: {cleaned}. Error: {str(e)}")

        # Fallback Mock data
        return cls._generate_mock_remediation(secret_type, file_path)

    @classmethod
    def ask_security_question(cls, secret_type: str, context: str, question: str) -> str:
        """
        Answer specific security Q&A about a leaked credential.
        """
        prompt = (
            f"The developer has a question about a leaked '{secret_type}' secret in this context:\n"
            f"```\n{context}\n```\n"
            f"Developer's Question: {question}\n\n"
            f"Provide a clear, brief, actionable answer on how to rotate the secret, secure the code, or verify its status."
        )

        response = cls._call_llm(prompt, "You are a helpful DevSecOps security assistant.")
        if response:
            return response.strip()

        # Mock chat assistant response
        return cls._generate_mock_chat_response(secret_type, question)

    @staticmethod
    def _generate_mock_explanation(secret_type: str) -> Dict[str, Any]:
        sev = "high"
        if "private" in secret_type.lower() or "aws" in secret_type.lower() or "admin" in secret_type.lower():
            sev = "critical"
        elif "firebase" in secret_type.lower() or "stripe" in secret_type.lower():
            sev = "high"
        elif "url" in secret_type.lower() or "uri" in secret_type.lower():
            sev = "medium"

        return {
            "danger_description": f"The exposure of an active {secret_type} allows unauthorized third parties to bypass standard authentication controls and directly access protected backend resources, systems, or APIs.",
            "risk_level": sev,
            "exploitation_scenario": f"An attacker scans public git repositories, extracts the {secret_type}, and uses automated scripts to authenticate requests to the target service. They can then query metadata, download sensitive datasets, or run unauthorized workloads.",
            "business_impact": "Exposure can result in severe data leakage, compliance violations (e.g. GDPR, HIPAA, PCI-DSS), financial liability due to unauthorized api resource consumption, and significant loss of customer trust."
        }

    @staticmethod
    def _generate_mock_remediation(secret_type: str, file_path: str) -> Dict[str, Any]:
        env_var_name = secret_type.upper().replace(" ", "_").replace("-", "_") + "_KEY"
        if "AWS" in env_var_name:
            env_var_name = "AWS_SECRET_ACCESS_KEY"
        elif "OPENAI" in env_var_name:
            env_var_name = "OPENAI_API_KEY"

        # Determine extension language
        ext = file_path.split(".")[-1] if "." in file_path else "js"
        if ext in ["py", "python"]:
            safe_code = f"import os\n\n# Load {secret_type} securely from environment variables\napi_key = os.environ.get('{env_var_name}')"
        elif ext in ["js", "ts", "jsx", "tsx"]:
            safe_code = f"// Load {secret_type} securely from environment variables\nconst apiKey = process.env.{env_var_name};"
        else:
            safe_code = f"# Load secret from environment variables\nexport {env_var_name}=\"your_secure_value_here\""

        return {
            "safe_code": safe_code,
            "env_template": f"# Save this in a secure .env file (add .env to .gitignore)\n{env_var_name}=YOUR_ACTUAL_SECRET_VALUE",
            "rotation_steps": (
                f"1. Revoke the compromised secret immediately in your {secret_type} provider dashboard.\n"
                f"2. Generate a new credential/token from the provider console.\n"
                f"3. Populate the new key into your environment variables (e.g. in your hosting provider configuration or local .env file).\n"
                f"4. Verify that the application continues to run without hardcoded values."
            )
        }

    @staticmethod
    def _generate_mock_chat_response(secret_type: str, question: str) -> str:
        q_lower = question.lower()
        if "rotate" in q_lower or "revoke" in q_lower:
            return (
                f"To rotate this {secret_type}:\n"
                f"1. Log into the console/dashboard of the target service.\n"
                f"2. Navigate to the API credentials or security settings panel.\n"
                f"3. Generate a new credential and copy the token value securely.\n"
                f"4. Delete or disable the old (exposed) API key. Allow a small window if you need zero-downtime, but execute it quickly."
            )
        elif "false positive" in q_lower or "ignore" in q_lower:
            return (
                f"If this is a false positive (e.g. mock test keys), you can mark the status as 'False Positive' in the Sentinel AI dashboard. "
                f"Alternatively, you can add an inline comment like `# sentinel-ignore` or add the file to your `.sentinelignore` config file."
            )
        else:
            return (
                f"Regarding your question: '{question}'\n\n"
                f"For the leaked {secret_type}, we recommend that you do not keep this value in your source tree. "
                f"Always inject it dynamically through environment secrets (e.g. GitHub Actions secrets, Kubernetes Secrets, or AWS Secrets Manager)."
            )
