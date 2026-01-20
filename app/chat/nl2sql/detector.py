import json
import logging
import re
from typing import Tuple

from app.chat.llm.client import llm_client
from app.chat.nl2sql.prompts import DETECTION_PROMPT
from app.chat.nl2sql.exceptions import QueryDetectionError

logger = logging.getLogger(__name__)

class QueryDetector:
    """Detects if a user message required a data query.
    """

    DATA_KEYWORDS = [
        "cuanto", "cuantos", "cuánto", "cuántos",
        "total", "suma", "promedio", "average",
        "gasto", "costo", "ingreso", "venta",
        "comparar", "comparación", "vs", "versus",
        "mayor", "menor", "máximo", "mínimo",
        "top", "ranking", "ordenar", "ordenados",
        "categoría", "servicio", "producto", "equipo",
        "mes", "año", "trimestre", "período", "fecha",
        "tendencia", "evolución", "histórico",
        "muestra", "mostrar", "dame", "lista", "listar",
        "ticket", "falla", "mantenimiento", "evento",
        "abierto", "cerrado", "pendiente", "resuelto",
        "cliente", "usuario", "técnico",
    ]

    CHAT_KEYWORDS = [
        "hola", "gracias", "adiós", "chao",
        "ayuda", "help", "qué puedes", "que puedes",
        "cómo funciona", "como funciona",
        "explicar", "explica", "qué es", "que es",
        "por qué", "por que", "quién", "quien",
    ]

    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold

    async def is_data_query(
        self,
        message: str,
        use_llm: bool = True,
    ) -> Tuple[bool, float, str]:
        """
        Determine if message requires a database query.
        Returns: (is_data_query, confidence, reasoning)
        """
        heuristic_result = self._heuristic_check(message)

        if heuristic_result[1] > 0.85:
            logger.info(f"Heuristic detection: {heuristic_result}")
            return heuristic_result

        if use_llm:
            try:
                llm_result = await self._llm_detection(message)
                logger.info(f"LLM detection: {llm_result}")
                return llm_result
            except Exception as e:
                logger.warning(f"LLM detection failed, using heuristic: {e}")
                return heuristic_result

        return heuristic_result



    def _heuristic_check(self, message: str) -> Tuple[bool, float, str]:
        """Fast heuristic cherk based on keywords
        """
        message_lower = message.lower()

        data_score = sum(1 for kw in self.DATA_KEYWORDS if kw in message_lower)
        chat_score = sum(1 for kw in self.CHAT_KEYWORDS if kw in message_lower)

        if data_score == 0 and chat_score == 0:
            return (False, 0.3, "No se encontraron palabras clave relevantes.")
        
        total = data_score + chat_score
        data_ratio = data_score / total if total > 0 else 0

        is_data = data_ratio > 0.5
        confidence = min(0.5 + (data_ratio * 0.4), 0.85)

        reasoning = f"Heuristic: {data_score} data keywords vs { chat_score} chat keywords."
        return (is_data, confidence, reasoning)
    
    async def _llm_detection(self, message: str) -> Tuple[bool, float, str]:
        """Use Gemini LLM for more accurate dectection."""
        prompt = DETECTION_PROMPT.format(user_message=message)

        try:
            response = await gemini_client.generate_response(
                user_message=prompt,
                conversation_history=[],
                context_data={},
            )

            result = self._parse_json_response(response)

            return (
                result.get("requires_data", False),
                result.get("confidence", 0.5),
                result.get("reasoning", "LLM detection")
            )

        except json.JSONDecodeError as e:
            raise QueryDetectionError(f"Invalid LLM response format: {e}")
        
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON response from Gemini"""
        cleaned = response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            start = 1 if lines[0].startswith("```") else 0
            end = -1 if lines[-1] == "```" else len(lines)
            cleaned = "\n".join(lines[start:end])

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise

