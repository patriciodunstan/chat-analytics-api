"""Gemini LLM client for chat and analysis."""
from typing import AsyncIterator

import google.generativeai as genai

from app.config import get_settings


settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class GeminiClient:
    """Client for interacting with Google Gemini."""

    def __init__(self):
        self.model = genai.GenerativeModel(settings.gemini_model)

    async def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict] = None,
        context_data: dict = None,
    ) -> str:
        """Generate a response to a user message."""
        # Build the prompt
        system_prompt = self._build_system_prompt(context_data)

        # Prepare chat history
        chat_history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

        # Create chat session
        chat = self.model.start_chat(history=chat_history)

        # Generate response
        full_prompt = f"{system_prompt}\n\nUsuario: {user_message}"
        response = chat.send_message(full_prompt)

        return response.text

    async def generate_analysis(
        self,
        analysis_type: str,
        data: dict,
    ) -> dict:
        """Generate analysis and recommendations from data."""
        prompt = self._build_analysis_prompt(analysis_type, data)

        response = self.model.generate_content(prompt)

        return {
            "analysis": response.text,
            "recommendations": self._extract_recommendations(response.text),
        }

    async def stream_response(
        self,
        user_message: str,
        conversation_history: list[dict] = None,
        context_data: dict = None,
    ) -> AsyncIterator[str]:
        """Stream a response chunk by chunk."""
        system_prompt = self._build_system_prompt(context_data)

        chat_history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

        chat = self.model.start_chat(history=chat_history)
        full_prompt = f"{system_prompt}\n\nUsuario: {user_message}"

        response = chat.send_message(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _build_system_prompt(self, context_data: dict = None) -> str:
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
        lines = text.split('\n')

        in_recommendations = False
        for line in lines:
            if 'recomendacion' in line.lower() or 'recommendation' in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.strip().startswith(('-', '•', '*', '1', '2', '3')):
                recommendations.append(line.strip().lstrip('-•* 0123456789.'))

        return recommendations[:5]  # Return top 5 recommendations


# Singleton instance
gemini_client = GeminiClient()