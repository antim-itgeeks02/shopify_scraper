import time
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session

from app.scraper.crawler import crawl_category, scrape_page_with_playwright, CATEGORIES
from app.scraper.parser import parse_app_page
from app.models.app_listing import AppListing
from app.models.rating_distribution import RatingDistribution
from app.core.database import SessionLocal


def app_exists(db: Session, app_url: str) -> bool:
    """Check if an app URL already exists in DB."""
    return db.query(AppListing).filter(AppListing.app_url == app_url).first() is not None


def save_app(db: Session, data, distributions: list[dict], category: str) -> bool:
    """
    Save a parsed app + its rating distributions to the database.
    Returns True if saved, False if skipped (duplicate).
    """
    if app_exists(db, data.app_url):
        print(f"  [SKIP] Already exists: {data.app_url}")
        return False

    # Save app listing
    app = AppListing(
        name=data.name,
        developer=data.developer,
        description=data.description,
        category=category,
        rating=data.rating,
        review_count=data.review_count,
        no_of_downloads=data.no_of_downloads,
        app_url=data.app_url,
        icon_url=data.icon_url,
    )
    db.add(app)
    db.flush()  # get app.id before committing

    # Save rating distributions
    for d in distributions:
        dist = RatingDistribution(
            app_id=app.id,
            star=d["star"],
            count=d.get("count", 0),
            percentage=d.get("percentage"),
        )
        db.add(dist)

    db.commit()
    db.refresh(app)
    return True


def run_pipeline(category: str = "upsell"):
    """
    Full pipeline for a given category:
    1. Crawl all app URLs
    2. Parse each app page
    3. Save to PostgreSQL with rating distributions

    Supported categories: upsell, sales-channel, email-marketing, customer-support
    """
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. "
            f"Supported: {list(CATEGORIES.keys())}"
        )

    print("\n" + "="*50)
    print(f"SHOPIFY SCRAPER PIPELINE STARTED")
    print(f"Category: {category}")
    print("="*50 + "\n")

    # Step 1 — Crawl all URLs
    print(f"[PIPELINE] Step 1: Crawling category '{category}'...")
    app_urls = crawl_category(category)
    print(f"[PIPELINE] Found {len(app_urls)} apps to scrape\n")

    # Step 2 — Parse & Save each app
    print("[PIPELINE] Step 2: Parsing and saving each app...")

    db = SessionLocal()
    saved = 0
    skipped = 0
    failed = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for i, url in enumerate(app_urls, 1):
                print(f"\n[{i}/{len(app_urls)}] {url}")

                try:
                    # Fetch and parse
                    soup = scrape_page_with_playwright(url, page)
                    app_data, distributions = parse_app_page(soup, url)

                    if app_data is None:
                        print(f"  [FAILED] Could not parse")
                        failed += 1
                        continue

                    # Save to DB
                    was_saved = save_app(db, app_data, distributions, category)
                    if was_saved:
                        print(f"  [SAVED] {app_data.name} | ⭐ {app_data.rating} | 💬 {app_data.review_count} | 📊 {len(distributions)} star levels")
                        saved += 1
                    else:
                        skipped += 1

                except Exception as e:
                    print(f"  [ERROR] {e}")
                    failed += 1

                time.sleep(1)

            browser.close()

    finally:
        db.close()

    # Summary
    print("\n" + "="*50)
    print("PIPELINE COMPLETE")
    print(f"  Category: {category}")
    print(f"  ✅ Saved:   {saved}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Failed:  {failed}")
    print(f"  📦 Total:   {len(app_urls)}")
    print("="*50 + "\n")