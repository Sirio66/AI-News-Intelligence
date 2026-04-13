from fastapi import FastAPI, BackgroundTasks
from .scraper import fetch_rss_articles
from .database import SessionLocal, engine
from .models import Base, Article
from .ranking import calculate_score
from .llm import summarize_text
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Automation Imports
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Set up logging so you can see the automation working in Render logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Deterministic AI News Intelligence Engine")

# AUTOMATION LOGIC

def run_pipeline():
    """The 'Brain' of the automation: runs everything in order."""
    logger.info("Auto-starting pipeline: Scrape -> Rank -> Summarize")
    try:
        scrape_news()
        rank_articles()
        summarize_articles()
        logger.info("✅ Pipeline complete! Your news is fresh.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

@app.on_event("startup")
async def startup_event():
    # 1. Run the pipeline immediately when the app wakes up
    run_pipeline()
    
    # 2. Start the clock to run it every 4 hours automatically
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, 'interval', hours=4)
    scheduler.start()
    logger.info("Scheduler started: News will refresh every 4 hours.")

# ROUTES

@app.get("/")
def root():
    return {"message": "Engine is running and automated"}

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
                summary="Summary pending...",
                score=0.0
            )
            db.add(new_article)
            saved_count += 1
    db.commit()
    db.close()
    return {"saved_articles": saved_count}

@app.get("/rank")
def rank_articles():
    db = SessionLocal()
    articles = db.query(Article).all()
    for article in articles:
        article.score = calculate_score(article)
    db.commit()
    ranked = db.query(Article).order_by(Article.score.desc()).limit(6).all()
    result = [{"title": a.title, "url": a.url, "score": a.score} for a in ranked]
    db.close()
    return result

@app.get("/summarize")
def summarize_articles():
    db = SessionLocal()
    articles = db.query(Article).order_by(Article.score.desc()).limit(6).all()
    summarized_count = 0
    for article in articles:
        # Check if content exists and it hasn't been summarized yet
        if article.content and (article.summary == "" or article.summary == "Summary pending..."):
            summary = summarize_text(article.content)
            article.summary = summary
            summarized_count += 1
    db.commit()
    db.close()
    return {"summarized_articles": summarized_count}

@app.get("/brief")
def generate_brief():
    db = SessionLocal()
    articles = db.query(Article).order_by(Article.score.desc()).limit(5).all()
    brief = []
    for i, article in enumerate(articles, start=1):
        brief.append({
            "rank": i,
            "title": article.title,
            "url": article.url,
            "summary": article.summary,
            "score": article.score
        })
    db.close()
    return {"top_news_brief": brief}

# UI SERVING

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
def serve_ui():
    return FileResponse("static/index.html")