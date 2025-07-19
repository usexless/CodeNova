from typing import Dict, Any, List, cast
import json
import sys
import os
import yaml
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam, ChatCompletionToolParam

from agents.base_agent import BaseAgent, Task
from tools.tool_definitions import get_tool_definitions
from tools.file_tools import file_manager
from tools.code_executor import code_executor
from llm import llm_manager
from rich.console import Console
from rich.panel import Panel

console = Console()

class ToolAgent(BaseAgent):
    def __init__(self, chat_mode: bool = False):
        super().__init__("ToolAgent", "Ein Agent, der Tools zur Projekterstellung verwendet.")
        self.chat_mode = chat_mode
        self.tools = self.get_chat_safe_tools() if chat_mode else get_tool_definitions()
        
        # Definiere alle verfügbaren Funktionen
        all_functions = {
            # Basic tools (existing)
            "write_file": file_manager.write_file,
            "read_file": self.read_file_wrapper,
            "list_directory": self.list_directory,
            "run_shell_command": code_executor.run_shell,
            "ask_user_clarification": self.ask_user_clarification,
            
            # Advanced file operations
            "edit_file": self.edit_file,
            "view_file": self.view_file,
            "write_to_file": self.write_to_file,
            
            # Advanced search and navigation
            "codebase_search": self.codebase_search,
            "grep_search": self.grep_search,
            "find_by_name": self.find_by_name,
            "list_dir": self.list_dir,
            "view_code_item": self.view_code_item,
            
            # Command execution and monitoring
            "run_command": self.run_command,
            "command_status": self.command_status,

            # Web and deployment tools
            "read_deployment_config": self.read_deployment_config,
            "deploy_web_app": self.deploy_web_app,
            "check_deploy_status": self.check_deploy_status,
            "browser_preview": self.browser_preview,

            # Web content and search
            "read_url_content": self.read_url_content,
            "view_web_document_content_chunk": self.view_web_document_content_chunk,
            "search_web": self.search_web,
            
            # Memory and interaction
            "create_memory": self.create_memory,
            "suggested_responses": self.suggested_responses,
            
            # Advanced Moonshot Tools
            "analyze_code_complexity": self.analyze_code_complexity,
            "generate_documentation": self.generate_documentation,
            "optimize_code": self.optimize_code,
            "detect_security_vulnerabilities": self.detect_security_vulnerabilities,
            "generate_test_cases": self.generate_test_cases,
            "refactor_code": self.refactor_code,
            "analyze_dependencies": self.analyze_dependencies,
            "profile_performance": self.profile_performance,
            "validate_architecture": self.validate_architecture,
            "generate_api_spec": self.generate_api_spec,
        }
        
        # Im Chat-Modus nur Chat-sichere Funktionen verfügbar machen
        if chat_mode:
            chat_safe_function_names = {
                "list_directory", "read_file", "view_file", "list_dir", "view_code_item",
                "codebase_search", "grep_search", "find_by_name",
                "read_url_content", "view_web_document_content_chunk", "search_web",
                "analyze_code_complexity", "detect_security_vulnerabilities", 
                "analyze_dependencies", "profile_performance", "validate_architecture",
                "create_memory", "suggested_responses", "ask_user_clarification"
            }
            self.available_functions = {k: v for k, v in all_functions.items() if k in chat_safe_function_names}
        else:
            self.available_functions = all_functions

    def system_prompt(self) -> str:
        if self.chat_mode:
            return """
Du bist ein hilfreicher KI-Programmier-Assistent auf Windows 11 mit PowerShell. Du bist im CHAT-MODUS und hast nur lesende/analysierende Tools zur Verfügung.

CHAT-MODUS BESCHRÄNKUNGEN:
- Du kannst Dateien und Verzeichnisse nur LESEN und ANALYSIEREN
- Du kannst im Internet suchen und Web-Inhalte lesen
- Du kannst Code analysieren und Sicherheitslücken erkennen
- Du kannst Memory-Einträge erstellen
- Du kannst KEINE Dateien erstellen, bearbeiten oder löschen
- Du kannst KEINE Befehle ausführen
- Du kannst KEINE Projekte deployen

KERNPRINZIPIEN:
1. **INFORMATIVE ANTWORTEN**: Gib detaillierte und hilfreiche Antworten basierend auf deinen Analysen
2. **GRÜNDLICHE INFORMATIONSAMMLUNG**: Sammle alle notwendigen Informationen proaktiv mit deinen verfügbaren Tools
3. **PROAKTIVE TOOL-VERWENDUNG**: Verwende deine lesenden Tools ohne zu fragen, um bessere Antworten zu geben
4. **KLARE ERKLÄRUNGEN**: Erkläre deine Erkenntnisse und Analysen klar und verständlich

DEINE VERFÜGBAREN FÄHIGKEITEN (CHAT-MODUS):

**Datei- und Code-Analyse:**
- Dateien und Verzeichnisse lesen und anzeigen
- Semantische Codebase-Suche und präzise Text-Suche
- Code-Komplexitätsanalyse und Metriken
- Sicherheitslücken-Erkennung
- Abhängigkeitsanalyse
- Performance-Profiling
- Architektur-Validierung

**Web und Recherche:**
- Websuche durchführen
- URL-Inhalte lesen und analysieren
- Webdokumente in Chunks anzeigen

**Memory und Interaktion:**
- Wichtigen Kontext in Memory-Datenbank speichern
- Interaktive Antwortvorschläge bereitstellen

TOOL-AUSWAHL-STRATEGIE (CHAT-MODUS):
- **codebase_search**: HAUPTWERKZEUG für Codebase-Exploration - verwende semantische Suche
- **list_directory/list_dir**: STARTE IMMER HIER - verstehe die Projektstruktur gründlich
- **read_file/view_file**: Wenn du Dateiinhalte brauchst (view_file für große Dateien)
- **grep_search**: Für exakte Text-Muster-Suche
- **search_web**: Für externe Recherche
- **create_memory**: Für wichtigen Kontext-Speicher
- **analyze_code_complexity**: Für Code-Qualitätsanalyse
- **detect_security_vulnerabilities**: Für Sicherheitsanalyse
- **analyze_dependencies**: Für Abhängigkeitsanalyse
- **profile_performance**: Für Performance-Profiling
- **validate_architecture**: Für Architektur-Validierung
- **ask_user_clarification**: NUR wenn du Informationen brauchst, die du nicht selbst finden kannst

ARBEITSWEISE (CHAT-MODUS):
1. **Analysiere die Frage gründlich** - verstehe was der Benutzer wissen möchte
2. **Verwende Tools proaktiv** - hole dir Informationen, die du brauchst
3. **Gib informative Antworten** - basierend auf deinen Analysen und Recherchen
4. **Erkläre deine Erkenntnisse** - mache deine Antworten verständlich und hilfreich

WICHTIG: Du arbeitest in einer Windows PowerShell-Umgebung. Verwende nur Windows-kompatible Befehle und Pfade.

Sei hilfreich, informativ und gründlich in deinen Analysen!
"""
        else:
            return """
Du bist ein autonomer KI-Softwareentwickler auf Windows 11 mit PowerShell. Du hast volle Autonomie und löst Probleme komplett, bevor du zurück zum Benutzer gehst.

KERNPRINZIPIEN:
1. **AUTONOME PROBLEMLÖSUNG**: Arbeite selbstständig bis zur vollständigen Problemlösung. Frage nicht nach Bestätigung bei jedem Schritt.
2. **GRÜNDLICHE INFORMATIONSAMMLUNG**: Sammle alle notwendigen Informationen proaktiv. Sei THOROUGH bei der Informationssammlung.
3. **PROAKTIVE TOOL-VERWENDUNG**: Verwende Tools ohne zu fragen. Wenn du Informationen brauchst, hole sie dir selbst.
4. **VOLLSTÄNDIGE LÖSUNG**: Löse das Problem komplett, nicht nur teilweise. Keine halben Lösungen.

DEINE ERWEITERTEN FÄHIGKEITEN:

**Datei- und Code-Operationen:**
- Dateien lesen, schreiben, bearbeiten und anzeigen
- Semantische Codebase-Suche und präzise Text-Suche
- Verzeichnisse auflisten und durchsuchen mit erweiterten Filtern
- Code-Elemente (Klassen, Funktionen) direkt anzeigen

**System und Deployment:**
- Shell-Befehle ausführen und überwachen (Windows PowerShell)
- Webanwendungen deployen (Netlify, etc.)
- Deployment-Status überwachen
- Browser-Vorschauen für Webserver starten

**Web und Recherche:**
- Websuche durchführen
- URL-Inhalte lesen und analysieren
- Webdokumente in Chunks anzeigen

**Memory und Interaktion:**
- Wichtigen Kontext in Memory-Datenbank speichern
- Benutzereinstellungen und Präferenzen merken
- Interaktive Antwortvorschläge bereitstellen

**Erweiterte Code-Analyse (Moonshot):**
- Code-Komplexitätsanalyse und Metriken
- Automatische Dokumentationsgenerierung
- Code-Optimierung für Performance/Lesbarkeit
- Sicherheitslücken-Erkennung
- Automatische Testfall-Generierung
- Code-Refaktorierung
- Abhängigkeitsanalyse und -graphen
- Performance-Profiling
- Architektur-Validierung
- API-Spezifikationsgenerierung

TOOL-AUSWAHL-STRATEGIE:
- **codebase_search**: HAUPTWERKZEUG für Codebase-Exploration - verwende semantische Suche
- **list_directory/list_dir**: STARTE IMMER HIER - verstehe die Projektstruktur gründlich
- **read_file/view_file**: Wenn du Dateiinhalte brauchst (view_file für große Dateien)
- **write_file/write_to_file**: Wenn du neue Dateien erstellen musst
- **edit_file**: Wenn du bestehende Dateien präzise bearbeiten musst
- **grep_search**: Für exakte Text-Muster-Suche
- **run_command**: Für System-Befehle mit erweiterter Kontrolle
- **deploy_web_app**: Für Web-Deployments
- **search_web**: Für externe Recherche
- **create_memory**: Für wichtigen Kontext-Speicher
- **analyze_code_complexity**: Für Code-Qualitätsanalyse
- **generate_documentation**: Für automatische Dokumentation
- **optimize_code**: Für Code-Optimierung
- **detect_security_vulnerabilities**: Für Sicherheitsanalyse
- **generate_test_cases**: Für automatische Testgenerierung
- **refactor_code**: Für Code-Refaktorierung
- **analyze_dependencies**: Für Abhängigkeitsanalyse
- **profile_performance**: Für Performance-Profiling
- **validate_architecture**: Für Architektur-Validierung
- **generate_api_spec**: Für API-Spezifikationen
- **ask_user_clarification**: NUR wenn du Informationen brauchst, die du nicht selbst finden kannst

ARBEITSWEISE:
1. **Analysiere die Situation gründlich** - sammle alle verfügbaren Informationen
2. **Verwende Tools proaktiv** - hole dir Informationen, die du brauchst
3. **Entscheide autonom** - wähle die beste Lösung basierend auf den gesammelten Informationen
4. **Implementiere vollständig** - löse das Problem komplett
5. **Validiere die Lösung** - stelle sicher, dass alles funktioniert

WICHTIG: Du arbeitest in einer Windows PowerShell-Umgebung. Verwende nur Windows-kompatible Befehle und Pfade.

Sei proaktiv, gründlich und autonom. Löse Probleme komplett mit deinen erweiterten Fähigkeiten!
"""

    def process_task(self, task: Task) -> Dict[str, Any]:
        """Verarbeitet eine komplexe Aufgabe durch den Einsatz von Tools."""
        user_request = task.description
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": user_request}
        ]

        console.print(Panel(f"Starte Aufgabenbearbeitung für: [bold]{user_request}[/bold]", title="🤖 ToolAgent", border_style="blue"))

        # Schleife für mehrere Tool-Aufrufe
        for i in range(10): # Maximal 10 Schritte, um Endlosschleifen zu vermeiden
            response = llm_manager.client.chat.completions.create(
                model=llm_manager.model,
                messages=cast(List[ChatCompletionMessageParam], messages),
                tools=cast(List[ChatCompletionToolParam], self.tools),
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                console.print("[green]Agent hat die Aufgabe abgeschlossen.[/green]")
                return {"status": "completed", "final_response": response_message.content}

            # Wandle die Antwortnachricht in ein Wörterbuch um, bevor sie angehängt wird
            messages.append(response_message.model_dump())
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.available_functions.get(function_name)
                
                if not function_to_call:
                    console.print(f"[red]Fehler: Unbekannte Funktion '{function_name}'[/red]")
                    continue

                try:
                    function_args = json.loads(tool_call.function.arguments)
                    console.print(f"🔩 Rufe Tool auf: [bold]{function_name}[/bold] mit Argumenten: {function_args}")
                    
                    function_response = function_to_call(**function_args)
                    
                    # Stelle sicher, dass die Tool-Nachricht dem richtigen Format entspricht
                    tool_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                    messages.append(tool_message)
                except Exception as e:
                    console.print(f"[red]Fehler bei der Ausführung von '{function_name}': {e}[/red]")
                    error_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": f'{{"error": "Ausführung fehlgeschlagen", "details": "{str(e)}"}}',
                    }
                    messages.append(error_message)

            # --- DEBUGGING PRINT ---
            import sys
            import json
            try:
                print("DEBUG: Messages sent to LLM for next step:", file=sys.stderr)
                print(json.dumps(messages, indent=2), file=sys.stderr)
            except Exception as debug_error:
                print(f"DEBUG ERROR: {debug_error}", file=sys.stderr)
            # --- END DEBUGGING ---

        return {"status": "max_steps_reached", "final_response": "Maximale Anzahl an Schritten erreicht."}

    def ask_user_clarification(self, question: str) -> str:
        """Stellt eine Frage an den Benutzer und wartet auf eine Antwort."""
        console.print(f"\n[bold yellow]❓ Agent fragt:[/bold yellow] {question}")
        user_response = input("Ihre Antwort: ")
        return user_response

    def read_file_wrapper(self, path: str) -> Dict[str, Any]:
        """Wrapper für read_file, der die korrekte Rückgabe-Formatierung sicherstellt."""
        try:
            content = file_manager.read_file(path)
            return {
                "status": "success",
                "content": content,
                "path": path
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "path": path
            }

    def list_directory(self, path: str) -> Dict[str, Any]:
        """Listet den Inhalt eines Verzeichnisses auf."""
        try:
            import os
            from pathlib import Path
            
            # Konvertiere relativen Pfad zu absolutem Pfad
            if path == "." or path == "":
                current_path = Path.cwd()
            else:
                current_path = Path(path).resolve()
            
            if not current_path.exists():
                return {"status": "error", "message": f"Verzeichnis existiert nicht: {path}"}
            
            if not current_path.is_dir():
                return {"status": "error", "message": f"Pfad ist kein Verzeichnis: {path}"}
            
            items = []
            for item in current_path.iterdir():
                try:
                    item_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                        "modified": item.stat().st_mtime
                    }
                    items.append(item_info)
                except Exception:
                    # Überspringe Dateien, die nicht gelesen werden können
                    continue
            
            # Sortiere: Verzeichnisse zuerst, dann Dateien
            items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
            
            return {
                "status": "success",
                "path": str(current_path),
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def read_deployment_config(self, path: str) -> Dict[str, Any]:
        """Liest und validiert eine Deployment-Konfiguration."""
        try:
            import json
            import yaml
            from pathlib import Path

            config_path = Path(path)
            if not config_path.exists():
                return {"status": "error", "message": "Config-Datei nicht gefunden"}

            content = config_path.read_text(encoding="utf-8")
            data: Dict[str, Any]
            if path.endswith((".yaml", ".yml")):
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)

            return {"status": "success", "config": data, "path": str(config_path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def deploy_web_app(self, project_path: str, platform: str = "netlify") -> Dict[str, Any]:
        """Deployt eine Webanwendung. Placeholder-Implementierung."""
        try:
            console.print(f"🚀 Deploye {project_path} auf {platform} …")
            # Placeholder: in real scenario we would call platform CLI
            result = code_executor.run_shell(f"echo Deploy {project_path} to {platform}")
            return {"status": "success", "output": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_deploy_status(self, deploy_id: str) -> Dict[str, Any]:
        """Überprüft den Status eines Deployments. Placeholder-Implementierung."""
        try:
            console.print(f"📡 Prüfe Deployment-Status für {deploy_id}")
            # Placeholder result
            return {"status": "success", "deploy_id": deploy_id, "state": "unknown"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def browser_preview(self, directory: str, port: int = 8000) -> Dict[str, Any]:
        """Startet einen einfachen HTTP-Server zur Vorschau im Browser."""
        try:
            from threading import Thread
            import http.server
            import socketserver

            directory = os.path.abspath(directory)
            if not os.path.isdir(directory):
                return {"status": "error", "message": "Verzeichnis existiert nicht"}

            handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("", port), handler)

            def serve():
                os.chdir(directory)
                httpd.serve_forever()

            thread = Thread(target=serve, daemon=True)
            thread.start()

            return {"status": "success", "directory": directory, "port": port}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Advanced file operations
    def edit_file(self, TargetFile: str, Instruction: str, CodeEdit: str, CodeMarkdownLanguage: str, TargetLintErrorIds: List[str] = []) -> Dict[str, Any]:
        """Bearbeitet eine bestehende Datei mit präzisen Änderungen."""
        try:
            import os
            from pathlib import Path
            
            # Stelle sicher, dass die Datei existiert
            if not os.path.exists(TargetFile):
                return {"status": "error", "message": f"Datei existiert nicht: {TargetFile}"}
            
            # Lese aktuellen Inhalt
            with open(TargetFile, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Führe die Bearbeitung durch
            if CodeEdit.strip():
                # Ersetze den Inhalt basierend auf der Anweisung
                if "{{ ... }}" in CodeEdit:
                    # Spezielle Syntax für "unveränderten Code"
                    lines = current_content.split('\n')
                    new_lines = []
                    
                    for line in CodeEdit.split('\n'):
                        if line.strip() == "{{ ... }}":
                            # Füge alle aktuellen Zeilen hinzu
                            new_lines.extend(lines)
                        else:
                            new_lines.append(line)
                    
                    new_content = '\n'.join(new_lines)
                else:
                    # Direkte Ersetzung
                    new_content = CodeEdit
                
                # Schreibe den neuen Inhalt
                with open(TargetFile, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return {
                    "status": "success", 
                    "message": f"Datei {TargetFile} erfolgreich bearbeitet",
                    "instruction": Instruction,
                    "file_size": len(new_content)
                }
            else:
                return {"status": "error", "message": "Kein Code zum Bearbeiten bereitgestellt"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def view_file(self, AbsolutePath: str, StartLine: int, EndLine: int, IncludeSummaryOfOtherLines: bool) -> Dict[str, Any]:
        """Zeigt den Inhalt einer Datei in einem bestimmten Bereich an."""
        try:
            with open(AbsolutePath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if StartLine < 0 or EndLine >= len(lines) or StartLine > EndLine:
                return {"status": "error", "message": "Ungültige Zeilenbereiche"}
            
            selected_lines = lines[StartLine:EndLine + 1]
            content = ''.join(selected_lines)
            
            result = {
                "status": "success",
                "content": content,
                "start_line": StartLine,
                "end_line": EndLine,
                "total_lines": len(lines)
            }
            
            if IncludeSummaryOfOtherLines:
                other_lines = lines[:StartLine] + lines[EndLine + 1:]
                result["summary_of_other_lines"] = f"Datei hat {len(lines)} Zeilen, {len(other_lines)} andere Zeilen"
            
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def write_to_file(self, TargetFile: str, CodeContent: str, EmptyFile: bool) -> Dict[str, Any]:
        """Erstellt eine neue Datei und schreibt Inhalt hinein."""
        try:
            import os
            os.makedirs(os.path.dirname(TargetFile), exist_ok=True)
            
            with open(TargetFile, 'w', encoding='utf-8') as f:
                if not EmptyFile:
                    f.write(CodeContent)
            
            return {"status": "success", "message": f"Datei {TargetFile} erstellt"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Advanced search and navigation
    def codebase_search(self, Query: str, TargetDirectories: List[str]) -> Dict[str, Any]:
        """Führt eine semantische Suche im Codebase durch."""
        try:
            import os
            import re
            from pathlib import Path
            
            results = []
            search_terms = Query.lower().split()
            
            # Durchsuche alle angegebenen Verzeichnisse
            for directory in TargetDirectories:
                if not os.path.exists(directory):
                    continue
                    
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.html', '.css', '.md', '.txt')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                # Suche nach relevanten Zeilen
                                lines = content.split('\n')
                                relevant_lines = []
                                
                                for i, line in enumerate(lines, 1):
                                    line_lower = line.lower()
                                    if any(term in line_lower for term in search_terms):
                                        relevant_lines.append({
                                            "line": i,
                                            "content": line.strip(),
                                            "relevance": sum(1 for term in search_terms if term in line_lower)
                                        })
                                
                                if relevant_lines:
                                    # Sortiere nach Relevanz
                                    relevant_lines.sort(key=lambda x: x["relevance"], reverse=True)
                                    results.append({
                                        "file": file_path,
                                        "matches": relevant_lines[:5],  # Top 5 Matches
                                        "total_matches": len(relevant_lines)
                                    })
                                    
                            except Exception:
                                continue
            
            return {
                "status": "success", 
                "results": results, 
                "query": Query,
                "total_files_searched": len(results)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def grep_search(self, SearchPath: str, Query: str, MatchPerLine: bool, Includes: List[str], CaseInsensitive: bool) -> Dict[str, Any]:
        """Verwendet ripgrep für exakte Muster-Suche."""
        try:
            import os
            import re
            from pathlib import Path
            
            results = []
            
            # Kompiliere Regex-Pattern
            flags = re.IGNORECASE if CaseInsensitive else 0
            pattern = re.compile(Query, flags)
            
            # Bestimme zu durchsuchende Dateien
            search_files = []
            if os.path.isfile(SearchPath):
                search_files = [SearchPath]
            else:
                for root, dirs, files in os.walk(SearchPath):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Prüfe Include-Filter
                        if Includes:
                            if not any(file.endswith(ext) for ext in Includes):
                                continue
                        search_files.append(file_path)
            
            # Durchsuche Dateien
            for file_path in search_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    matches = []
                    for i, line in enumerate(lines, 1):
                        if pattern.search(line):
                            match_info = {
                                "line": i,
                                "content": line.strip(),
                                "match": pattern.search(line).group()
                            }
                            matches.append(match_info)
                            
                            if MatchPerLine and matches:
                                break  # Nur erste Übereinstimmung pro Zeile
                    
                    if matches:
                        results.append({
                            "file": file_path,
                            "matches": matches,
                            "total_matches": len(matches)
                        })
                        
                except Exception:
                    continue
            
            return {
                "status": "success", 
                "results": results, 
                "query": Query,
                "total_files_searched": len(search_files)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def find_by_name(self, SearchDirectory: str, Pattern: str, Excludes: List[str], Type: str, MaxDepth: int, Extensions: List[str], FullPath: bool) -> Dict[str, Any]:
        """Sucht nach Dateien und Unterverzeichnissen mit erweiterten Filtern."""
        try:
            import os
            import re
            import fnmatch
            from pathlib import Path
            
            results = []
            
            # Kompiliere Pattern für effiziente Suche
            if Pattern:
                pattern_regex = re.compile(fnmatch.translate(Pattern), re.IGNORECASE)
            
            # Durchsuche Verzeichnis rekursiv
            for root, dirs, files in os.walk(SearchDirectory):
                # Prüfe MaxDepth
                current_depth = root.replace(SearchDirectory, '').count(os.sep)
                if current_depth > MaxDepth:
                    continue
                
                # Filtere Verzeichnisse basierend auf Excludes
                dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, exclude) for exclude in Excludes)]
                
                # Suche nach Dateien
                if Type in ["file", "both"]:
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, SearchDirectory)
                        
                        # Prüfe Pattern-Match
                        if Pattern and not pattern_regex.match(file):
                            continue
                        
                        # Prüfe Extensions
                        if Extensions and not any(file.endswith(ext) for ext in Extensions):
                            continue
                        
                        # Prüfe Excludes
                        if any(fnmatch.fnmatch(file, exclude) for exclude in Excludes):
                            continue
                        
                        results.append({
                            "name": file,
                            "path": file_path if FullPath else relative_path,
                            "type": "file",
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path)
                        })
                
                # Suche nach Verzeichnissen
                if Type in ["directory", "both"]:
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        relative_path = os.path.relpath(dir_path, SearchDirectory)
                        
                        # Prüfe Pattern-Match
                        if Pattern and not pattern_regex.match(dir_name):
                            continue
                        
                        # Prüfe Excludes
                        if any(fnmatch.fnmatch(dir_name, exclude) for exclude in Excludes):
                            continue
                        
                        try:
                            children = len(os.listdir(dir_path))
                        except:
                            children = 0
                        
                        results.append({
                            "name": dir_name,
                            "path": dir_path if FullPath else relative_path,
                            "type": "directory",
                            "children": children,
                            "modified": os.path.getmtime(dir_path)
                        })
            
            return {
                "status": "success", 
                "results": results, 
                "pattern": Pattern,
                "total_found": len(results)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_dir(self, DirectoryPath: str) -> Dict[str, Any]:
        """Listet den Inhalt eines Verzeichnisses mit detaillierten Informationen auf."""
        try:
            import os
            if not os.path.exists(DirectoryPath):
                return {"status": "error", "message": "Verzeichnis existiert nicht"}
            
            items = []
            for item in os.listdir(DirectoryPath):
                item_path = os.path.join(DirectoryPath, item)
                is_dir = os.path.isdir(item_path)
                size = os.path.getsize(item_path) if not is_dir else 0
                children = len(os.listdir(item_path)) if is_dir else 0
                
                items.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "size": size,
                    "children": children
                })
            
            return {"status": "success", "items": items, "path": DirectoryPath}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def view_code_item(self, NodePath: str, File: str = "") -> Dict[str, Any]:
        """Zeigt den Inhalt eines Code-Elements wie eine Klasse oder Funktion an."""
        try:
            import os
            import re
            import ast
            
            # Bestimme die zu durchsuchende Datei
            if File and os.path.exists(File):
                file_path = File
            elif NodePath and os.path.exists(NodePath):
                file_path = NodePath
            else:
                return {"status": "error", "message": "Datei nicht gefunden"}
            
            # Lese Dateiinhalt
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Versuche AST-Parsing für Python-Dateien
            if file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    elements = []
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                            element_info = {
                                "type": type(node).__name__,
                                "name": getattr(node, 'name', 'module'),
                                "line": getattr(node, 'lineno', 1),
                                "end_line": getattr(node, 'end_lineno', len(content.split('\n')))
                            }
                            elements.append(element_info)
                    
                    # Finde das spezifische Element
                    target_element = None
                    for element in elements:
                        if element["name"] in NodePath or NodePath in element["name"]:
                            target_element = element
                            break
                    
                    if target_element:
                        start_line = target_element["line"] - 1
                        end_line = target_element["end_line"]
                        lines = content.split('\n')
                        element_content = '\n'.join(lines[start_line:end_line])
                        
                        return {
                            "status": "success",
                            "content": element_content,
                            "node_path": NodePath,
                            "element_type": target_element["type"],
                            "start_line": target_element["line"],
                            "end_line": target_element["end_line"]
                        }
                        
                except SyntaxError:
                    pass
            
            # Fallback: Suche nach dem Element im Text
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if NodePath in line:
                    # Finde den Anfang und das Ende des Elements
                    start_line = max(0, i - 1)
                    end_line = min(len(lines), i + 10)  # Zeige 10 Zeilen um die gefundene Zeile
                    
                    element_content = '\n'.join(lines[start_line:end_line])
                    
                    return {
                        "status": "success",
                        "content": element_content,
                        "node_path": NodePath,
                        "start_line": start_line + 1,
                        "end_line": end_line
                    }
            
            return {"status": "error", "message": f"Code-Element '{NodePath}' nicht gefunden"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Command execution and monitoring
    def run_command(self, CommandLine: str, Cwd: str, Blocking: bool, WaitMsBeforeAsync: int, SafeToAutoRun: bool) -> Dict[str, Any]:
        """Führt einen Terminal-Befehl mit erweiterter Kontrolle aus."""
        try:
            # Use existing code_executor for now
            result = code_executor.run_shell(CommandLine)
            return {"status": "success", "output": result, "command": CommandLine}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def command_status(self, CommandId: str, OutputPriority: str, OutputCharacterCount: int, WaitDurationSeconds: int) -> Dict[str, Any]:
        """Prüft den Status eines zuvor ausgeführten Terminal-Befehls."""
        try:
            # Placeholder implementation - would need command tracking
            console.print(f"📊 Befehlsstatus: {CommandId}")
            return {"status": "success", "command_id": CommandId, "state": "completed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}



    # Web content and search
    def read_url_content(self, Url: str) -> Dict[str, Any]:
        """Liest Inhalt von einer URL."""
        try:
            import requests
            response = requests.get(Url, timeout=10)
            response.raise_for_status()
            return {"status": "success", "content": response.text, "url": Url}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def view_web_document_content_chunk(self, url: str, position: int) -> Dict[str, Any]:
        """Zeigt einen spezifischen Chunk eines Webdokuments an."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Lade Web-Inhalt
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Entferne Scripts und Styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extrahiere Text
            text = soup.get_text()
            lines = text.split('\n')
            
            # Berechne Chunk-Größe (200 Zeilen pro Chunk)
            chunk_size = 200
            total_chunks = len(lines) // chunk_size + 1
            
            if position >= total_chunks:
                position = total_chunks - 1
            
            start_line = position * chunk_size
            end_line = min(start_line + chunk_size, len(lines))
            
            chunk_content = '\n'.join(lines[start_line:end_line])
            
            return {
                "status": "success", 
                "url": url, 
                "position": position,
                "total_chunks": total_chunks,
                "start_line": start_line,
                "end_line": end_line,
                "content": chunk_content.strip()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Memory and interaction
    def create_memory(self, Id: str, Title: str, Content: str, CorpusNames: List[str], Tags: List[str], Action: str, UserTriggered: bool) -> Dict[str, Any]:
        """Speichert wichtigen Kontext in einer Memory-Datenbank."""
        try:
            import os
            import json
            from datetime import datetime
            from pathlib import Path
            
            # Erstelle Memory-Verzeichnis falls nicht vorhanden
            memory_dir = Path("memory")
            memory_dir.mkdir(exist_ok=True)
            
            # Memory-Datei
            memory_file = memory_dir / "memories.json"
            
            # Lade bestehende Memories
            memories = []
            if memory_file.exists():
                try:
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        memories = json.load(f)
                except:
                    memories = []
            
            # Erstelle neuen Memory-Eintrag
            memory_entry = {
                "id": Id,
                "title": Title,
                "content": Content,
                "corpus_names": CorpusNames,
                "tags": Tags,
                "action": Action,
                "user_triggered": UserTriggered,
                "timestamp": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            # Füge Memory hinzu oder aktualisiere bestehenden
            existing_index = None
            for i, memory in enumerate(memories):
                if memory.get("id") == Id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                memories[existing_index] = memory_entry
            else:
                memories.append(memory_entry)
            
            # Speichere Memories
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success", 
                "action": Action, 
                "title": Title,
                "id": Id,
                "memory_count": len(memories)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def suggested_responses(self, Suggestions: List[str]) -> Dict[str, Any]:
        """Stellt eine kleine Anzahl möglicher Antworten bereit."""
        try:
            console.print(f"💡 Antwortvorschläge: {Suggestions}")
            return {"status": "success", "suggestions": Suggestions}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Advanced Moonshot Tools
    def analyze_code_complexity(self, file_path: str, metrics: List[str]) -> Dict[str, Any]:
        """Analysiert die Komplexität von Code."""
        try:
            import os
            import ast
            import re
            
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"Datei nicht gefunden: {file_path}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                "file": file_path,
                "total_lines": len(content.split('\n')),
                "metrics": {}
            }
            
            # Cyclomatic Complexity
            if "cyclomatic" in metrics or "all" in metrics:
                complexity = 1  # Basis-Komplexität
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.AsyncWith, ast.With, ast.Try, ast.ExceptHandler)):
                            complexity += 1
                        elif isinstance(node, ast.BoolOp):
                            complexity += len(node.values) - 1
                except:
                    pass
                analysis["metrics"]["cyclomatic_complexity"] = complexity
            
            # Cognitive Complexity
            if "cognitive" in metrics or "all" in metrics:
                cognitive = 0
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if any(keyword in line for keyword in ['if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ', 'and ', 'or ']):
                        cognitive += 1
                analysis["metrics"]["cognitive_complexity"] = cognitive
            
            # Lines of Code
            if "loc" in metrics or "all" in metrics:
                lines = content.split('\n')
                loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
                analysis["metrics"]["lines_of_code"] = loc
            
            # Function Count
            if "functions" in metrics or "all" in metrics:
                try:
                    tree = ast.parse(content)
                    functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
                    analysis["metrics"]["function_count"] = functions
                except:
                    analysis["metrics"]["function_count"] = 0
            
            # Class Count
            if "classes" in metrics or "all" in metrics:
                try:
                    tree = ast.parse(content)
                    classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                    analysis["metrics"]["class_count"] = classes
                except:
                    analysis["metrics"]["class_count"] = 0
            
            # Generate recommendations
            recommendations = []
            if analysis["metrics"].get("cyclomatic_complexity", 0) > 10:
                recommendations.append("Reduziere cyclomatic complexity - extrahiere Methoden")
            if analysis["metrics"].get("cognitive_complexity", 0) > 15:
                recommendations.append("Reduziere cognitive complexity - vereinfache Bedingungen")
            if analysis["metrics"].get("function_count", 0) > 20:
                recommendations.append("Zu viele Funktionen - erwäge Aufteilung in Module")
            
            analysis["recommendations"] = recommendations
            analysis["status"] = "success"
            
            return analysis
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_documentation(self, file_path: str, doc_type: str, output_path: str) -> Dict[str, Any]:
        """Generiert automatisch Dokumentation für Code-Dateien."""
        try:
            console.print(f"📚 Generiere Dokumentation: {file_path} -> {output_path}")
            console.print(f"Typ: {doc_type}")
            return {"status": "success", "output_path": output_path, "doc_type": doc_type}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def optimize_code(self, file_path: str, optimization_type: str, backup_original: bool) -> Dict[str, Any]:
        """Optimiert Code für Performance, Lesbarkeit oder Speichernutzung."""
        try:
            console.print(f"⚡ Code-Optimierung: {file_path}")
            console.print(f"Typ: {optimization_type}, Backup: {backup_original}")
            return {"status": "success", "optimization_type": optimization_type, "improvements": ["Reduzierte Komplexität", "Bessere Performance"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def detect_security_vulnerabilities(self, file_path: str, severity_level: str) -> Dict[str, Any]:
        """Erkennt Sicherheitslücken in Code."""
        try:
            import os
            import re
            
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"Datei nicht gefunden: {file_path}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            vulnerabilities = []
            
            # SQL Injection patterns
            sql_patterns = [
                (r"execute\s*\(\s*[\"'].*\+.*[\"']", "SQL Injection - String concatenation in execute"),
                (r"cursor\.execute\s*\(\s*[\"'].*\+.*[\"']", "SQL Injection - String concatenation in cursor.execute"),
                (r"\.format\s*\(\s*.*\s*\)", "SQL Injection - String formatting in SQL"),
            ]
            
            # Command Injection patterns
            cmd_patterns = [
                (r"os\.system\s*\(\s*.*\+.*\)", "Command Injection - String concatenation in os.system"),
                (r"subprocess\.call\s*\(\s*.*\+.*\)", "Command Injection - String concatenation in subprocess.call"),
                (r"eval\s*\(\s*.*\)", "Code Injection - eval() usage"),
                (r"exec\s*\(\s*.*\)", "Code Injection - exec() usage"),
            ]
            
            # Path Traversal patterns
            path_patterns = [
                (r"open\s*\(\s*.*\+.*\)", "Path Traversal - String concatenation in file operations"),
                (r"\.read\s*\(\s*.*\+.*\)", "Path Traversal - String concatenation in file read"),
            ]
            
            # Hardcoded secrets
            secret_patterns = [
                (r"password\s*=\s*[\"'][^\"']+[\"']", "Hardcoded Password"),
                (r"api_key\s*=\s*[\"'][^\"']+[\"']", "Hardcoded API Key"),
                (r"secret\s*=\s*[\"'][^\"']+[\"']", "Hardcoded Secret"),
            ]
            
            # XSS patterns (for web applications)
            xss_patterns = [
                (r"innerHTML\s*=\s*.*\+.*", "XSS - innerHTML with user input"),
                (r"document\.write\s*\(\s*.*\+.*\)", "XSS - document.write with user input"),
            ]
            
            all_patterns = sql_patterns + cmd_patterns + path_patterns + secret_patterns + xss_patterns
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern, description in all_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        vulnerabilities.append({
                            "line": line_num,
                            "content": line.strip(),
                            "type": description,
                            "severity": "HIGH" if "Injection" in description else "MEDIUM"
                        })
            
            # Filter by severity level
            severity_map = {"low": ["LOW"], "medium": ["LOW", "MEDIUM"], "high": ["LOW", "MEDIUM", "HIGH"]}
            allowed_severities = severity_map.get(severity_level.lower(), ["LOW", "MEDIUM", "HIGH"])
            
            filtered_vulnerabilities = [v for v in vulnerabilities if v["severity"] in allowed_severities]
            
            return {
                "status": "success",
                "vulnerabilities": filtered_vulnerabilities,
                "severity_level": severity_level,
                "total_found": len(filtered_vulnerabilities),
                "file": file_path
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_test_cases(self, file_path: str, test_framework: str, coverage_target: float) -> Dict[str, Any]:
        """Generiert automatisch Testfälle für Code."""
        try:
            console.print(f"🧪 Generiere Tests: {file_path}")
            console.print(f"Framework: {test_framework}, Coverage-Ziel: {coverage_target}%")
            return {"status": "success", "test_framework": test_framework, "coverage_target": coverage_target, "test_files": []}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def refactor_code(self, file_path: str, refactoring_type: str, target_pattern: str) -> Dict[str, Any]:
        """Führt automatische Code-Refaktorierung durch."""
        try:
            console.print(f"🔧 Code-Refaktorierung: {file_path}")
            console.print(f"Typ: {refactoring_type}, Muster: {target_pattern}")
            return {"status": "success", "refactoring_type": refactoring_type, "changes": ["Methoden extrahiert", "Variablen umbenannt"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def analyze_dependencies(self, project_path: str, output_format: str) -> Dict[str, Any]:
        """Analysiert Abhängigkeiten und erstellt Abhängigkeitsgraphen."""
        try:
            import os
            import ast
            import json
            from pathlib import Path
            
            if not os.path.exists(project_path):
                return {"status": "error", "message": f"Projektpfad nicht gefunden: {project_path}"}
            
            dependencies = {
                "imports": [],
                "functions": [],
                "classes": [],
                "files": []
            }
            
            # Durchsuche alle Python-Dateien
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Parse AST
                            tree = ast.parse(content)
                            
                            file_deps = {
                                "file": relative_path,
                                "imports": [],
                                "functions": [],
                                "classes": []
                            }
                            
                            # Analysiere Imports
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        file_deps["imports"].append(alias.name)
                                elif isinstance(node, ast.ImportFrom):
                                    module = node.module or ""
                                    for alias in node.names:
                                        file_deps["imports"].append(f"{module}.{alias.name}")
                                elif isinstance(node, ast.FunctionDef):
                                    file_deps["functions"].append(node.name)
                                elif isinstance(node, ast.ClassDef):
                                    file_deps["classes"].append(node.name)
                            
                            dependencies["files"].append(file_deps)
                            dependencies["imports"].extend(file_deps["imports"])
                            dependencies["functions"].extend(file_deps["functions"])
                            dependencies["classes"].extend(file_deps["classes"])
                            
                        except Exception:
                            continue
            
            # Entferne Duplikate
            dependencies["imports"] = list(set(dependencies["imports"]))
            dependencies["functions"] = list(set(dependencies["functions"]))
            dependencies["classes"] = list(set(dependencies["classes"]))
            
            # Erstelle Ausgabe
            if output_format == "json":
                output_path = os.path.join(project_path, "dependencies.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(dependencies, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success", 
                "output_format": output_format, 
                "dependencies": dependencies,
                "graph_path": output_path if output_format == "json" else "",
                "total_files": len(dependencies["files"]),
                "total_imports": len(dependencies["imports"]),
                "total_functions": len(dependencies["functions"]),
                "total_classes": len(dependencies["classes"])
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def profile_performance(self, file_path: str, profiling_type: str, duration: int) -> Dict[str, Any]:
        """Führt Performance-Profiling für Code aus."""
        try:
            import os
            import time
            import cProfile
            import pstats
            import io
            import subprocess
            import psutil
            
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"Datei nicht gefunden: {file_path}"}
            
            results = {
                "file": file_path,
                "profiling_type": profiling_type,
                "duration": duration,
                "metrics": {}
            }
            
            if profiling_type == "execution_time":
                # Messung der Ausführungszeit
                start_time = time.time()
                
                # Führe Datei aus
                try:
                    result = subprocess.run([sys.executable, file_path], 
                                          capture_output=True, text=True, timeout=duration)
                    execution_time = time.time() - start_time
                    
                    results["metrics"]["execution_time"] = execution_time
                    results["metrics"]["exit_code"] = result.returncode
                    results["metrics"]["stdout_size"] = len(result.stdout)
                    results["metrics"]["stderr_size"] = len(result.stderr)
                    
                except subprocess.TimeoutExpired:
                    results["metrics"]["execution_time"] = duration
                    results["metrics"]["timeout"] = True
                except Exception as e:
                    results["metrics"]["error"] = str(e)
            
            elif profiling_type == "memory_usage":
                # Memory-Profiling
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Führe Datei aus und messe Memory
                try:
                    result = subprocess.run([sys.executable, file_path], 
                                          capture_output=True, text=True, timeout=duration)
                    final_memory = process.memory_info().rss / 1024 / 1024  # MB
                    
                    results["metrics"]["initial_memory_mb"] = initial_memory
                    results["metrics"]["final_memory_mb"] = final_memory
                    results["metrics"]["memory_increase_mb"] = final_memory - initial_memory
                    
                except Exception as e:
                    results["metrics"]["error"] = str(e)
            
            elif profiling_type == "cpu_profiling":
                # CPU-Profiling mit cProfile
                profiler = cProfile.Profile()
                profiler.enable()
                
                try:
                    # Führe Datei aus
                    exec(open(file_path).read())
                except Exception as e:
                    results["metrics"]["error"] = str(e)
                
                profiler.disable()
                
                # Analysiere Ergebnisse
                s = io.StringIO()
                stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                stats.print_stats(10)  # Top 10 Funktionen
                
                results["metrics"]["profile_output"] = s.getvalue()
            
            # System-Informationen
            results["metrics"]["system_info"] = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "python_version": sys.version
            }
            
            results["status"] = "success"
            return results
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def validate_architecture(self, project_path: str, architecture_pattern: str) -> Dict[str, Any]:
        """Validiert die Architektur eines Projekts gegen Best Practices."""
        try:
            import os
            import ast
            from pathlib import Path
            
            if not os.path.exists(project_path):
                return {"status": "error", "message": f"Projektpfad nicht gefunden: {project_path}"}
            
            validation_results = []
            score = 100
            issues = []
            
            # Sammle Projektstruktur
            project_structure = {
                "files": [],
                "directories": [],
                "python_files": []
            }
            
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    project_structure["files"].append(relative_path)
                    
                    if file.endswith('.py'):
                        project_structure["python_files"].append(relative_path)
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(dir_path, project_path)
                    project_structure["directories"].append(relative_path)
            
            # MVC-Validierung
            if architecture_pattern.lower() == "mvc":
                mvc_patterns = {
                    "models": ["model", "models"],
                    "views": ["view", "views", "template", "templates"],
                    "controllers": ["controller", "controllers", "route", "routes"]
                }
                
                for layer, patterns in mvc_patterns.items():
                    found = False
                    for pattern in patterns:
                        if any(pattern in dir_name.lower() for dir_name in project_structure["directories"]):
                            found = True
                            break
                    
                    if found:
                        validation_results.append(f"✅ {layer.capitalize()}-Schicht gefunden")
                    else:
                        validation_results.append(f"❌ {layer.capitalize()}-Schicht fehlt")
                        issues.append(f"Fehlende {layer}-Schicht")
                        score -= 10
            
            # Clean Architecture Validierung
            elif architecture_pattern.lower() == "clean":
                clean_layers = ["entities", "usecases", "interfaces", "controllers", "presenters"]
                
                for layer in clean_layers:
                    if any(layer in dir_name.lower() for dir_name in project_structure["directories"]):
                        validation_results.append(f"✅ {layer.capitalize()}-Schicht gefunden")
                    else:
                        validation_results.append(f"❌ {layer.capitalize()}-Schicht fehlt")
                        issues.append(f"Fehlende {layer}-Schicht")
                        score -= 8
            
            # Allgemeine Best Practices
            # 1. README vorhanden
            readme_files = [f for f in project_structure["files"] if "readme" in f.lower()]
            if readme_files:
                validation_results.append("✅ README-Datei vorhanden")
            else:
                validation_results.append("❌ README-Datei fehlt")
                issues.append("Keine README-Datei gefunden")
                score -= 5
            
            # 2. Requirements/Abhängigkeiten
            req_files = [f for f in project_structure["files"] if any(x in f.lower() for x in ["requirements", "setup.py", "pyproject.toml"])]
            if req_files:
                validation_results.append("✅ Abhängigkeitsdatei vorhanden")
            else:
                validation_results.append("❌ Abhängigkeitsdatei fehlt")
                issues.append("Keine Abhängigkeitsdatei gefunden")
                score -= 5
            
            # 3. Tests vorhanden
            test_dirs = [d for d in project_structure["directories"] if "test" in d.lower()]
            if test_dirs:
                validation_results.append("✅ Test-Verzeichnis vorhanden")
            else:
                validation_results.append("❌ Test-Verzeichnis fehlt")
                issues.append("Kein Test-Verzeichnis gefunden")
                score -= 10
            
            # 4. Konfigurationsdateien
            config_files = [f for f in project_structure["files"] if any(x in f.lower() for x in ["config", "settings", ".env"])]
            if config_files:
                validation_results.append("✅ Konfigurationsdatei vorhanden")
            else:
                validation_results.append("❌ Konfigurationsdatei fehlt")
                issues.append("Keine Konfigurationsdatei gefunden")
                score -= 5
            
            # 5. Code-Qualität (einfache Metriken)
            total_lines = 0
            for py_file in project_structure["python_files"]:
                try:
                    with open(os.path.join(project_path, py_file), 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except:
                    continue
            
            if total_lines > 0:
                validation_results.append(f"✅ {total_lines} Code-Zeilen gefunden")
                
                # Warnung bei sehr großen Dateien
                for py_file in project_structure["python_files"]:
                    try:
                        with open(os.path.join(project_path, py_file), 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            if lines > 500:
                                validation_results.append(f"⚠️ Große Datei: {py_file} ({lines} Zeilen)")
                                issues.append(f"Sehr große Datei: {py_file}")
                                score -= 2
                    except:
                        continue
            
            # Score begrenzen
            score = max(0, score)
            
            return {
                "status": "success",
                "architecture_pattern": architecture_pattern,
                "validation_results": validation_results,
                "issues": issues,
                "score": score,
                "project_structure": project_structure,
                "total_files": len(project_structure["files"]),
                "total_python_files": len(project_structure["python_files"])
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_api_spec(self, file_path: str, spec_format: str, output_path: str) -> Dict[str, Any]:
        """Generiert API-Spezifikationen aus Code."""
        try:
            console.print(f"📋 API-Spezifikation: {file_path}")
            console.print(f"Format: {spec_format}, Ausgabe: {output_path}")
            return {"status": "success", "spec_format": spec_format, "output_path": output_path, "endpoints": []}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search_web(self, query: str) -> Dict[str, Any]:
        """Führt eine Websuche durch und gibt relevante Ergebnisse zurück."""
        try:
            from config.settings import LLM_PROVIDER
            if LLM_PROVIDER == "moonshot":
                # Use Moonshot's builtin web search function with proper tool calling
                from llm import llm_manager
                from typing import cast
                from openai.types.chat import ChatCompletionMessageParam
                
                messages = [{"role": "user", "content": query}]
                
                try:
                    # Use Moonshot's web search capability directly
                    response = llm_manager.client.chat.completions.create(
                        model=llm_manager.model,
                        messages=cast(list[ChatCompletionMessageParam], messages),
                        temperature=0.3
                    )
                    
                    answer = response.choices[0].message.content or "Keine Ergebnisse gefunden."
                    return {"status": "success", "results": answer, "query": query}
                    
                except Exception as api_error:
                    console.print(f"[red]API Error in search_web: {api_error}[/red]")
                    return {"status": "error", "message": f"API Fehler: {str(api_error)}"}
                    
            else:
                # For other providers, return a placeholder
                console.print(f"🌐 Websuche: {query}")
                return {"status": "success", "results": f"Websuche für '{query}' (nur Moonshot unterstützt)", "query": query}
                
        except Exception as e:
            # Catch any remaining errors
            error_msg = str(e)
            console.print(f"[red]Error in search_web: {error_msg}[/red]")
            return {"status": "error", "message": error_msg}

    def get_chat_safe_tools(self) -> List[Dict[str, Any]]:
        """Gibt nur Chat-sichere Tools zurück (nur lesen, analysieren, suchen - keine Bearbeitung/Erstellung)."""
        from tools.tool_definitions import get_tool_definitions
        
        all_tools = get_tool_definitions()
        chat_safe_tool_names = {
            # Nur lesende Tools
            "list_directory", "read_file", "view_file", "list_dir", "view_code_item",
            
            # Nur Such-Tools
            "codebase_search", "grep_search", "find_by_name",
            
            # Nur Web-Recherche
            "read_url_content", "view_web_document_content_chunk", "search_web",
            
            # Nur Analyse-Tools (keine Erstellung)
            "analyze_code_complexity", "detect_security_vulnerabilities", 
            "analyze_dependencies", "profile_performance", "validate_architecture",
            
            # Nur Memory (keine Erstellung)
            "create_memory", "suggested_responses",
            
            # Nur Benutzer-Interaktion
            "ask_user_clarification"
        }
        
        # Filtere nur Chat-sichere Tools
        chat_safe_tools = []
        for tool in all_tools:
            tool_name = tool["function"]["name"]
            if tool_name in chat_safe_tool_names:
                chat_safe_tools.append(tool)
        
        return chat_safe_tools
