# llm.py
import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()


def build_llm(api_key: str = None) -> LLM:
    """
    Single point of connection for the LLM.
    Config comes from .env: LLM_BASE_URL, MODEL_NAME, LLM_API_KEY
    (Groq now / Ollama locally / NVIDIA Brev on hackathon day).
    """
    return LLM(
        model=f"openai/{os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')}",
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        api_key=api_key or os.getenv("LLM_API_KEY", "not-needed"),
        temperature=0.4,
        max_tokens=4096,
    )