import requests

session = requests.Session()

def llama_query(prompt):
    response = session.post(
        "http://localhost:11500/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )
    return response.json()["response"]
