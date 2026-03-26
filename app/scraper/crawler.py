import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://apps.shopify.com"

# All supported categories
CATEGORIES = {
    "upsell": "https://apps.shopify.com/categories/marketing-and-conversion-upsell-and-bundles",
    "sales-channel": "https://apps.shopify.com/categories/sales-channels",
    "email-marketing": "https://apps.shopify.com/categories/marketing-and-conversion-marketing-email-marketing",
    "customer-support": "https://apps.shopify.com/categories/store-management-support",
}

EXCLUDED_PATHS = [
    "/categories", "/stories", "/sitemap",
    "/partner", "/blog", "/privacy",
    "/terms", "/search"
]


def get_app_urls_from_page(soup: BeautifulSoup) -> list[str]:
    """Extracts all clean app URLs from a page."""
    app_urls = []
    all_links = soup.select("a[href*='apps.shopify.com/']")

    for link in all_links:
        href = link.get("href", "")
        clean_url = href.split("?")[0].rstrip("/")

        if not clean_url or "apps.shopify.com" not in clean_url:
            continue
        if clean_url == "https://apps.shopify.com":
            continue
        if any(path in clean_url for path in EXCLUDED_PATHS):
            continue

        path = clean_url.replace("https://apps.shopify.com", "")
        if not path or "/" not in path:
            continue

        if clean_url not in app_urls:
            app_urls.append(clean_url)

    return app_urls


def get_subcategory_urls(soup: BeautifulSoup, category_slug: str) -> list[str]:
    """Extracts only real subcategory URLs for a given category."""
    subcategory_urls = []
    all_links = soup.select(f"a[href*='{category_slug}-']")

    for link in all_links:
        href = link.get("href", "").split("?")[0].rstrip("/")

        if "/categories/" not in href:
            continue
        if href and href not in subcategory_urls:
            subcategory_urls.append(href)

    return subcategory_urls


def scrape_page_with_playwright(url: str, page) -> BeautifulSoup:
    """
    Navigates to a URL and scrolls until no new content loads.
    Returns BeautifulSoup of the final page.
    """
    print(f"[CRAWLER] Fetching → {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    previous_count = 0
    scroll_attempts = 0

    while scroll_attempts < 15:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        soup = BeautifulSoup(page.content(), "lxml")
        current_count = len(get_app_urls_from_page(soup))

        print(f"  Scroll {scroll_attempts + 1} → {current_count} apps")

        if current_count == previous_count:
            print(f"  No new apps — done scrolling")
            break

        previous_count = current_count
        scroll_attempts += 1

    return BeautifulSoup(page.content(), "lxml")


def crawl_category(category: str = "upsell") -> list[str]:
    """
    Crawls a given category + all its subcategories.
    Returns deduplicated list of all app URLs.

    Supported categories: upsell, sales-channel, email-marketing, customer-support
    """
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. "
            f"Supported: {list(CATEGORIES.keys())}"
        )

    category_url = CATEGORIES[category]

    # Extract slug from URL for subcategory detection
    # e.g. "marketing-and-conversion-upsell-and-bundles"
    category_slug = category_url.split("/categories/")[1]

    all_urls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Step 1 — scrape main category page
        print(f"\n[STEP 1] Scraping main category: {category}")
        main_soup = scrape_page_with_playwright(category_url, page)
        main_urls = get_app_urls_from_page(main_soup)
        print(f"[STEP 1] Found {len(main_urls)} apps on main page")

        for url in main_urls:
            if url not in all_urls:
                all_urls.append(url)

        # Step 2 — find subcategories
        subcategory_urls = get_subcategory_urls(main_soup, category_slug)
        print(f"\n[STEP 2] Found {len(subcategory_urls)} subcategories:")
        for s in subcategory_urls:
            print(f"  → {s}")

        # Step 3 — scrape each subcategory
        for i, subcat_url in enumerate(subcategory_urls, 1):
            print(f"\n[STEP 3.{i}] Scraping subcategory: {subcat_url}")
            subcat_soup = scrape_page_with_playwright(subcat_url, page)
            subcat_urls = get_app_urls_from_page(subcat_soup)
            print(f"[STEP 3.{i}] Found {len(subcat_urls)} apps")

            new_count = 0
            for url in subcat_urls:
                if url not in all_urls:
                    all_urls.append(url)
                    new_count += 1
            print(f"[STEP 3.{i}] {new_count} new unique apps added")

            time.sleep(1)

        browser.close()

    print(f"\n[CRAWLER] Total unique apps found: {len(all_urls)}")
    return all_urls