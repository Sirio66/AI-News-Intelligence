import requests

def summarize_text(text):
    try:
        prompt = f"Summarize this news article in 3 concise sentences:\n\n{text[:2000]}"

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )

        data = response.json()

        return data.get("response", "No summary generated.").strip()

    except Exception as e:
        print("LLM ERROR:", e)
        return "Summary unavailable."