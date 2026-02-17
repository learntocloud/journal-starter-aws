from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import logging
import json
import os

from api.repositories.postgres_repository import PostgresDB
from api.models.analysis_response import AnalysisResponse

logger = logging.getLogger("journal")

async def analyze_journal_entry(self, entry_id: str) -> AnalysisResponse | None:
        """Analyzes a journal entry using OpenAI's API."""
        logger.info("Analyzing entry %s", entry_id)
        
        # Fetch the entry
        entry = await self.get_entry(entry_id)
        if not entry:
            logger.warning("Entry %s not found. Analysis aborted.", entry_id)
            return None
        
        # Combine the three fields into one string for LLM analysis
        entry_text = f"Work: {entry['work']}\n\nStruggle: {entry['struggle']}\n\nIntention: {entry['intention']}"
        logger.debug("Combined entry text: %s", entry_text)
        
        openai_client = AsyncOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=os.getenv("AZURE_OPENAI_BASE_URL")
        )

        system_message = (
            "You are an experienced learning coach analyzing student learning journals. "
            "Analyze this journal entry and provide a response following this JSON format: "
            '{"sentiment": "positive" | "negative" | "neutral", '
            '"summary": "2 sentence summary", '
            '"topics": ["topic1", "topic2"], '
            '"struggle_detected": "true" | "false"} '
            "Rules: Ensure the summary captures key learnings and/or challenges. "
            "Limit topics to 1-3 key topics. Be objective. "
            "Do not make assumptions beyond what is written."
        )

        user_message = f"Journal Entry:\n{entry_text}"

        response = await openai_client.chat.completions.create(
            model="gpt4omini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "AnalysisResponse",
                    "schema": AnalysisResponse.model_json_schema(),
                    "strict": True
                }
            },
            max_tokens=1000,
            temperature=0.7,
        )

        # Extract the response content and parse it as AnalysisResponse
        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from LLM")
            raise ValueError("LLM returned empty response")
        
        analysis_json = json.loads(content)
        analysis_result = AnalysisResponse(**analysis_json)
        logger.debug("Parsed analysis result: %s", analysis_result)

        return analysis_result
