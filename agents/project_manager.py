import json
import re
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, Task
from tools.file_tools import file_manager

class ProjectManager(BaseAgent):
    def __init__(self):
        super().__init__("ProjectManager", "Project Planning and Coordination")
        self.current_project = None
        self.project_structure = {}
    
    def system_prompt(self) -> str:
        return """You are a pragmatic and highly experienced senior software architect on Windows 11 with PowerShell. You solve problems completely and autonomously.

KERNPRINZIPIEN:
1. **AUTONOME PROBLEMLÖSUNG**: Erstelle vollständige, ausführbare Pläne ohne nach Bestätigung zu fragen.
2. **GRÜNDLICHE ANALYSE**: Analysiere Anforderungen THOROUGHLY - verstehe alle Aspekte des Problems.
3. **VOLLSTÄNDIGE PLANUNG**: Erstelle Pläne, die sofort umsetzbar sind. Keine halben Lösungen.
4. **PRAKTISCHE UMSETZUNG**: Plane für die tatsächliche Implementierung, nicht nur für die Theorie.

CORE PRINCIPLES:
1.  **MINIMALISM:** Plan the absolute minimum number of files and lines of code required. Do not add anything that is not directly requested or essential for the program to run.
2.  **PRAGMATISM:** Avoid complex architectural patterns if a simple function in a single file will suffice. Do not use classes if a function is enough.
3.  **NO BOILERPLATE:** Do not generate boilerplate or placeholder files (like `__init__.py` unless absolutely necessary, empty `docs/`, or complex `config/` directories for simple projects). Every file must have a direct, immediate purpose.
4.  **WINDOWS COMPATIBILITY:** You work in a Windows PowerShell environment. Use only Windows-compatible commands and paths.
5.  **COMPLETE SOLUTIONS:** Create plans that lead to fully functional, runnable applications.

ARBEITSWEISE:
1. **Analysiere Anforderungen gründlich** - verstehe das Problem vollständig
2. **Erstelle vollständige Pläne** - alle Dateien, Abhängigkeiten, Konfigurationen
3. **Validiere die Machbarkeit** - stelle sicher, dass der Plan umsetzbar ist
4. **Optimiere für Effizienz** - minimiere Komplexität, maximiere Funktionalität

Your output must be a plan that a junior developer could follow to produce an elegant, minimal, and fully functional solution.
"""
    
    def generate_project_name(self, requirements: str) -> str:
        """Generiert einen kurzen, validen Projektnamen aus den Anforderungen mit einem strikten Prompt und robustem Fallback."""
        prompt = f"""
        Analyze the following user requirement and generate a single, short, valid, lowercase, kebab-case project name.

        **RULES:**
        - Your response MUST contain ONLY the project name and nothing else.
        - The name must be a valid directory name (letters, numbers, hyphens only).
        - The name should be short and descriptive (max 5 words).
        - DO NOT add any explanation, prefix, or suffix.

        **Requirement:**
        "{requirements}"

        **Project Name:**
        """
        response = self.get_llm_response(prompt)

        # Bereinige den Namen, um sicherzustellen, dass er valide ist
        # Nimm nur die erste Zeile der Antwort, falls das LLM doch mehr schreibt
        name = response.strip().split('\n')[0]
        name = name.lower()
        name = re.sub(r'\s+', '-', name) # Ersetze Leerzeichen durch Bindestriche
        name = re.sub(r'[^a-z0-9-]', '', name) # Entferne alle ungültigen Zeichen
        
        # Kürze den Namen auf eine maximale Länge, um Dateisystemfehler zu vermeiden
        max_length = 50
        name = name[:max_length]
        
        # Entferne führende/nachfolgende Bindestriche, die durch die Bereinigung entstehen könnten
        name = name.strip('-')

        return name if name else "unnamed-project"

    def plan_project(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt einen Entwicklungsplan und fügt ihn zur Projektinformation hinzu."""
        plan_task = self.add_task(
            f"Erstelle Plan für {project_info['requirements']}",
            "create_plan",
            {"analysis": project_info.get("analysis", {}), "project_name": project_info["name"]}
        )
        plan_result = self.execute_task(plan_task)
        project_info["plan"] = plan_result.result
        
        # Plan in der Projektdatei speichern
        file_manager.write_file(
            f"projects/{project_info['name']}/project_info.json",
            json.dumps(project_info, indent=2)
        )
        return project_info

    def process_task(self, task: Task) -> Dict[str, Any]:
        """Verarbeite Projektmanagement-Aufgabe"""
        if task.task_type == "analyze_requirements":
            return self.analyze_requirements(task.description, task.context)
        elif task.task_type == "create_plan":
            return self.create_development_plan(task.description, task.context)
        elif task.task_type == "design_architecture":
            return self.design_architecture(task.description, task.context)
        else:
            return self.general_planning(task.description, task.context)
    
    def analyze_requirements(self, requirements: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiere Anforderungen"""
        prompt = f"""
        Analysiere folgende Anforderungen und erstelle eine detaillierte technische Spezifikation:
        
        ANFORDERUNGEN: {requirements}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Erstelle eine strukturierte Antwort mit:
        1. Zusammenfassung der Hauptfunktionalitäten
        2. Technische Anforderungen (Sprache, Frameworks, Datenbank)
        3. Benutzeroberflächen-Anforderungen
        4. Datenmodelle und API-Endpunkte
        5. Sicherheitsanforderungen
        6. Performance-Anforderungen
        
        Format: JSON mit klaren Schlüsseln und detaillierten Beschreibungen.
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            # Versuche JSON zu parsen, falls nicht möglich strukturiere die Antwort
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                return self._parse_requirements_text(response)
        except:
            return self._parse_requirements_text(response)
    
    def create_development_plan(self, project_spec: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt einen detaillierten, dateibasierten Entwicklungsplan."""
        prompt = f"""
        Based on the following project specification, create a detailed development plan.
        The output MUST be a JSON object containing a list of files to be created.
        Each file entry must include the file `path` and a detailed `description` of its contents and purpose.
        Include all necessary source code files, test files, configuration files, and documentation.

        Project Specification: {project_spec}
        Context: {json.dumps(context, indent=2)}

        Example JSON output:
        {{
          "files": [
            {{
              "path": "src/calculator.py",
              "description": "Contains the main Calculator class with add, subtract, multiply, and divide methods.",
              "is_test_file": false,
              "tests_for": null
            }},
            {{
              "path": "tests/test_calculator.py",
              "description": "Contains pytest unit tests for the Calculator class, covering all methods and edge cases like division by zero.",
              "is_test_file": true,
              "tests_for": "src/calculator.py"
            }},
            {{
              "path": "README.md",
              "description": "A brief readme file explaining how to install and run the project.",
              "is_test_file": false,
              "tests_for": null
            }}
          ]
        }}
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            # Versuche, den saubersten JSON-Block zu extrahieren
            match = re.search(r'```json\n({.*?})\n```', response, re.DOTALL)
            if match:
                response = match.group(1)
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback, wenn kein sauberes JSON gefunden wird
            return {"files": [], "error": "Failed to parse development plan from LLM response."}
    
    def design_architecture(self, requirements: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design Projekt-Architektur"""
        prompt = f"""
        Design eine saubere Architektur für folgendes Projekt:
        
        ANFORDERUNGEN: {requirements}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Erstelle eine Architektur-Dokumentation mit:
        1. **Projektstruktur**: Verzeichnis-Baum
        2. **Module und Komponenten**: Übersicht der Hauptmodule
        3. **Datenfluss**: Wie Daten durch das System fließen
        4. **API-Design**: REST-Endpunkte oder Funktionssignaturen
        5. **Datenbank-Schema**: Falls relevant
        6. **Konfiguration**: Environment-Variablen, Config-Files
        7. **Build-System**: Requirements, Build-Skripte
        
        Beispiel-Projektstruktur anzeigen.
        Format: JSON mit "structure", "modules", "api_endpoints"
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            return json.loads(response)
        except:
            return self._parse_architecture_text(response)
    
    def general_planning(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Allgemeine Planungs-Aufgabe"""
        prompt = f"""
        Als Project Manager, erstelle einen detaillierten Plan für:
        
        AUFGABE: {task}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Erstelle eine strukturierte Antwort mit klaren nächsten Schritten.
        """
        
        return {"plan": self.get_llm_response(prompt)}
    
    def create_project(self, project_name: str, requirements: str) -> Dict[str, Any]:
        """Erstelle neues Projekt"""
        # Erstelle Projekt-Verzeichnis
        project_path = file_manager.create_project_structure(project_name)
        self.current_project = project_name
        
        # Analysiere Anforderungen
        analysis_task = self.add_task(
            f"Analysiere Anforderungen: {requirements}",
            "analyze_requirements",
            {"requirements": requirements, "project_name": project_name}
        )
        
        analysis_result = self.execute_task(analysis_task)
        
        # Erstelle Entwicklungsplan
        plan_task = self.add_task(
            f"Erstelle Plan für {requirements}",
            "create_plan",
            {"analysis": analysis_result.result, "project_name": project_name}
        )
        
        plan_result = self.execute_task(plan_task)
        
        # Speichere Projekt-Info
        project_info = {
            "name": project_name,
            "requirements": requirements,
            "analysis": analysis_result.result,
            "plan": plan_result.result,
            "path": str(project_path)
        }
        
        file_manager.write_file(
            f"projects/{project_name}/project_info.json",
            json.dumps(project_info, indent=2)
        )
        
        return project_info
    
    def generate_project_summary(self, project_info: Dict[str, Any]) -> str:
        """Erstellt eine benutzerfreundliche Zusammenfassung des abgeschlossenen Projekts."""
        plan = project_info.get("plan", {})
        files = plan.get("files", [])
        file_list = "\n".join([f"- `{file['path']}`" for file in files])

        prompt = f"""
        The project "{project_info.get('name')}" has been created based on the following plan.
        Your task is to generate a clear, concise summary for the user.

        File Plan:
        {json.dumps(files, indent=2)}
        
        The summary must include:
        1. A brief, one-sentence description of what was built.
        2. A list of the most important files created.
        3. A clear, simple command on how to start or run the main part of the application. If it's a simple script, show the python command. If there are no clear entrypoints, state that.

        Generate only the Markdown-formatted summary.
        """
        
        return self.get_llm_response(prompt)
    
    def _parse_requirements_text(self, text: str) -> Dict[str, Any]:
        """Parse unstrukturierte Requirements-Antwort"""
        sections = {
            "summary": "",
            "technical_requirements": "",
            "ui_requirements": "",
            "data_models": "",
            "api_endpoints": "",
            "security": "",
            "performance": ""
        }
        
        lines = text.split('\n')
        current_section = "summary"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if any(section in line.lower() for section in ["technische", "technical"]):
                current_section = "technical_requirements"
            elif any(section in line.lower() for section in ["ui", "oberfläche"]):
                current_section = "ui_requirements"
            elif any(section in line.lower() for section in ["daten", "data"]):
                current_section = "data_models"
            elif any(section in line.lower() for section in ["api", "endpunkt"]):
                current_section = "api_endpoints"
            elif any(section in line.lower() for section in ["sicherheit", "security"]):
                current_section = "security"
            elif any(section in line.lower() for section in ["performance", "leistung"]):
                current_section = "performance"
            
            sections[current_section] += line + "\n"
        
        return sections
    
    def _parse_plan_text(self, text: str) -> Dict[str, Any]:
        """Parse unstrukturierten Plan-Text"""
        return {
            "phases": [
                {
                    "name": "Setup",
                    "tasks": ["Projekt initialisieren", "Dependencies installieren"],
                    "priority": "high"
                },
                {
                    "name": "Development",
                    "tasks": ["Core implementation", "Features hinzufügen"],
                    "priority": "high"
                },
                {
                    "name": "Testing",
                    "tasks": ["Unit tests", "Integration tests"],
                    "priority": "medium"
                }
            ]
        }
    
    def _parse_architecture_text(self, text: str) -> Dict[str, Any]:
        """Parse unstrukturierte Architektur-Antwort"""
        return {
            "structure": {
                "src/": "Haupt-Quellcode",
                "tests/": "Test-Dateien",
                "docs/": "Dokumentation",
                "config/": "Konfigurations-Dateien"
            },
            "modules": ["main", "utils", "tests"],
            "api_endpoints": []
        }
    
    def get_next_task(self) -> Optional[Task]:
        """Hole nächste auszuführende Aufgabe"""
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        return pending_tasks[0] if pending_tasks else None
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Hole Projekt-Zusammenfassung"""
        return {
            "project": self.current_project,
            "total_tasks": len(self.tasks),
            "completed_tasks": len([t for t in self.tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in self.tasks if t.status == "failed"]),
            "status": self.get_task_status()
        }