from pydantic import BaseModel, Field
from typing import List, Optional

class NewsArticle(BaseModel):
    title: str
    url: str
    image_url: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    published_date: Optional[str] = None
    relevance_score: float = Field(..., description="How 'hot' or relevant this is to tech news (0-1)")

class NewsReport(BaseModel):
    articles: List[NewsArticle]
    trending_topics: List[str]

class CriticFeedback(BaseModel):
    approved: bool
    feedback: str
    improved_title: Optional[str] = None
    improved_summary: Optional[str] = None
