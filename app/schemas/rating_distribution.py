from pydantic import BaseModel, ConfigDict


class RatingDistributionBase(BaseModel):
    star: int
    count: int
    percentage: float | None = None


class RatingDistributionCreate(RatingDistributionBase):
    """Used when inserting a new rating distribution record"""
    app_id: int


class RatingDistributionResponse(RatingDistributionBase):
    """Used when reading a record from DB"""
    id: int
    app_id: int

    model_config = ConfigDict(from_attributes=True)