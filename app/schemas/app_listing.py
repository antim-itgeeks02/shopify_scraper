from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.rating_distribution import RatingDistributionResponse


class AppListingBase(BaseModel):
    name: str
    developer: str | None = None
    description: str | None = None
    category: str = "upsell"
    rating: float | None = None
    review_count: int | None = None
    no_of_downloads: str | None = None
    app_url: str
    icon_url: str | None = None


class AppListingCreate(AppListingBase):
    """Used when inserting a new record into DB"""
    pass


class AppListingResponse(AppListingBase):
    """Used when reading a record from DB — includes rating distributions"""
    id: int
    scraped_at: datetime
    rating_distributions: list[RatingDistributionResponse] = []

    model_config = ConfigDict(from_attributes=True)