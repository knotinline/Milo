import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "chatgpt": {
        "label": "ChatGPT",
        "api_key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
        "base_url": None,
    },
    "deepseek": {
        "label": "DeepSeek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_env": "DEEPSEEK_MODEL",
        "default_model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
    },
}


def _mock_response(messages: List[Dict[str, str]], provider: str) -> str:
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    low = user.lower()
    label = PROVIDERS[provider]["label"]
    if "photosynthesis" in low:
        return "Photosynthesis is how plants use sunlight, water, and carbon dioxide to make their own food. They also release oxygen, which helps animals and people breathe."
    if "drugs" in low:
        return "Drugs are chemicals that change how the body or brain works. Some medicines are used safely with doctors, but illegal or misused drugs can be dangerous. It is best to ask a teacher, parent, or doctor for trusted information."
    return f"This is a safe demo response from {label} mock mode. Add an API key in .env to use the real {label} API."


def moderate(text: str) -> Optional[Dict[str, Dict[str, float]]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_key_here":
        return None

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.moderations.create(model="omni-moderation-latest", input=text)
    result = response.results[0]
    return {
        "scores": result.category_scores.model_dump(),
        "categories": result.categories.model_dump(),
    }


def call_model(messages: List[Dict[str, str]], provider: str) -> str:
    config = PROVIDERS[provider]
    api_key = os.getenv(config["api_key_env"])
    model = os.getenv(config["model_env"], config["default_model"])

    if not api_key or api_key == "your_key_here":
        return _mock_response(messages, provider)

    from openai import OpenAI

    client_kwargs = {"api_key": api_key}
    if config["base_url"]:
        client_kwargs["base_url"] = config["base_url"]

    client = OpenAI(**client_kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.4,
    )
    return response.choices[0].message.content or ""
