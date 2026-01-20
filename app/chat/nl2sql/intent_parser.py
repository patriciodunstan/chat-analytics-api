
import json
import logging
import re
from datetime import datetime


from app.chat.llm.client import llm_client
from app.chat.nl2sql.schemas import ParsedIntent, DateRange, DatabaseSchema
from app.chat.nl2sql.prompts import INTENT_PARSING_PROMPT
from app.chat.nl2sql.exceptions import IntentParsingError

logger = logging.getLogger(__name__)

class IntentParser:
    """Parses user intent from natural lenguage using database schema
    """

    async def parse(
            self,
            message: str,
            schema: DatabaseSchema,
            schema_prompt: str
    ) -> ParsedIntent:
        """Parse user message to extract query intent."""
        prompt = INTENT_PARSING_PROMPT.format(
            schema_description=schema_prompt,
            current_date=datetime.utcnow().strftime("%Y-%m-%d"),
            user_message=message
        )
        try:
            response = await llm_client.generate_response(
                user_message=prompt,
                conversation_history=[],
                context_data={},
            )

            parsed = self._parse_json_response(response)
            intent = self._build_intent(parsed, message)
            self._validate_intent(intent, schema)

            return intent
        
        except json.JSONDecodeError as e:
            raise IntentParsingError(f"Invalid LLM response format: {e}")
        except Exception as e:
            raise IntentParsingError(f"Error parsing intent: {e}")
        
    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON object from LLM response."""
        cleaned = response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            start = 1 if lines[0].startswith("```") else 0
            end = -1 if lines[-1] == "```" else len(lines)
            cleaned = "\n".join(lines[start:end])

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise
    
    def _build_intent(
            self, parsed: dict, original_message: str
    ) -> ParsedIntent:
        """
        Build ParsedIntent from parsed JSON
        """

        date_range = None
        if dr := parsed.get("date_range"):
            if dr.get("start_date") or dr.get("end_date"):
                date_range = DateRange(
                    start_date=dr.get("start_date"),
                    end_date=dr.get("end_date"),
                    period_description=dr.get("period_description", "")
                )
        return ParsedIntent(
            tables=parsed.get("tables", []),
            select_columns=parsed.get("select_columns", []),
            aggregations=parsed.get("aggregations", []),
            filters=parsed.get("filters", []),
            group_by=parsed.get("group_by", []),
            order_by=parsed.get("order_by", []),
            limit=parsed.get("limit"),
            date_range=date_range,
            confidence=parsed.get("confidence", 0.5),
            reasoning=parsed.get("reasoning", ""),
            original_message=original_message
        )
    
    def _validate_intent(self, intent: ParsedIntent, schema: DatabaseSchema):
        """Validate intent against schema."""
        valid_tables = [t.lower() for t in schema.get_table_names()]

        for table in intent.tables[:]:
            if table.lower() not in valid_tables:
                logger.warning(f"Table '{table}' not found in schema, removing")
                intent.tables.remove(table)

        if not intent.tables:
            raise IntentParsingError(
                f"No valid tables found. Available: {', '.join(schema.get_table_names())}"
            )