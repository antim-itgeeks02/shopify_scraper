# test_scraper.py
from app.scraper.pipeline import run_pipeline

# Test with email-marketing category
run_pipeline(category="email-marketing")