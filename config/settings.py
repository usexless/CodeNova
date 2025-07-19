import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from typing import Dict, Any

# Lade Umgebungsvariablen aus .env, falls vorhanden
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

BASE_DIR = Path(__file__).parent.parent
PROJECTS_DIR = BASE_DIR / "projects"
MEMORY_DIR = BASE_DIR / "memory"

# --- Konfigurations-Management ---
def is_configured() -> bool:
    """Überprüft, ob die Ersteinrichtung abgeschlossen ist."""
    return os.getenv("SETUP_COMPLETED") == "true"

def save_configuration(provider: str, api_key: str, model: str):
    """Speichert die Konfiguration in der .env-Datei."""
    # Speichere die neuen Werte
    set_key(dotenv_path, "LLM_PROVIDER", provider)
    
    if provider == "openai":
        set_key(dotenv_path, "OPENAI_API_KEY", api_key)
        set_key(dotenv_path, "OPENAI_MODEL", model)
    elif provider == "openrouter":
        set_key(dotenv_path, "OPENROUTER_API_KEY", api_key)
        set_key(dotenv_path, "OPENROUTER_MODEL", model)
    elif provider == "moonshot":
        set_key(dotenv_path, "MOONSHOT_API_KEY", api_key)
        set_key(dotenv_path, "MOONSHOT_MODEL", model)
        
    set_key(dotenv_path, "SETUP_COMPLETED", "true")

    # Lade die Umgebungsvariablen neu, um die Änderungen sofort zu übernehmen
    load_dotenv(dotenv_path=dotenv_path, override=True)

# --- LLM Provider Konfiguration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI Konfiguration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

# OpenRouter Konfiguration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku")

# Moonshot (Kimi) Konfiguration
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")

# Allgemeine LLM-Einstellungen
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))

# System-Einstellungen
AGENT_TIMEOUT = 300
MAX_RETRIES = 3
DEBUG_MODE = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

# Verfügbare LLM-Provider (alle OpenAI-kompatibel)
AVAILABLE_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
        "api_key_env": "OPENAI_API_KEY",
        "api_base_url": "https://api.openai.com/v1"
    },
    "openrouter": {
        "name": "OpenRouter",
        "models": ["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku", "google/gemini-pro-1.5", "mistralai/mistral-large"],
        "api_key_env": "OPENROUTER_API_KEY",
        "api_base_url": "https://openrouter.ai/api/v1"
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "api_key_env": "MOONSHOT_API_KEY",
        "api_base_url": "https://api.moonshot.ai/v1"
    }
}

def get_current_provider_config() -> Dict[str, Any]:
    """Hole die aktuelle Provider-Konfiguration."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider not in AVAILABLE_PROVIDERS:
        print(f"⚠️  Warnung: Unbekannter Provider '{provider}'. Verwende OpenAI als Fallback.")
        return AVAILABLE_PROVIDERS["openai"]
    
    return AVAILABLE_PROVIDERS[provider]

def get_current_model() -> str:
    """Hole das aktuell konfigurierte Modell."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    elif provider == "openrouter":
        return os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku")
    elif provider == "moonshot":
        return os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
    else:
        return os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

def validate_configuration() -> bool:
    """Validiere die aktuelle Konfiguration."""
    if not is_configured():
        return False
        
    provider_config = get_current_provider_config()
    
    api_key_env = provider_config.get("api_key_env")
    if api_key_env:
        api_key = os.getenv(api_key_env)
        if not api_key:
            print(f"❌ Fehler: Umgebungsvariable '{api_key_env}' ist nicht gesetzt!")
            return False
    
    return True

# Initialisiere Verzeichnisse, falls sie nicht existieren
if not PROJECTS_DIR.exists():
    PROJECTS_DIR.mkdir()

if not MEMORY_DIR.exists():
    MEMORY_DIR.mkdir()