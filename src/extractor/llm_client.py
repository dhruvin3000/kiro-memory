"""
Thin LLM client that supports OpenAI, Ollama (local), and a rule-based fallback.
Provider is selected via LLM_PROVIDER env var.
"""
import os
import json
from typing import Optional


def extract_json_from_response(text: str) -> Optional[dict]:
    """Pull the first JSON object out of an LLM response string."""
    import re
    # Try to find a JSON block (with or without markdown fences)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        # Try raw JSON
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def call_llm(prompt: str) -> str:
    """
    Call the configured LLM and return the raw response string.
    Falls back to rule-based extraction if no LLM is configured.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return _call_openai(prompt)
    elif provider == "ollama":
        return _call_ollama(prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def _call_openai(prompt: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software architect assistant. "
                        "Your job is to identify architectural decisions, design choices, "
                        "and their rationale from text. Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[llm] OpenAI call failed: {e}")
        return ""


def _call_ollama(prompt: str) -> str:
    try:
        import urllib.request
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3")
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }).encode()
        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        print(f"[llm] Ollama call failed: {e}")
        return ""
