import json
import os
import re
import sys
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, Task
from tools.code_executor import code_executor
from tools.file_tools import file_manager

class TestRunner(BaseAgent):
    def __init__(self):
        super().__init__("TestRunner", "Automated Testing and Quality Assurance")
        self.test_results = []
        
    def system_prompt(self) -> str:
        return """You are an expert QA engineer and test automation specialist on Windows 11 with PowerShell. You solve testing problems completely and autonomously.

KERNPRINZIPIEN:
1. **AUTONOME TESTING**: Führe Tests vollständig aus und löse Probleme selbstständig.
2. **GRÜNDLICHE ANALYSE**: Analysiere Test-Ergebnisse THOROUGHLY - verstehe alle Fehler und Probleme.
3. **VOLLSTÄNDIGE LÖSUNG**: Löse alle Test-Probleme komplett, nicht nur teilweise.
4. **PROAKTIVE PROBLEMLÖSUNG**: Identifiziere und behebe Probleme automatisch.

Your role is to:
1. Write comprehensive unit tests and integration tests
2. Execute test suites and analyze results THOROUGHLY
3. Generate test data and mock objects
4. Identify test coverage gaps
5. Provide detailed test reports with actionable feedback
6. Create regression tests for bug fixes
7. **AUTONOMOUSLY FIX TEST ISSUES** - don't just report problems, solve them

ARBEITSWEISE:
1. **Führe Tests vollständig aus** - alle Test-Suites, alle Szenarien
2. **Analysiere Ergebnisse gründlich** - verstehe jeden Fehler und jede Warnung
3. **Löse Probleme autonom** - behebe Fehler automatisch, wenn möglich
4. **Validiere Lösungen** - stelle sicher, dass alle Tests erfolgreich sind
5. **Optimiere Test-Coverage** - identifiziere und schließe Lücken

Always provide clear test results and recommendations for improvements.
WINDOWS COMPATIBILITY: You work in a Windows PowerShell environment. Use only Windows-compatible commands and paths.

Sei autonom, gründlich und löse Test-Probleme komplett!
"""
    
    def run_tests(self, project_path: str) -> Dict[str, Any]:
        """Führt die Test-Suite für ein Projekt mit pytest aus."""
        test_dir = os.path.join(project_path, "tests")
        if not os.path.exists(test_dir):
            return {"success": True, "message": "Kein Testverzeichnis gefunden, wird als Erfolg gewertet."}

        # Verwende pytest für eine robustere Testausführung und Berichterstattung
        # Use Windows-compatible command
        if os.name == 'nt':  # Windows
            command = f'python -m pytest "{test_dir}"'
        else:
            command = f'python -m pytest "{test_dir}"'
        
        result = code_executor.run_shell(command)

        # Parse the result to provide a structured response
        output = result.get("stdout", "")
        success = result.get("exit_code") == 0
        
        return {
            "success": success,
            "output": output,
            "details": self._parse_pytest_output(output)
        }

    def _parse_pytest_output(self, output: str) -> Dict[str, int]:
        """Parst die pytest-Ausgabe, um eine Zusammenfassung zu erhalten."""
        summary = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
        }
        summary_line = re.search(r"=+ (.*) =+", output)
        if summary_line:
            parts = summary_line.group(1).split(",")
            for part in parts:
                part = part.strip()
                match = re.match(r"(\d+) (\w+)", part)
                if match:
                    count, status = match.groups()
                    if status in summary:
                        summary[status] = int(count)
        
        summary["total"] = sum(summary.values())
        return summary

    def process_task(self, task: Task) -> Dict[str, Any]:
        """Verarbeite Test-Aufgabe"""
        if task.task_type == "run_tests":
            return self.run_test_suite(task.description, task.context)
        elif task.task_type == "generate_tests":
            return self.generate_test_suite(task.description, task.context)
        elif task.task_type == "analyze_coverage":
            return self.analyze_test_coverage(task.description, task.context)
        elif task.task_type == "create_test_data":
            return self.create_test_data(task.description, task.context)
        else:
            return self.run_generic_tests(task.description, task.context)
    
    def run_test_suite(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Führe kompletten Test-Suite aus"""
        project_name = context.get('project_name', 'myproject')
        test_dir = f"projects/{project_name}/tests"
        
        if not os.path.exists(test_dir):
            return {"error": f"Test directory not found: {test_dir}"}
        
        results = {
            "project": project_name,
            "test_dir": test_dir,
            "test_files": [],
            "summary": {},
            "details": []
        }
        
        # Finde alle Test-Dateien
        test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
        
        for test_file in test_files:
            test_path = os.path.join(test_dir, test_file)
            test_result = self._run_single_test(test_path, project_name)
            results["test_files"].append(test_result)
        
        # Zusammenfassung
        total_tests = sum(r.get("total_tests", 0) for r in results["test_files"])
        passed_tests = sum(r.get("passed", 0) for r in results["test_files"])
        failed_tests = sum(r.get("failed", 0) for r in results["test_files"])
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        return results
    
    def generate_test_suite(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generiere komplette Test-Suite"""
        project_name = context.get('project_name', 'myproject')
        target_file = context.get('target_file', 'main.py')
        
        # Lese zu testenden Code
        source_path = f"projects/{project_name}/src/{target_file}"
        source_code = file_manager.read_file(source_path)
        
        prompt = f"""
        Erstelle umfassende Tests für folgenden Python-Code:
        
        SOURCE CODE:
        {source_code}
        
        ANFORDERUNGEN: {description}
        
        Erstelle:
        1. Unit-Tests für alle Funktionen und Klassen
        2. Integration-Tests
        3. Edge-Case Tests
        4. Mock-Tests für externe Abhängigkeiten
        5. Parametrisierte Tests
        6. Fixtures für Setup/Teardown
        
        Verwende pytest und erstelle saubere, wiederverwendbare Tests.
        
        Gib die Tests im JSON-Format zurück mit:
        {{
            "test_files": [
                {{
                    "filename": "test_module.py",
                    "content": "...",
                    "description": "Beschreibung der Tests"
                }}
            ],
            "requirements": ["pytest", "pytest-mock"]
        }}
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            # Parse JSON-Antwort
            if response.strip().startswith('{'):
                test_data = json.loads(response)
            else:
                test_data = self._extract_test_code(response)
            
            # Speichere Test-Dateien
            saved_tests = []
            test_dir = f"projects/{project_name}/tests"
            
            for test_file in test_data.get('test_files', []):
                filename = test_file.get('filename', 'test_generated.py')
                content = test_file.get('content', '')
                
                test_path = f"{test_dir}/{filename}"
                success = file_manager.write_file(test_path, content)
                
                saved_tests.append({
                    "path": test_path,
                    "success": success,
                    "description": test_file.get('description', '')
                })
            
            # Installiere Test-Dependencies
            requirements = test_data.get('requirements', [])
            for req in requirements:
                code_executor.install_package(req)
            
            return {
                "tests_generated": len(saved_tests),
                "saved_tests": saved_tests,
                "requirements": requirements
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_test_coverage(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiere Test-Abdeckung"""
        project_name = context.get('project_name', 'myproject')
        source_dir = f"projects/{project_name}/src"
        test_dir = f"projects/{project_name}/tests"
        
        # Zähle Source-Dateien und Test-Dateien
        source_files = []
        test_files = []
        
        if os.path.exists(source_dir):
            source_files = [f for f in os.listdir(source_dir) if f.endswith('.py') and not f.startswith('__')]
        
        if os.path.exists(test_dir):
            test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
        
        # Analysiere Coverage pro Datei
        coverage_analysis = []
        for source_file in source_files:
            test_file = f"test_{source_file}"
            has_test = test_file in test_files
            
            # Lese Source-Datei und zähle Funktionen/Klassen
            source_path = f"{source_dir}/{source_file}"
            source_content = file_manager.read_file(source_path)
            
            functions = len(re.findall(r'def\s+(\w+)', source_content))
            classes = len(re.findall(r'class\s+(\w+)', source_content))
            
            coverage_analysis.append({
                "source_file": source_file,
                "has_test": has_test,
                "functions": functions,
                "classes": classes,
                "coverage_status": "covered" if has_test else "missing"
            })
        
        # Gesamt-Coverage
        total_files = len(source_files)
        covered_files = len([c for c in coverage_analysis if c["has_test"]])
        
        return {
            "total_source_files": total_files,
            "covered_files": covered_files,
            "coverage_percentage": (covered_files / total_files * 100) if total_files > 0 else 0,
            "analysis": coverage_analysis,
            "missing_tests": [c["source_file"] for c in coverage_analysis if not c["has_test"]]
        }
    
    def create_test_data(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Erstelle Test-Daten"""
        project_name = context.get('project_name', 'myproject')
        data_type = context.get('data_type', 'sample_data')
        
        prompt = f"""
        Erstelle Test-Daten für:
        
        BESCHREIBUNG: {description}
        DATEN-TYP: {data_type}
        
        Erstelle:
        1. JSON-Test-Daten
        2. CSV-Test-Daten (falls relevant)
        3. Mock-Daten für Tests
        4. Fixtures für pytest
        
        Die Daten sollten:
        - Realistische Beispiele enthalten
        - Edge-Cases abdecken
        - Gut strukturiert sein
        - Für Tests verwendbar sein
        
        Gib im JSON-Format zurück.
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            test_data = json.loads(response) if response.strip().startswith('{') else {"data": response}
            
            # Speichere Test-Daten
            data_dir = f"projects/{project_name}/tests/data"
            file_manager.create_directory(data_dir)
            
            saved_data = []
            if isinstance(test_data, dict):
                for key, value in test_data.items():
                    if isinstance(value, (dict, list)):
                        filename = f"{key}.json"
                        filepath = f"{data_dir}/{filename}"
                        file_manager.write_file(filepath, json.dumps(value, indent=2))
                        saved_data.append(filepath)
            
            return {
                "data_generated": len(saved_data),
                "files": saved_data,
                "data_preview": str(test_data)[:500]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def run_generic_tests(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Führe generische Tests aus"""
        project_name = context.get('project_name', 'myproject')
        
        # Führe einfache Syntax-Checks durch
        src_dir = f"projects/{project_name}/src"
        
        if not os.path.exists(src_dir):
            return {"error": f"Source directory not found: {src_dir}"}
        
        results = {
            "syntax_checks": [],
            "import_checks": [],
            "overall_status": "unknown"
        }
        
        for filename in os.listdir(src_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(src_dir, filename)
                
                # Syntax-Check
                syntax_result = self._check_syntax(filepath)
                results["syntax_checks"].append(syntax_result)
                
                # Import-Check
                import_result = self._check_imports(filepath)
                results["import_checks"].append(import_result)
        
        # Zusammenfassung
        syntax_errors = len([c for c in results["syntax_checks"] if not c["valid"]])
        import_errors = len([c for c in results["import_checks"] if not c["valid"]])
        
        if syntax_errors == 0 and import_errors == 0:
            results["overall_status"] = "passed"
        else:
            results["overall_status"] = "failed"
        
        return results
    
    def _run_single_test(self, test_path: str, project_name: str) -> Dict[str, Any]:
        """Führe einzelnen Test aus"""
        result = code_executor.execute_file(test_path, f"projects/{project_name}")
        
        # Parse pytest output
        output_lines = result.get("stdout", "").split('\n')
        total_tests = 0
        passed = 0
        failed = 0
        
        for line in output_lines:
            if "collected" in line and "items" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    total_tests = int(numbers[0])
            elif "passed" in line:
                passed = len(re.findall(r'PASSED', line))
            elif "FAILED" in line:
                failed = len(re.findall(r'FAILED', line))
        
        return {
            "test_file": os.path.basename(test_path),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success": result.get("success", False),
            "output": result
        }
    
    def _check_syntax(self, filepath: str) -> Dict[str, Any]:
        """Prüfe Python-Syntax"""
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            
            compile(code, filepath, 'exec')
            return {"file": filepath, "valid": True, "error": None}
        except SyntaxError as e:
            return {"file": filepath, "valid": False, "error": str(e)}
        except Exception as e:
            return {"file": filepath, "valid": False, "error": str(e)}
    
    def _check_imports(self, filepath: str) -> Dict[str, Any]:
        """Prüfe Imports"""
        try:
            # Führe Import-Test aus
            filename = os.path.basename(filepath)
            module_name = filename[:-3]  # Entferne .py
            
            # Wechsle in Projekt-Verzeichnis
            project_dir = os.path.dirname(os.path.dirname(filepath))
            test_cmd = [sys.executable, '-c', f'import {module_name}']
            
            result = code_executor._run_command(test_cmd, project_dir)
            
            return {
                "file": filepath,
                "valid": result.get("success", False),
                "error": result.get("stderr", "")
            }
        except Exception as e:
            return {"file": filepath, "valid": False, "error": str(e)}
    
    def _extract_test_code(self, response: str) -> Dict[str, Any]:
        """Extrahiere Test-Code aus Antwort"""
        test_files = []
        
        # Suche nach Python-Test-Code
        test_blocks = re.findall(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
        
        for i, content in enumerate(test_blocks):
            if 'test_' in content or 'assert' in content:
                test_files.append({
                    "filename": f"test_module{i+1}.py",
                    "content": content.strip(),
                    "description": f"Tests für Modul {i+1}"
                })
        
        return {"test_files": test_files}
    
    def get_test_report(self, project_name: str) -> Dict[str, Any]:
        """Hole Test-Bericht für Projekt"""
        test_dir = f"projects/{project_name}/tests"
        
        if not os.path.exists(test_dir):
            return {"error": "No tests found"}
        
        # Führe alle Tests aus
        return self.run_test_suite("All tests", {"project_name": project_name})
    
    def fix_failing_tests(self, test_results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Behebe fehlgeschlagene Tests"""
        project_name = context.get('project_name', 'myproject')
        
        failed_tests = [t for t in test_results.get("test_files", []) if t.get("failed", 0) > 0]
        
        if not failed_tests:
            return {"message": "No failing tests to fix"}
        
        fixes = []
        for test in failed_tests:
            # Analysiere Fehler und erstelle Fix-Vorschläge
            fix_prompt = f"""
            Fix folgenden fehlgeschlagenen Test:
            
            TEST FILE: {test["test_file"]}
            OUTPUT: {json.dumps(test.get("output", {}), indent=2)}
            
            Analysiere den Fehler und erstelle:
            1. Korrekturen für den Test-Code
            2. Falls nötig, Korrekturen für die zu testende Funktionalität
            3. Erklärung des Problems
            
            Gib die Fixes im JSON-Format zurück.
            """
            
            fix_response = self.get_llm_response(fix_prompt)
            fixes.append({
                "test_file": test["test_file"],
                "fix_suggestions": fix_response
            })
        
        return {
            "failed_tests": len(failed_tests),
            "fixes": fixes
        }