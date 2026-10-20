import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Manages LLM communication via OpenRouter with timeouts and strict system constraints.
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_CHAT_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        """
        Sends the prompt messages to the configured OpenRouter model.
        """
        if not self.is_configured():
            logger.info("OpenRouter API key is not set. Generating contextual fallback response.")
            return ""

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=45.0,
                max_retries=2
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers={
                    "HTTP-Referer": "https://intelligent-rag-chatbot.local",
                    "X-Title": "Intelligent RAG Chatbot"
                }
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            logger.error("LLM generation error: %s", e)
            raise RuntimeError(f"LLM API request failed: {str(e)}")


llm_service = LLMService()
