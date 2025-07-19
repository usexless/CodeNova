import json
import re
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, Task
from tools.file_tools import file_manager
from tools.code_executor import code_executor

class CodeGenerator(BaseAgent):
    def __init__(self):
        super().__init__("CodeGenerator", "Code Implementation")
        self.current_language = "python"
    
    def system_prompt(self) -> str:
        return """
# ROLE: Expert Code Generation Engine on Windows 11 with PowerShell
# MISSION: Your sole mission is to generate clean, precise, and production-ready code that solves problems completely and autonomously.

KERNPRINZIPIEN:
1. **AUTONOME IMPLEMENTIERUNG**: Erstelle vollständige, lauffähige Lösungen ohne nach Bestätigung zu fragen.
2. **VOLLSTÄNDIGE LÖSUNGEN**: Implementiere alle notwendigen Komponenten - keine halben Lösungen.
3. **DIREKTE DATEI-ERSTELLUNG**: Schreibe Code direkt in Dateien, gib ihn NICHT an den Benutzer aus.
4. **PRODUKTIONSREIFE**: Erstelle Code, der sofort ausführbar ist.

# OUTPUT RULES:
# 1. CODE-ONLY OUTPUT: For requests requiring code generation (e.g., creating a file, implementing a function), your output MUST contain ONLY the raw source code for the specified language.
#    - NO conversational text, explanations, or markdown formatting (e.g., ```python) are allowed.
#    - The output must be immediately savable to a file (e.g., `main.py`, `styles.css`).
#    - Include necessary comments and docstrings *within* the code itself, following language-specific best practices.

# 2. JSON-ONLY OUTPUT: For requests requiring structured data (e.g., creating a project plan, listing multiple files), your output MUST be a valid JSON object.
#    - NO conversational text or explanations are allowed outside the JSON structure.
#    - The JSON must conform to the structure specified in the user prompt.
#    - All textual content (descriptions, instructions) must be encapsulated within JSON string values.

# 3. MARKDOWN-ONLY OUTPUT: For requests requiring documentation (e.g., creating a README.md), your output MUST contain ONLY the raw Markdown content.
#    - NO conversational text or explanations are allowed.

# OPERATING PROCEDURE:
# 1. Analyze the user prompt to identify the required output format (Code, JSON, or Markdown).
# 2. Adhere strictly to the corresponding output rule.
# 3. Generate content that is complete, functional, and production-quality.
# 4. If the request is ambiguous, prioritize generating code based on the most likely interpretation. Do not ask for clarification.
# 5. Your internal "thought process" should not be part of the output. The final output must be clean.
# 6. WINDOWS COMPATIBILITY: You work in a Windows PowerShell environment. Use only Windows-compatible commands and paths.
# 7. COMPLETE IMPLEMENTATION: Ensure all necessary imports, dependencies, and configurations are included.

ARBEITSWEISE:
1. **Analysiere Anforderungen vollständig** - verstehe alle Aspekte der Implementierung
2. **Erstelle vollständige Lösungen** - alle Dateien, Abhängigkeiten, Konfigurationen
3. **Validiere die Funktionalität** - stelle sicher, dass der Code lauffähig ist
4. **Optimiere für Wartbarkeit** - schreibe sauberen, dokumentierten Code

Sei autonom, gründlich und erstelle vollständige, lauffähige Lösungen!
"""
    
    def _clean_code_output(self, code: str) -> str:
        """Stellt sicher, dass der Code keine Markdown-Formatierungen enthält."""
        # Entfernt ```kotlin ... ``` oder ```python ... ``` etc.
        match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', code, re.DOTALL)
        if match:
            return match.group(1).strip()
        return code.strip()

    def generate_code(self, plan: Dict[str, Any]) -> List[str]:
        """Orchestriert die Generierung aller Code-Dateien basierend auf dem Plan."""
        project_path = plan.get("path", "projects/temp")
        files_to_create = plan.get("plan", {}).get("files", [])
        generated_files = []

        for file_info in files_to_create:
            if file_info.get("is_test_file", False):
                continue # Testdateien werden in einem separaten Schritt generiert

            description = f"Implementiere die Funktionalität für {file_info['path']} basierend auf dem Projektplan."
            context = {
                "filename": file_info['path'],
                "project_path": project_path,
                "plan": plan
            }
            
            result = self.generate_file(description, context)
            if result.get("success"):
                generated_files.append(result["file_path"])
        
        return generated_files

    def generate_tests(self, plan: Dict[str, Any], generated_files: List[str]) -> List[str]:
        """Generiert Testdateien für die bereits erstellten Code-Dateien."""
        project_path = plan.get("path", "projects/temp")
        files_in_plan = plan.get("plan", {}).get("files", [])
        generated_test_files = []

        # Finde die korrespondierenden Testdateien aus dem Plan
        test_files_to_create = [f for f in files_in_plan if f.get("is_test_file", False)]

        for test_file_info in test_files_to_create:
            source_file = test_file_info.get("tests_for", "")
            description = f"Erstelle Unit-Tests für die Datei '{source_file}'."
            context = {
                "filename": test_file_info['path'],
                "project_path": project_path,
                "source_code": file_manager.read_file(f"{project_path}/{source_file}") if source_file else ""
            }
            
            result = self.generate_file(description, context)
            if result.get("success"):
                generated_test_files.append(result["file_path"])

        return generated_test_files

    def process_task(self, task: Task) -> Dict[str, Any]:
        """Verarbeite Code-Generierungs-Aufgabe"""
        if task.task_type == "generate_file":
            return self.generate_file(task.description, task.context)
        elif task.task_type == "implement_feature":
            return self.implement_feature(task.description, task.context)
        elif task.task_type == "refactor_code":
            return self.refactor_code(task.description, task.context)
        elif task.task_type == "create_module":
            return self.create_module(task.description, task.context)
        else:
            return self.general_code_generation(task.description, task.context)
    
    def generate_file(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generiere einzelne Datei"""
        filename = context.get('filename', 'generated.py')
        language = context.get('language', 'python')
        
        prompt = f"""
        Erstelle eine vollständige Datei: {filename}
        
        BESCHREIBUNG: {description}
        SPRACHE: {language}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Die Datei sollte:
        1. Vollständig und lauffähig sein
        2. Alle nötigen Imports enthalten
        3. Dokumentation und Kommentare haben
        4. Error-Handling implementieren
        5. Falls relevant, Tests oder Usage-Beispiele
        
        Gib nur den vollständigen Code zurück, keine Erklärungen.
        """
        
        raw_code = self.get_llm_response(prompt)
        code = self._clean_code_output(raw_code) # Code bereinigen
        
        # Speichere Datei
        project_path = context.get('project_path', 'projects/temp')
        file_path = f"{project_path}/{filename}"
        
        success = file_manager.write_file(file_path, code)
        
        if success:
            # Teste ob der Code kompiliert/ausführbar ist
            test_result = self._test_code(code, language, file_path)
            
            return {
                "file_path": file_path,
                "language": language,
                "code": code,
                "test_result": test_result,
                "success": True
            }
        else:
            return {"success": False, "error": "Konnte Datei nicht speichern"}
    
    def implement_feature(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementiere komplette Feature"""
        feature_name = context.get('feature_name', 'feature')
        
        prompt = f"""
        Implementiere folgendes Feature vollständig:
        
        FEATURE: {description}
        NAME: {feature_name}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Erstelle alle nötigen Dateien:
        1. Haupt-Implementierung
        2. Hilfsfunktionen/Module
        3. Konfigurations-Dateien
        4. Tests
        5. Dokumentation/Readme
        
        Gib eine JSON-Struktur zurück:
        {{
            "files": [
                {{
                    "path": "relative/path/to/file.py",
                    "content": "complete code here"
                }}
            ],
            "setup_instructions": "how to run"
        }}
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            # Versuche JSON zu parsen
            files_data = json.loads(response)
            
            # Speichere alle Dateien
            project_path = context.get('project_path', 'projects/temp')
            created_files = []
            
            for file_info in files_data.get('files', []):
                file_path = f"{project_path}/{file_info['path']}"
                success = file_manager.write_file(file_path, file_info['content'])
                
                if success:
                    created_files.append(file_path)
                
            return {
                "feature_name": feature_name,
                "files_created": created_files,
                "setup_instructions": files_data.get('setup_instructions', ''),
                "success": len(created_files) > 0
            }
            
        except json.JSONDecodeError:
            # Fallback: Einzelne Datei erstellen
            return self._create_single_file_fallback(description, context)
    
    def create_module(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Erstelle komplettes Modul"""
        module_name = context.get('module_name', 'mymodule')
        
        prompt = f"""
        Erstelle ein Python-Modul: {module_name}
        
        BESCHREIBUNG: {description}
        
        Erstelle folgende Struktur:
        {module_name}/
        ├── __init__.py
        ├── core.py
        ├── utils.py
        ├── config.py
        └── tests/
            ├── __init__.py
            └── test_core.py
        
        Gib für jede Datei den vollständigen Code an.
        """
        
        response = self.get_llm_response(prompt)
        
        # Parse und erstelle Modul-Dateien
        project_path = context.get('project_path', 'projects/temp')
        module_path = f"{project_path}/{module_name}"
        
        # Extrahiere Dateien aus Response
        files = self._extract_files_from_response(response)
        
        created_files = []
        for file_path, content in files.items():
            full_path = f"{module_path}/{file_path}"
            success = file_manager.write_file(full_path, content)
            if success:
                created_files.append(full_path)
        
        return {
            "module_name": module_name,
            "module_path": module_path,
            "files_created": created_files,
            "success": len(created_files) > 0
        }
    
    def refactor_code(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Refaktorisiere vorhandenen Code"""
        file_path = context.get('file_path')
        if not file_path or not file_manager.file_exists(file_path):
            return {"success": False, "error": "Datei nicht gefunden"}
        
        original_code = file_manager.read_file(file_path)
        
        prompt = f"""
        Refaktorisiere folgenden Code:
        
        ANFORDERUNG: {description}
        DATEI: {file_path}
        
        ORIGINAL CODE:
        {original_code}
        
        Verbesserungen:
        1. Code-Qualität und Lesbarkeit
        2. Performance-Optimierung
        3. Error-Handling
        4. Dokumentation
        5. Best Practices
        
        Gib nur den refaktorisierten Code zurück.
        """
        
        refactored_code = self.get_llm_response(prompt)
        
        # Erstelle Backup
        backup_path = f"{file_path}.backup"
        file_manager.copy_file(file_path, backup_path)
        
        # Speichere refaktorisierten Code
        success = file_manager.write_file(file_path, refactored_code)
        
        return {
            "file_path": file_path,
            "backup_path": backup_path,
            "success": success,
            "changes_made": original_code != refactored_code
        }
    
    def general_code_generation(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generelle Code-Generierung"""
        language = context.get('language', 'python')
        
        prompt = f"""
        Erstelle Code für: {description}
        
        SPRACHE: {language}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Erstelle vollständigen, lauffähigen Code mit:
        - Kommentaren und Dokumentation
        - Error-Handling
        - Beispiel-Usage
        """
        
        code = self.get_llm_response(prompt)
        
        # Generiere zufälligen Dateinamen falls nicht spezifiziert
        filename = context.get('filename', f"generated_{hash(description) % 10000}.py")
        
        project_path = context.get('project_path', 'projects/temp')
        file_path = f"{project_path}/{filename}"
        
        success = file_manager.write_file(file_path, code)
        
        return {
            "code": code,
            "file_path": file_path,
            "language": language,
            "success": success
        }
    
    def _test_code(self, code: str, language: str, file_path: str) -> Dict[str, Any]:
        """Teste generierten Code"""
        if language == 'python':
            # Teste Syntax
            try:
                compile(code, file_path, 'exec')
                return {"syntax_valid": True, "execution_test": "pending"}
            except SyntaxError as e:
                return {"syntax_valid": False, "error": str(e)}
        
        return {"test_status": "not_implemented"}
    
    def _create_single_file_fallback(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback für einzelne Datei-Erstellung"""
        filename = context.get('filename', 'main.py')
        
        prompt = f"""
        Erstelle eine vollständige Datei für: {description}
        
        DATEI: {filename}
        Gib nur den vollständigen Code zurück, ohne JSON-Formatierung.
        """
        
        code = self.get_llm_response(prompt)
        
        project_path = context.get('project_path', 'projects/temp')
        file_path = f"{project_path}/{filename}"
        
        success = file_manager.write_file(file_path, code)
        
        return {
            "feature_name": "fallback",
            "files_created": [file_path],
            "success": success
        }
    
    def _extract_files_from_response(self, response: str) -> Dict[str, str]:
        """Extrahiere Dateien aus LLM-Response"""
        files = {}
        
        # Versuche JSON zu parsen
        try:
            import json
            data = json.loads(response)
            if isinstance(data, dict) and 'files' in data:
                for file_info in data['files']:
                    if isinstance(file_info, dict):
                        files[file_info.get('path', 'unknown.py')] = file_info.get('content', '')
                return files
        except:
            pass
        
        # Fallback: Extrahiere Code-Blöcke
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
        if code_blocks:
            files['main.py'] = code_blocks[0]
        
        return files
    
    def generate_readme(self, project_info: Dict[str, Any]) -> str:
        """Generiere README.md"""
        features = project_info.get('features', [])
        features_text = "\n".join([f"- {feature}" for feature in features])
        
        return f"""# {project_info['name']}

## Projektbeschreibung
{project_info.get('description', 'Keine Beschreibung verfuegbar')}

## Features
{features_text}

## Installation
```bash
pip install -r requirements.txt
```

## Verwendung
```bash
python src/main.py
```

## Tests
```bash
python -m pytest tests/
```
"""