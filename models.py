from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductOffer:
    title: str
    price: float
    price_formatted: str
    store: str
    link: str
    source: str
    image_url: Optional[str] = None
    rating: Optional[str] = None
    original_price: Optional[float] = None
    discount_pct: Optional[int] = None

