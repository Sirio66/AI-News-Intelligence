from .models import Article


def calculate_score(article: Article) -> float:
    """
    Deterministic scoring logic.
    No AI involved.
    """

    score = 0.0

    # Title length factor
    if article.title:
        score += len(article.title) * 0.1

    # Keyword boost
    important_keywords = [
        "AI",
        "OpenAI",
        "Microsoft",
        "Google",
        "Apple",
        "security",
        "cyber",
        "data",
        "startup",
        "LLM"
    ]

    for keyword in important_keywords:
        if keyword.lower() in article.title.lower():
            score += 5.0

    return round(score, 2)
