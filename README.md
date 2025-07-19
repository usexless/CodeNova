# AI Programmer - Autonome KI-Programmierumgebung

Eine leistungsstarke KI-gesteuerte Entwicklungsumgebung, die automatisch Software-Projekte aus natürlichen Sprachanforderungen erstellt und dabei eine Auswahl an führenden, OpenAI-kompatiblen Large Language Models nutzt.

## ✨ Features

- **Multi-Provider-Unterstützung**: Nahtlose Integration mit OpenAI, OpenRouter (für Anthropic, Google etc.) und Moonshot (Kimi).
- **Interaktive Modi**: Chat- und Auto-Modus zum Planen und Erstellen von Projekten.
- **Interaktiver Chat**: Ein intelligenter Assistent für Code-Diskussionen und schnelle Prototypen.
- **Automatisierte Projekt-Workflows**: Von der Planung über die Codegenerierung bis hin zu Tests und Dokumentation.
- **Konfigurierbar und Erweiterbar**: Einfache Anpassung über `.env`-Dateien und eine modulare Agenten-Architektur.

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.8 oder höher
- Ein API-Schlüssel für einen der unterstützten Provider (OpenAI, OpenRouter, Moonshot).

### Installation

1.  **Repository klonen:**
    ```bash
    git clone https://github.com/dein-repo/ai-programmer.git
    cd ai-programmer
    ```

2.  **Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Umgebung konfigurieren:**
    - Kopiere die Vorlage: `cp .env.example .env`
    - Bearbeite die `.env`-Datei und trage deinen API-Schlüssel ein.

## 🔧 LLM-Konfiguration

Wähle deinen Provider und das gewünschte Modell in der `.env`-Datei aus.

```dotenv
# Wähle einen Provider: openai, openrouter, moonshot
LLM_PROVIDER=openai

# --- OpenAI ---
OPENAI_API_KEY="sk-dein_openai_schlüssel"
OPENAI_MODEL="gpt-4-turbo"

# --- OpenRouter (für Anthropic, Google etc.) ---
OPENROUTER_API_KEY="sk-or-dein_openrouter_schlüssel"
OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"

# --- Moonshot (Kimi) ---
MOONSHOT_API_KEY="dein_moonshot_schlüssel"
MOONSHOT_MODEL="moonshot-v1-128k"
```

### Anwendung starten

Starte CodeNova mit:

```bash
python main.py
```

Beim ersten Start führt dich ein Setup-Wizard durch die Konfiguration.

## 🤖 Anwendungsmodi

Nach dem Start arbeitest du in einer interaktiven Shell. Mit der **Tab**-Taste wechselst du zwischen Chat- und Auto-Modus:

- **Chat-Modus**: Stelle Fragen oder verwende Befehle wie `/plan`.
- **Auto-Modus**: Die KI erkennt eigenständig Projektanforderungen und startet den Build-Prozess.

### Beispiel: Ein Projekt bauen

Starte die Anwendung und gib deine Anforderung im Auto-Modus ein:

```
python main.py
```

Nach dem Start kannst du zum Auto-Modus wechseln und beispielsweise schreiben:

```
Erstelle eine einfache API mit FastAPI, die auf /ping mit {"response": "pong"} antwortet.
```

Die KI erkennt die Projektanforderung und baut das Projekt automatisch.

### Beispiel: Chat-Modus verwenden

Im Chat-Modus stellst du Fragen oder gibst Befehle wie `/plan` ein:

```
> /plan my-cli-tool "Ein Python-CLI-Tool, das mit 'click' das Wetter für eine Stadt anzeigt."
```

## ⚙️ Architektur

Das System basiert auf einer modularen Agenten-Architektur:

-   **`ProjectManager`**: Plant das Projekt und definiert die Aufgaben.
-   **`CodeGenerator`**: Schreibt den Code basierend auf den Spezifikationen.
-   **`TestRunner`**: Erstellt und führt Tests aus.
-   **`Debugger`**: Versucht, fehlerhaften Code zu korrigieren.
-   **`LLMManager`**: Verwaltet die Kommunikation mit den Sprachmodellen.

Alle Interaktionen und generierten Dateien werden im `projects/` Verzeichnis gespeichert.

## 📞 Support

Bei Problemen:
1.  Überprüfe die Fehlermeldungen in der Konsole.
2.  Starte `python main.py` erneut und prüfe die Setup-Einstellungen.
3.  Stelle sicher, dass deine Umgebungsvariablen in der `.env`-Datei korrekt sind.

---

## Lizenz

Dieses Projekt ist unter der [CC BY-NC 4.0 Lizenz](https://creativecommons.org/licenses/by-nc/4.0/deed.de) veröffentlicht.  
Keine kommerzielle Nutzung erlaubt. Namensnennung erforderlich.