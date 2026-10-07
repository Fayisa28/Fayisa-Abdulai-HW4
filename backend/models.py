"""Typed response shapes shared by the Campus Customs agent and API."""

from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    image_url: str


class ProductCard(BaseModel):
    """The safe product facts the agent may place beside a chat reply."""
    product_id: str
    name: str
    category: str
    price: float
    colors: list[str] = Field(default_factory=list)
    in_stock_sizes: list[str] = Field(default_factory=list)
    low_stock_sizes: list[str] = Field(default_factory=list)


class SizeStock(BaseModel):
    size: str
    quantity: int = Field(ge=0)
    available: bool
    status: str


class ProductInfo(BaseModel):
    found: bool
    product_id: str
    name: str | None = None
    description: str | None = None
    price: float | None = None
    colors: list[str] = Field(default_factory=list)
    image_url: str | None = None
    sizes: list[SizeStock] = Field(default_factory=list)


class StockStatus(BaseModel):
    found: bool
    product_id: str
    size: str
    quantity: int | None = Field(default=None, ge=0)
    available: bool = False
    message: str


class AgentReply(BaseModel):
    reply: str
    product_ids: list[str] = Field(default_factory=list)
