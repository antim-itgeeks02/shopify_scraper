from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from app.core.database import Base


class AppListing(Base):
    __tablename__ = "app_listings"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # App details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    developer: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="upsell")

    # Ratings & downloads
    rating: Mapped[float | None] = mapped_column(nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    no_of_downloads: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # URLs
    app_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    rating_distributions = relationship(
    "RatingDistribution",
    back_populates="app",
    cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AppListing name={self.name!r} rating={self.rating}>"