from fastapi import FastAPI, HTTPException, Query
from app.scraper.pipeline import run_pipeline
from app.scraper.crawler import CATEGORIES
from app.core.database import SessionLocal
from app.models.app_listing import AppListing
from app.models.rating_distribution import RatingDistribution
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Shopify Scraper API",
    description="Scrapes Shopify App Store - Multiple Categories",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "Shopify Scraper API is running",
        "supported_categories": list(CATEGORIES.keys()),
    }


# ─────────────────────────────────────────
# SCRAPE ENDPOINTS — one per category
# ─────────────────────────────────────────

@app.post("/scrape/upsell")
def scrape_upsell():
    """Scrape all apps from the Upsell & Bundles category."""
    try:
        run_pipeline(category="upsell")
        return {"message": "Upsell category scraped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/sales-channel")
def scrape_sales_channel():
    """Scrape all apps from the Sales Channels category."""
    try:
        run_pipeline(category="sales-channel")
        return {"message": "Sales Channel category scraped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/email-marketing")
def scrape_email_marketing():
    """Scrape all apps from the Email Marketing category."""
    try:
        run_pipeline(category="email-marketing")
        return {"message": "Email Marketing category scraped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/customer-support")
def scrape_customer_support():
    """Scrape all apps from the Customer Support category."""
    try:
        run_pipeline(category="customer-support")
        return {"message": "Customer Support category scraped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────
# QUERY ENDPOINTS
# ─────────────────────────────────────────

@app.get("/apps")
def get_apps(
    category: str | None = Query(None, description="Filter by category"),
    skip: int = Query(0, description="Pagination offset"),
    limit: int = Query(50, description="Number of results"),
):
    """
    Returns all scraped apps.
    Optionally filter by category: upsell, sales-channel, email-marketing, customer-support
    """
    db = SessionLocal()
    try:
        query = db.query(AppListing)

        if category:
            if category not in CATEGORIES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown category. Supported: {list(CATEGORIES.keys())}"
                )
            query = query.filter(AppListing.category == category)

        total = query.count()
        apps = query.offset(skip).limit(limit).all()

        return {
            "total": total,
            "category": category or "all",
            "skip": skip,
            "limit": limit,
            "apps": [
                {
                    "id": a.id,
                    "name": a.name,
                    "developer": a.developer,
                    "rating": a.rating,
                    "review_count": a.review_count,
                    "category": a.category,
                    "app_url": a.app_url,
                    "icon_url": a.icon_url,
                    "scraped_at": a.scraped_at,
                }
                for a in apps
            ],
        }
    finally:
        db.close()


@app.get("/apps/{app_id}")
def get_app(app_id: int):
    """
    Returns a single app by ID including full rating distribution.
    """
    db = SessionLocal()
    try:
        app_obj = db.query(AppListing).filter(AppListing.id == app_id).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="App not found")

        return {
            "id": app_obj.id,
            "name": app_obj.name,
            "developer": app_obj.developer,
            "description": app_obj.description,
            "category": app_obj.category,
            "rating": app_obj.rating,
            "review_count": app_obj.review_count,
            "app_url": app_obj.app_url,
            "icon_url": app_obj.icon_url,
            "scraped_at": app_obj.scraped_at,
            "rating_distribution": [
                {
                    "star": d.star,
                    "count": d.count,
                    "percentage": d.percentage,
                }
                for d in sorted(app_obj.rating_distributions, key=lambda x: x.star, reverse=True)
            ],
        }
    finally:
        db.close()


@app.get("/apps/{app_id}/ratings")
def get_app_ratings(app_id: int):
    """
    Returns only the rating distribution for a specific app.
    """
    db = SessionLocal()
    try:
        app_obj = db.query(AppListing).filter(AppListing.id == app_id).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="App not found")

        distributions = (
            db.query(RatingDistribution)
            .filter(RatingDistribution.app_id == app_id)
            .order_by(RatingDistribution.star.desc())
            .all()
        )

        return {
            "app_id": app_id,
            "app_name": app_obj.name,
            "overall_rating": app_obj.rating,
            "total_reviews": app_obj.review_count,
            "distribution": [
                {
                    "star": d.star,
                    "count": d.count,
                    "percentage": d.percentage,
                }
                for d in distributions
            ],
        }
    finally:
        db.close()


@app.get("/stats")
def get_stats():
    """
    Returns summary stats for all scraped categories.
    """
    db = SessionLocal()
    try:
        stats = []
        for cat in CATEGORIES.keys():
            count = db.query(AppListing).filter(AppListing.category == cat).count()
            stats.append({
                "category": cat,
                "total_apps": count,
            })

        total = db.query(AppListing).count()

        return {
            "total_apps_all_categories": total,
            "by_category": stats,
        }
    finally:
        db.close()