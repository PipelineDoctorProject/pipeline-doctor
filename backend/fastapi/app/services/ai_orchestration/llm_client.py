import os
from typing import Optional

try:
    from groq import Groq
except ImportError:
    Groq = None


DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def get_default_llm_callable():
    api_key = os.getenv("GROQ_API_KEY")
    if Groq is None or not api_key:
        return None

    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    def invoke(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "Return only concise RCA reasoning plus the requested JSON object.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""

    return invoke


def get_configured_model_name() -> Optional[str]:
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    return None
