"""LLM client for chat and analysis using GLM-4.6 via Z.AI OpenAI-compatible API."""
import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class LLMClient:
    """Client for interacting with GLM-4.6 via Z.AI OpenAI-compatible API."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_model

    async def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        context_data: dict | None = None,
    ) -> str:
        """Generate a response to a user message."""
        system_prompt = self._build_system_prompt(context_data)

        # Build messages for OpenAI format
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = msg["role"] if msg["role"] in ("user", "assistant") else "user"
                messages.append({"role": role, "content": msg["content"]})

        # Add current message
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

    async def generate_analysis(
        self,
        analysis_type: str,
        data: dict,
    ) -> dict:
        """Generate analysis and recommendations from data."""
        prompt = self._build_analysis_prompt(analysis_type, data)

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=4096,
            )

            text = response.choices[0].message.content

            return {
                "analysis": text,
                "recommendations": self._extract_recommendations(text),
            }
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            raise

    async def stream_response(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        context_data: dict | None = None,
    ) -> AsyncIterator[str]:
        """Stream a response chunk by chunk."""
        system_prompt = self._build_system_prompt(context_data)

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            for msg in conversation_history:
                role = msg["role"] if msg["role"] in ("user", "assistant") else "user"
                messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise

    def _build_system_prompt(self, context_data: dict | None = None) -> str:
        """Build the system prompt with optional context."""
        base_prompt = """Eres un asistente de análisis de datos empresarial especializado en NL2SQL.

Tu función es ayudar a los usuarios a:
1. Hacer consultas en lenguaje natural sobre sus datos
2. Interpretar resultados de consultas SQL
3. Generar insights y recomendaciones

Responde siempre en español de forma clara y profesional.

Cuando analices datos, proporciona:
1. Un resumen ejecutivo
2. Análisis detallado
3. Conclusiones clave
4. Recomendaciones accionables"""

        if context_data:
            context_str = f"\n\nDatos de contexto disponibles:\n{context_data}"
            return base_prompt + context_str

        return base_prompt

    def _build_analysis_prompt(self, analysis_type: str, data: dict) -> str:
        """Build a specific analysis prompt."""
        prompts = {
            "data_summary": f"""Analiza los siguientes datos:

{data}

Proporciona:
1. **Resumen Ejecutivo**: Breve descripción del análisis
2. **Análisis Detallado**: Interpretación de los datos
3. **Tendencias**: Patrones identificados
4. **Conclusiones**: Hallazgos principales
5. **Recomendaciones**: Acciones específicas a tomar

Formato: Usa Markdown para estructurar la respuesta.""",

            "trend_analysis": f"""Genera un análisis de tendencias con los siguientes datos:

{data}

Incluye métricas clave, comparaciones y proyecciones.""",
        }

        return prompts.get(analysis_type, f"Analiza los siguientes datos:\n{data}")

    def _extract_recommendations(self, text: str) -> list[str]:
        """Extract recommendations from analysis text."""
        recommendations = []
        lines = text.split("\n")

        in_recommendations = False
        for line in lines:
            if "recomendacion" in line.lower() or "recommendation" in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.strip().startswith(("-", "•", "*", "1", "2", "3")):
                recommendations.append(line.strip().lstrip("-•* 0123456789."))

        return recommendations[:5]  # Return top 5 recommendations


# Singleton instance
llm_client = LLMClient()
