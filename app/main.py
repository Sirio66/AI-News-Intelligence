from fastapi import FastAPI
from .scraper import fetch_rss_articles
from .database import SessionLocal, engine
from .models import Base, Article
from .ranking import calculate_score
from .llm import summarize_text
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Deterministic AI News Intelligence Engine")


@app.get("/")
def root():
    return {"message": "Engine is running"}


# ----------------------------
# SCRAPE
# ----------------------------
@app.get("/scrape")
def scrape_news():
    rss_url = "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
    articles = fetch_rss_articles(rss_url)

    db = SessionLocal()
    saved_count = 0

    for item in articles:
        existing = db.query(Article).filter(Article.url == item["url"]).first()

        if not existing:
            new_article = Article(
                title=item["title"],
                url=item["url"],
                content=item.get("content", ""),
                summary="",
                score=0.0
            )
            db.add(new_article)
            saved_count += 1

    db.commit()
    db.close()

    return {"saved_articles": saved_count}


# ----------------------------
# RANK
# ----------------------------
@app.get("/rank")
def rank_articles():
    db = SessionLocal()

    articles = db.query(Article).all()

    for article in articles:
        article.score = calculate_score(article)

    db.commit()

    ranked = (
        db.query(Article)
        .order_by(Article.score.desc())
        .limit(6)
        .all()
    )

    result = [
        {
            "title": a.title,
            "url": a.url,
            "score": a.score
        }
        for a in ranked
    ]

    db.close()
    return result


# ----------------------------
# SUMMARIZE
# ----------------------------
@app.get("/summarize")
def summarize_articles():
    db = SessionLocal()

    articles = (
        db.query(Article)
        .order_by(Article.score.desc())
        .limit(6)
        .all()
    )

    summarized_count = 0

    for article in articles:
        if article.content and article.content.strip() != "":
            summary = summarize_text(article.content)
            article.summary = summary
            summarized_count += 1

    db.commit()
    db.close()

    return {"summarized_articles": summarized_count}


# ----------------------------
# BRIEF (NEW 🔥)
# ----------------------------
@app.get("/brief")
def generate_brief():
    db = SessionLocal()

    articles = (
        db.query(Article)
        .order_by(Article.score.desc())
        .limit(5)
        .all()
    )

    brief = []

    for i, article in enumerate(articles, start=1):
        brief.append({
            "rank": i,
            "title": article.title,
            "summary": article.summary,
            "score": article.score
        })

    db.close()

    return {
        "top_news_brief": brief
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
def serve_ui():
    return FileResponse("static/index.html")