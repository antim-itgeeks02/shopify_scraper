from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RatingDistribution(Base):
    __tablename__ = "rating_distributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to app_listings
    app_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("app_listings.id", ondelete="CASCADE"), nullable=False
    )

    # Star level: 1, 2, 3, 4, or 5
    star: Mapped[int] = mapped_column(Integer, nullable=False)

    # Number of reviews for this star level
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Percentage of total reviews
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationship back to AppListing
    app = relationship("AppListing", back_populates="rating_distributions")

    def __repr__(self) -> str:
        return f"<RatingDistribution app_id={self.app_id} star={self.star} count={self.count}>"