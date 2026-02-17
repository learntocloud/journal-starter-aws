from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class AnalysisResponse(BaseModel):
    """Data model for journal entry LLM analysis response."""
    
    model_config = ConfigDict(json_schema_extra={"additionalProperties": False})
    
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Sentiment analysis result of the journal entry.",
    )
    
    summary: str = Field(
        min_length=1,
        max_length=256,
        description="2 sentence summary of journal entry, detailing key learnings and/or challenges faced.",
    )

    topics: list[str] = Field(
        min_length=1,
        max_length=3,
        description="List of key topics discussed in the journal entry (1-3 topics).",
    )

    struggle_detected: bool = Field(
        description="Indicates whether a learning struggle was detected in the journal entry.",
    )