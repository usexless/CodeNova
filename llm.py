import os
from typing import List, Dict, Any, Optional, TypedDict
from openai import OpenAI, types
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from pydantic import SecretStr

from config.settings import (
    LLM_PROVIDER, TEMPERATURE, MAX_TOKENS, 
    get_current_provider_config, get_current_model, validate_configuration
)

class ChatMessage(TypedDict):
    role: str
    content: str

class LLMManager:
    def __init__(self):
        self.reload_config()
    
    def reload_config(self):
        """Lädt die Konfiguration neu und initialisiert die Clients."""
        if not validate_configuration():
            # Wenn nicht konfiguriert, warte, bis die Einrichtung abgeschlossen ist
            return

        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = get_current_model()
        self.provider_config = get_current_provider_config()
        
        # Initialisiere Client
        self.client = self._initialize_client()
        self.langchain_llm = self._initialize_langchain_llm()
    
    def _get_client_args(self) -> Dict[str, Any]:
        """Erstellt die Argumente für den OpenAI-Client."""
        api_key = os.getenv(self.provider_config["api_key_env"], "")
        base_url = self.provider_config["api_base_url"]
        return {"api_key": api_key, "base_url": base_url}

    def _initialize_client(self) -> OpenAI:
        """Initialisiere den OpenAI-kompatiblen Client."""
        return OpenAI(**self._get_client_args())
    
    def _initialize_langchain_llm(self) -> ChatOpenAI:
        """Initialisiere LangChain LLM für den aktuellen Provider."""
        client_args = self._get_client_args()
        return ChatOpenAI(
            model=self.model,
            temperature=TEMPERATURE,
            api_key=SecretStr(client_args["api_key"]),
            base_url=client_args["base_url"]
        )
    
    def _print_configuration(self):
        """Zeige aktuelle LLM-Konfiguration"""
        provider_name = self.provider_config["name"]
        print(f"🤖 AI Programmer gestartet mit:")
        print(f"   Provider: {provider_name}")
        print(f"   Modell: {self.model}")
        print(f"   Temperatur: {TEMPERATURE}")
        print(f"   Max Tokens: {MAX_TOKENS}")
        print()
    
    def generate_response(self, system_prompt: str, user_prompt: str, context: Optional[List[ChatMessage]] = None) -> str:
        """Generiere Antwort mit Kontext"""
        messages: List[ChatMessage] = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.extend(context[-10:])  # Letzte 10 Nachrichten
        
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            error_msg = f"Fehler bei API-Aufruf ({self.provider_config['name']}): {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def generate_structured_response(self, system_prompt: str, user_prompt: str, response_format: Dict[str, Any]) -> Any:
        """Generiere strukturierte Antwort (JSON)"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.langchain_llm.invoke(messages)
            return response.content
        except Exception as e:
            error_msg = f"Fehler bei strukturiertem API-Aufruf ({self.provider_config['name']}): {str(e)}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Hole Informationen über den aktuellen Provider"""
        return {
            "provider": self.provider,
            "provider_name": self.provider_config["name"],
            "model": self.model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS
        }
    
    def test_connection(self) -> bool:
        """Teste die Verbindung zum LLM-Provider"""
        try:
            test_response = self.generate_response(
                "Du bist ein hilfreicher Assistent.",
                "Antworte nur mit 'OK'."
            )
            return "OK" in test_response or "ok" in test_response
        except Exception as e:
            print(f"❌ Verbindungstest fehlgeschlagen: {str(e)}")
            return False

# Global instance
llm_manager = LLMManager()