import requests
from brain.memoria import DEFAULT_MODEL_HIGH, DEFAULT_MODEL

session = requests.Session()

def llama_query(prompt, model=DEFAULT_MODEL):
    response = session.post(
        "http://localhost:11500/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]
