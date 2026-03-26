import re
from bs4 import BeautifulSoup
from app.schemas.app_listing import AppListingCreate


def parse_rating_distribution(soup: BeautifulSoup) -> list[dict]:
    """
    Parses rating distribution from spans like:
    '93% of ratings are 5 stars'
    Returns list of dicts: [{star: 5, percentage: 93.0}, ...]
    """
    distributions = []

    spans = soup.find_all(
        string=lambda t: t and "% of ratings are" in t and "star" in t
    )

    for span in spans:
        text = span.strip()
        # Extract percentage and star level
        match = re.search(r"([\d.]+)%\s+of ratings are\s+(\d+)\s+star", text)
        if match:
            percentage = float(match.group(1))
            star = int(match.group(2))
            distributions.append({
                "star": star,
                "percentage": percentage,
            })

    # Sort by star descending (5, 4, 3, 2, 1)
    distributions.sort(key=lambda x: x["star"], reverse=True)
    return distributions


def parse_app_page(soup: BeautifulSoup, app_url: str) -> tuple[AppListingCreate | None, list[dict]]:
    """
    Parses a single app page.
    Returns a tuple of (AppListingCreate, rating_distributions list)
    Returns (None, []) if parsing fails.
    """
    try:
        # --- App Name ---
        name_tag = soup.select_one("h1.tw-text-heading-lg")
        name = name_tag.text.strip() if name_tag else None
        if not name:
            print(f"[PARSER] Skipping {app_url} — no name found")
            return None, []

        # --- Developer ---
        developer_tag = soup.select_one("a[href*='/partners/']")
        developer = developer_tag.text.strip() if developer_tag else None

        # --- Description ---
        desc_tag = soup.select_one("p.tw-hidden.tw-text-body-md.tw-text-fg-secondary")
        description = desc_tag.text.strip() if desc_tag else None

        # --- Rating & Review Count ---
        rating = None
        review_count = None

        for dt in soup.select("dt"):
            if dt.text.strip() == "Rating":
                dd = dt.find_next_sibling()
                if dd:
                    dd_text = dd.text.strip()

                    # Extract rating e.g. "4.8"
                    rating_match = re.search(r"([\d.]+)", dd_text)
                    if rating_match:
                        rating = float(rating_match.group(1))

                    # Extract review count e.g. "(787)"
                    review_match = re.search(r"\(([\d,]+)\)", dd_text)
                    if review_match:
                        review_count = int(review_match.group(1).replace(",", ""))
                break

        # --- Icon URL ---
        icon_url = None
        icon_tag = soup.select_one("figure img")
        if icon_tag:
            icon_url = icon_tag.get("src")

        # --- Rating Distribution ---
        distributions = parse_rating_distribution(soup)

        # Calculate count per star from percentage + total reviews
        if review_count and distributions:
            for d in distributions:
                d["count"] = round((d["percentage"] / 100) * review_count)
        else:
            for d in distributions:
                d["count"] = 0

        app_data = AppListingCreate(
            name=name,
            developer=developer,
            description=description,
            category="upsell",  # will be overridden by pipeline
            rating=rating,
            review_count=review_count,
            no_of_downloads=None,
            app_url=app_url,
            icon_url=icon_url,
        )

        return app_data, distributions

    except Exception as e:
        print(f"[PARSER] Error parsing {app_url}: {e}")
        return None, []