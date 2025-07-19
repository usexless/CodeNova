"""
Definiert die JSON-Schemata für alle Tools, die von den LLM-Agenten aufgerufen werden können.
Dieses Format ist kompatibel mit der OpenAI/Moonshot Tool-Calling-API.
"""

from typing import List, Dict, Any

def get_tool_definitions() -> List[Dict[str, Any]]:
    """Gibt eine Liste aller verfügbaren Tool-Definitionen zurück."""
    
    tools = [
        # Basic Tools (existing)
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "Listet den Inhalt eines Verzeichnisses auf. STARTE IMMER HIER - verstehe die Projektstruktur gründlich, bevor du andere Aktionen durchführst. Sammle alle verfügbaren Informationen proaktiv.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Der relative Pfad zum Verzeichnis, das aufgelistet werden soll. Gib '.' für das aktuelle Verzeichnis an."
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Liest den Inhalt einer Datei vollständig. Verwende dies proaktiv, um alle notwendigen Informationen zu sammeln, bevor du Entscheidungen triffst. Sei THOROUGH bei der Informationssammlung.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Der Pfad zur Datei, die gelesen werden soll."
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Schreibt oder überschreibt eine Datei mit neuem Inhalt. Erstelle vollständige, lauffähige Lösungen. Gib Code NICHT an den Benutzer aus - schreibe ihn direkt in Dateien.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Der Pfad zur Datei, die geschrieben werden soll."
                        },
                        "content": {
                            "type": "string",
                            "description": "Der vollständige Inhalt, der in die Datei geschrieben werden soll. Stelle sicher, dass der Inhalt vollständig und lauffähig ist."
                        }
                    },
                    "required": ["path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_shell_command",
                "description": "Führt einen Shell-Befehl aus und gibt die Ausgabe (stdout und stderr) sowie den Exit-Code zurück. WICHTIG: Du arbeitest in einer Windows PowerShell-Umgebung. Verwende nur Windows-kompatible Befehle und Pfade. Verwende dies proaktiv, um Probleme zu lösen und Informationen zu sammeln.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Der auszuführende Shell-Befehl. Verwende nur Windows PowerShell-kompatible Befehle. Sei spezifisch und vollständig."
                        }
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ask_user_clarification",
                "description": "Stellt dem Benutzer eine klärende Frage, wenn die Anforderungen unklar sind oder eine wichtige Entscheidung getroffen werden muss. Sollte nur verwendet werden, wenn eine Annahme riskant wäre.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Die Frage, die dem Benutzer gestellt werden soll."
                        }
                    },
                    "required": ["question"]
                }
            }
        },
        
        # Advanced File Operations
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Bearbeitet eine bestehende Datei mit präzisen Änderungen. Verwende dies für gezielte Modifikationen ohne die gesamte Datei zu überschreiben.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "TargetFile": {
                            "type": "string",
                            "description": "Der absolute Pfad zur zu bearbeitenden Datei."
                        },
                        "Instruction": {
                            "type": "string",
                            "description": "Eine Beschreibung der Änderungen, die vorgenommen werden sollen."
                        },
                        "CodeEdit": {
                            "type": "string",
                            "description": "Nur die präzisen Codezeilen, die bearbeitet werden sollen. Verwende {{ ... }} für unveränderten Code."
                        },
                        "CodeMarkdownLanguage": {
                            "type": "string",
                            "description": "Die Markdown-Sprache für den Codeblock, z.B. 'python' oder 'javascript'."
                        },
                        "TargetLintErrorIds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "IDs von Lint-Fehlern, die diese Bearbeitung beheben soll."
                        }
                    },
                    "required": ["TargetFile", "Instruction", "CodeEdit", "CodeMarkdownLanguage"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_file",
                "description": "Zeigt den Inhalt einer Datei in einem bestimmten Bereich an. Ideal für große Dateien, bei denen nur bestimmte Bereiche relevant sind.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "AbsolutePath": {
                            "type": "string",
                            "description": "Absoluter Pfad zur anzuzeigenden Datei."
                        },
                        "StartLine": {
                            "type": "integer",
                            "description": "Startzeile (0-basiert)."
                        },
                        "EndLine": {
                            "type": "integer",
                            "description": "Endzeile (inklusiv, max. 200 Zeilen von StartLine entfernt)."
                        },
                        "IncludeSummaryOfOtherLines": {
                            "type": "boolean",
                            "description": "Ob eine Zusammenfassung der anderen Zeilen eingeschlossen werden soll."
                        }
                    },
                    "required": ["AbsolutePath", "StartLine", "EndLine", "IncludeSummaryOfOtherLines"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_to_file",
                "description": "Erstellt eine neue Datei und schreibt Inhalt hinein. Erstellt automatisch fehlende Verzeichnisse.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "TargetFile": {
                            "type": "string",
                            "description": "Der absolute Pfad zur zu erstellenden Datei."
                        },
                        "CodeContent": {
                            "type": "string",
                            "description": "Der Inhalt, der in die Datei geschrieben werden soll."
                        },
                        "EmptyFile": {
                            "type": "boolean",
                            "description": "Ob eine leere Datei erstellt werden soll."
                        }
                    },
                    "required": ["TargetFile", "CodeContent", "EmptyFile"]
                }
            }
        },
        
        # Advanced Search and Navigation
        {
            "type": "function",
            "function": {
                "name": "codebase_search",
                "description": "Führt eine semantische Suche im Codebase durch. Findet Code-Snippets, die am relevantesten für die Suchanfrage sind. Verwende dies als Hauptwerkzeug für die Codebase-Exploration.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Query": {
                            "type": "string",
                            "description": "Die Suchanfrage. Sei präzise und beziehe dich auf Funktion oder Zweck des Codes."
                        },
                        "TargetDirectories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Liste absoluter Pfade zu Verzeichnissen, in denen gesucht werden soll."
                        }
                    },
                    "required": ["Query", "TargetDirectories"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "grep_search",
                "description": "Verwendet ripgrep für exakte Muster-Suche in Dateien oder Verzeichnissen. Ideal für präzise Text-Suche.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "SearchPath": {
                            "type": "string",
                            "description": "Der Pfad, in dem gesucht werden soll (Datei oder Verzeichnis)."
                        },
                        "Query": {
                            "type": "string",
                            "description": "Der Suchbegriff oder das Muster, nach dem gesucht werden soll."
                        },
                        "MatchPerLine": {
                            "type": "boolean",
                            "description": "Ob jede übereinstimmende Zeile zurückgegeben werden soll."
                        },
                        "Includes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dateien oder Verzeichnisse, in denen gesucht werden soll."
                        },
                        "CaseInsensitive": {
                            "type": "boolean",
                            "description": "Ob die Suche Groß-/Kleinschreibung ignorieren soll."
                        }
                    },
                    "required": ["SearchPath", "Query", "MatchPerLine", "Includes", "CaseInsensitive"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_by_name",
                "description": "Sucht nach Dateien und Unterverzeichnissen in einem angegebenen Verzeichnis mit erweiterten Filtern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "SearchDirectory": {
                            "type": "string",
                            "description": "Das Verzeichnis, in dem gesucht werden soll."
                        },
                        "Pattern": {
                            "type": "string",
                            "description": "Optionales Muster für die Suche (Glob-Format)."
                        },
                        "Excludes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dateien/Verzeichnisse, die ausgeschlossen werden sollen."
                        },
                        "Type": {
                            "type": "string",
                            "enum": ["file", "directory", "any"],
                            "description": "Typ-Filter."
                        },
                        "MaxDepth": {
                            "type": "integer",
                            "description": "Maximale Suchtiefe."
                        },
                        "Extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dateierweiterungen, die eingeschlossen werden sollen."
                        },
                        "FullPath": {
                            "type": "boolean",
                            "description": "Ob der vollständige Pfad dem Muster entsprechen muss."
                        }
                    },
                    "required": ["SearchDirectory", "Pattern", "Excludes", "Type", "MaxDepth", "Extensions", "FullPath"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": "Listet den Inhalt eines Verzeichnisses mit detaillierten Informationen auf.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "DirectoryPath": {
                            "type": "string",
                            "description": "Absoluter Pfad zum aufzulistenden Verzeichnis."
                        }
                    },
                    "required": ["DirectoryPath"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_code_item",
                "description": "Zeigt den Inhalt eines Code-Elements wie eine Klasse oder Funktion in einer Datei an.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "File": {
                            "type": "string",
                            "description": "Absoluter Pfad zur Datei."
                        },
                        "NodePath": {
                            "type": "string",
                            "description": "Pfad des Elements innerhalb der Datei, z.B. 'package.class.FunctionName'."
                        }
                    },
                    "required": ["NodePath"]
                }
            }
        },
        
        # Command Execution and Monitoring
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Führt einen Terminal-Befehl aus. Betriebssystem: Windows. Shell: PowerShell. Verwende nur Windows-kompatible Befehle.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "CommandLine": {
                            "type": "string",
                            "description": "Die exakte Befehlszeile, die ausgeführt werden soll."
                        },
                        "Cwd": {
                            "type": "string",
                            "description": "Das Arbeitsverzeichnis für den Befehl."
                        },
                        "Blocking": {
                            "type": "boolean",
                            "description": "Ob der Befehl blockieren soll, bis er vollständig beendet ist."
                        },
                        "WaitMsBeforeAsync": {
                            "type": "integer",
                            "description": "Millisekunden zu warten, bevor der Befehl asynchron wird."
                        },
                        "SafeToAutoRun": {
                            "type": "boolean",
                            "description": "Ob der Befehl sicher ohne Benutzerbestätigung ausgeführt werden kann."
                        }
                    },
                    "required": ["CommandLine", "Cwd", "Blocking", "WaitMsBeforeAsync", "SafeToAutoRun"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "command_status",
                "description": "Prüft den Status eines zuvor ausgeführten Terminal-Befehls anhand seiner ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "CommandId": {
                            "type": "string",
                            "description": "ID des Befehls, dessen Status geprüft werden soll."
                        },
                        "OutputPriority": {
                            "type": "string",
                            "enum": ["top", "bottom", "split"],
                            "description": "Priorität für die Anzeige der Befehlsausgabe."
                        },
                        "OutputCharacterCount": {
                            "type": "integer",
                            "description": "Anzahl der anzuzeigenden Zeichen."
                        },
                        "WaitDurationSeconds": {
                            "type": "integer",
                            "description": "Sekunden zu warten, bevor der Status geprüft wird."
                        }
                    },
                    "required": ["CommandId", "OutputPriority", "OutputCharacterCount", "WaitDurationSeconds"]
                }
            }
        },
        # Web Deployment Tools
        {
            "type": "function",
            "function": {
                "name": "read_deployment_config",
                "description": "Liest und validiert eine Deployment-Konfigurationsdatei (JSON oder YAML).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Pfad zur Konfigurationsdatei."}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "deploy_web_app",
                "description": "Deployt eine Webanwendung auf eine unterstützte Plattform (z. B. Netlify).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string", "description": "Pfad zum Webprojekt"},
                        "platform": {"type": "string", "description": "Deployment-Plattform", "default": "netlify"}
                    },
                    "required": ["project_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_deploy_status",
                "description": "Überprüft den Status eines zuvor gestarteten Deployments.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "deploy_id": {"type": "string", "description": "ID des Deployments"}
                    },
                    "required": ["deploy_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "browser_preview",
                "description": "Startet einen einfachen HTTP-Server zur lokalen Vorschau im Browser.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Verzeichnis, das serviert werden soll"},
                        "port": {"type": "integer", "description": "Port für den HTTP-Server", "default": 8000}
                    },
                    "required": ["directory"]
                }
            }
        },
        

        
        # Web Content and Search
        {
            "type": "function",
            "function": {
                "name": "read_url_content",
                "description": "Liest Inhalt von einer URL. Die URL muss auf eine gültige Internet-Ressource zeigen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Url": {
                            "type": "string",
                            "description": "Die URL, von der Inhalt gelesen werden soll."
                        }
                    },
                    "required": ["Url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_web_document_content_chunk",
                "description": "Zeigt einen spezifischen Chunk eines Webdokuments anhand seiner URL und Chunk-Position an.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Die URL, zu der der Chunk gehört."
                        },
                        "position": {
                            "type": "integer",
                            "description": "Die Position des anzuzeigenden Chunks."
                        }
                    },
                    "required": ["url", "position"]
                }
            }
        },
        
        # Memory and Interaction
        {
            "type": "function",
            "function": {
                "name": "create_memory",
                "description": "Speichert wichtigen Kontext in einer Memory-Datenbank. Verwende dies für Benutzereinstellungen, wichtige Code-Snippets, technische Stacks und andere wichtige Informationen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Id": {
                            "type": "string",
                            "description": "ID eines bestehenden MEMORY zum Aktualisieren oder Löschen."
                        },
                        "Title": {
                            "type": "string",
                            "description": "Beschreibender Titel für ein neues oder aktualisiertes MEMORY."
                        },
                        "Content": {
                            "type": "string",
                            "description": "Inhalt eines neuen oder aktualisierten MEMORY."
                        },
                        "CorpusNames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Namen der Workspaces, die mit dem MEMORY verknüpft sind."
                        },
                        "Tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags für das MEMORY (snake_case)."
                        },
                        "Action": {
                            "type": "string",
                            "enum": ["create", "update", "delete"],
                            "description": "Die Art der Aktion für das MEMORY."
                        },
                        "UserTriggered": {
                            "type": "boolean",
                            "description": "Ob der Benutzer explizit nach der Erstellung/Änderung gefragt hat."
                        }
                    },
                    "required": ["Id", "Title", "Content", "CorpusNames", "Tags", "Action", "UserTriggered"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "suggested_responses",
                "description": "Stellt eine kleine Anzahl möglicher Antworten auf eine Frage bereit. Verwende dies sparsam und nur bei einfachen Multiple-Choice-Optionen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Liste der Vorschläge. Jeder sollte maximal ein paar Wörter sein, nicht mehr als 3 Optionen."
                        }
                    },
                    "required": ["Suggestions"]
                }
            }
        },
        
        # Advanced Moonshot Tools
        {
            "type": "function",
            "function": {
                "name": "analyze_code_complexity",
                "description": "Analysiert die Komplexität von Code und identifiziert potenzielle Verbesserungsbereiche.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur zu analysierenden Datei."
                        },
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Zu berechnende Metriken (cyclomatic, cognitive, halstead, etc.)."
                        }
                    },
                    "required": ["file_path", "metrics"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_documentation",
                "description": "Generiert automatisch Dokumentation für Code-Dateien.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur Datei, für die Dokumentation generiert werden soll."
                        },
                        "doc_type": {
                            "type": "string",
                            "enum": ["readme", "api", "inline", "architecture"],
                            "description": "Art der zu generierenden Dokumentation."
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Pfad für die Ausgabedatei."
                        }
                    },
                    "required": ["file_path", "doc_type", "output_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "optimize_code",
                "description": "Optimiert Code für Performance, Lesbarkeit oder Speichernutzung.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur zu optimierenden Datei."
                        },
                        "optimization_type": {
                            "type": "string",
                            "enum": ["performance", "readability", "memory", "security"],
                            "description": "Art der Optimierung."
                        },
                        "backup_original": {
                            "type": "boolean",
                            "description": "Ob eine Sicherungskopie der Originaldatei erstellt werden soll."
                        }
                    },
                    "required": ["file_path", "optimization_type", "backup_original"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "detect_security_vulnerabilities",
                "description": "Erkennt Sicherheitslücken in Code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur zu analysierenden Datei."
                        },
                        "severity_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Minimale Schwere der zu meldenden Lücken."
                        }
                    },
                    "required": ["file_path", "severity_level"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_test_cases",
                "description": "Generiert automatisch Testfälle für Code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur Datei, für die Tests generiert werden sollen."
                        },
                        "test_framework": {
                            "type": "string",
                            "enum": ["pytest", "unittest", "jest", "mocha"],
                            "description": "Zu verwendendes Test-Framework."
                        },
                        "coverage_target": {
                            "type": "number",
                            "description": "Ziel-Coverage in Prozent."
                        }
                    },
                    "required": ["file_path", "test_framework", "coverage_target"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "refactor_code",
                "description": "Führt automatische Code-Refaktorierung durch.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur zu refaktorierenden Datei."
                        },
                        "refactoring_type": {
                            "type": "string",
                            "enum": ["extract_method", "rename", "move", "simplify"],
                            "description": "Art der Refaktorierung."
                        },
                        "target_pattern": {
                            "type": "string",
                            "description": "Zielmuster für die Refaktorierung."
                        }
                    },
                    "required": ["file_path", "refactoring_type", "target_pattern"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_dependencies",
                "description": "Analysiert Abhängigkeiten und erstellt Abhängigkeitsgraphen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Pfad zum Projekt."
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "dot", "svg", "png"],
                            "description": "Ausgabeformat für den Abhängigkeitsgraphen."
                        }
                    },
                    "required": ["project_path", "output_format"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "profile_performance",
                "description": "Führt Performance-Profiling für Code aus.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur zu profilierenden Datei."
                        },
                        "profiling_type": {
                            "type": "string",
                            "enum": ["cpu", "memory", "io", "network"],
                            "description": "Art des Profilings."
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Profiling-Dauer in Sekunden."
                        }
                    },
                    "required": ["file_path", "profiling_type", "duration"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "validate_architecture",
                "description": "Validiert die Architektur eines Projekts gegen Best Practices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Pfad zum Projekt."
                        },
                        "architecture_pattern": {
                            "type": "string",
                            "enum": ["mvc", "mvvm", "clean", "microservices"],
                            "description": "Erwartetes Architekturmuster."
                        }
                    },
                    "required": ["project_path", "architecture_pattern"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_api_spec",
                "description": "Generiert API-Spezifikationen aus Code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Pfad zur API-Datei."
                        },
                        "spec_format": {
                            "type": "string",
                            "enum": ["openapi", "swagger", "raml"],
                            "description": "Format der API-Spezifikation."
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Ausgabepfad für die Spezifikation."
                        }
                    },
                    "required": ["file_path", "spec_format", "output_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Führt eine Websuche durch und gibt relevante Ergebnisse zurück. Verwende dies für externe Recherche und aktuelle Informationen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Die Suchanfrage für die Websuche."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    return tools 