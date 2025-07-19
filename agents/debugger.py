import os
import re
import json
import subprocess
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from agents.base_agent import BaseAgent, Task
from tools.file_tools import file_manager
from tools.code_executor import code_executor
from llm import llm_manager

console = Console()

class Debugger(BaseAgent):
    def __init__(self):
        super().__init__("Debugger", "Error Analysis and Fix Generation")
        self.debug_history = []
        
    def system_prompt(self) -> str:
        return """You are an expert debugger and problem solver on Windows 11 with PowerShell. You solve debugging problems completely and autonomously.

KERNPRINZIPIEN:
1. **AUTONOME PROBLEMLÖSUNG**: Löse Debugging-Probleme vollständig und selbstständig.
2. **GRÜNDLICHE ANALYSE**: Analysiere Fehler THOROUGHLY - verstehe Root-Causes, nicht nur Symptome.
3. **VOLLSTÄNDIGE LÖSUNG**: Behebe alle Probleme komplett, nicht nur teilweise.
4. **PROAKTIVE FEHLERBEHEBUNG**: Identifiziere und behebe Probleme automatisch.

Your role is to:
1. Analyze error messages and stack traces THOROUGHLY
2. Identify root causes of bugs and issues
3. Generate targeted fixes and improvements
4. Provide explanations for fixes
5. Prevent similar issues in the future
6. Create regression tests for fixes
7. **AUTONOMOUSLY IMPLEMENT FIXES** - don't just suggest solutions, implement them

ARBEITSWEISE:
1. **Analysiere Fehler gründlich** - verstehe Root-Causes und Kontext
2. **Implementiere Lösungen autonom** - behebe Probleme direkt
3. **Validiere Fixes** - stelle sicher, dass Probleme behoben sind
4. **Verhindere Regressionen** - erstelle Tests für zukünftige Prävention
5. **Optimiere Code-Qualität** - verbessere die Gesamtqualität

Always provide clear, actionable fixes with explanations. Focus on root causes, not symptoms.
WINDOWS COMPATIBILITY: You work in a Windows PowerShell environment. Use only Windows-compatible commands and paths.

Sei autonom, gründlich und löse Debugging-Probleme komplett!
"""
    
    def lint_and_fix_file(self, file_path: str) -> bool:
        """
        Führt einen Linter für die angegebene Datei aus und versucht, gefundene Probleme zu beheben.
        Gibt True zurück, wenn die Datei sauber ist oder erfolgreich repariert wurde.
        """
        import os
        import subprocess
        import tempfile
        from pathlib import Path
        
        language = file_path.split('.')[-1].lower()
        console.print(f"    └── [yellow]Linter-Prüfung für {language.upper()}...[/yellow]", end="")
        
        try:
            if language == "py":
                return self._lint_python_file(file_path)
            elif language in ["js", "ts", "jsx", "tsx"]:
                return self._lint_javascript_file(file_path)
            elif language in ["html", "htm"]:
                return self._lint_html_file(file_path)
            elif language == "css":
                return self._lint_css_file(file_path)
            elif language in ["json", "yaml", "yml"]:
                return self._lint_config_file(file_path)
            else:
                console.print(f"\r    └── [blue]Linter-Prüfung für {language.upper()}... Übersprungen (nicht unterstützt)[/blue]")
                return True
                
        except Exception as e:
            console.print(f"\r    └── [red]Linter-Prüfung für {language.upper()}... FEHLER: {str(e)}[/red]")
            return False

    def _lint_python_file(self, file_path: str) -> bool:
        """Lintet eine Python-Datei mit flake8 und versucht Auto-Fixes."""
        try:
            # Prüfe ob flake8 installiert ist
            result = subprocess.run(["flake8", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"\r    └── [yellow]Linter-Prüfung für PYTHON... flake8 nicht installiert, überspringe[/yellow]")
                return True
            
            # Führe flake8 aus
            result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"\r    └── [green]Linter-Prüfung für PYTHON... OK[/green]")
                return True
            
            # Es gibt Linting-Fehler, versuche sie zu beheben
            lint_errors = result.stdout
            console.print(f"\r    └── [yellow]Linter-Prüfung für PYTHON... {len(lint_errors.splitlines())} Probleme gefunden, versuche zu beheben...[/yellow]")
            
            # Lese den aktuellen Code
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Versuche Auto-Fixes mit autopep8
            try:
                result = subprocess.run(["autopep8", "--in-place", "--aggressive", "--aggressive", file_path], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    console.print(f"\r    └── [green]Linter-Prüfung für PYTHON... Auto-Fixes angewendet[/green]")
                    return True
            except FileNotFoundError:
                pass
            
            # Wenn autopep8 nicht verfügbar, versuche manuelle Fixes
            fixed_code = self._fix_python_lint_errors(original_code, lint_errors)
            if fixed_code != original_code:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                console.print(f"\r    └── [green]Linter-Prüfung für PYTHON... Manuelle Fixes angewendet[/green]")
                return True
            
            console.print(f"\r    └── [red]Linter-Prüfung für PYTHON... Konnte Probleme nicht beheben[/red]")
            return False
            
        except Exception as e:
            console.print(f"\r    └── [red]Linter-Prüfung für PYTHON... FEHLER: {str(e)}[/red]")
            return False

    def _lint_javascript_file(self, file_path: str) -> bool:
        """Lintet eine JavaScript/TypeScript-Datei mit ESLint."""
        try:
            # Prüfe ob ESLint installiert ist
            result = subprocess.run(["npx", "eslint", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"\r    └── [yellow]Linter-Prüfung für JAVASCRIPT... ESLint nicht installiert, überspringe[/yellow]")
                return True
            
            # Führe ESLint aus
            result = subprocess.run(["npx", "eslint", file_path, "--format=compact"], capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"\r    └── [green]Linter-Prüfung für JAVASCRIPT... OK[/green]")
                return True
            
            # Versuche Auto-Fixes
            result = subprocess.run(["npx", "eslint", file_path, "--fix"], capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"\r    └── [green]Linter-Prüfung für JAVASCRIPT... Auto-Fixes angewendet[/green]")
                return True
            
            console.print(f"\r    └── [red]Linter-Prüfung für JAVASCRIPT... Probleme gefunden, konnte nicht beheben[/red]")
            return False
            
        except Exception as e:
            console.print(f"\r    └── [red]Linter-Prüfung für JAVASCRIPT... FEHLER: {str(e)}[/red]")
            return False

    def _lint_html_file(self, file_path: str) -> bool:
        """Lintet eine HTML-Datei."""
        try:
            # Einfache HTML-Validierung mit Python
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prüfe auf grundlegende HTML-Probleme
            issues = []
            if not content.strip().startswith('<!DOCTYPE html>') and not content.strip().startswith('<html'):
                issues.append("Fehlende DOCTYPE oder HTML-Tag")
            
            if content.count('<html') != content.count('</html>'):
                issues.append("Ungleiche Anzahl von HTML-Tags")
            
            if content.count('<head') != content.count('</head>'):
                issues.append("Ungleiche Anzahl von HEAD-Tags")
            
            if content.count('<body') != content.count('</body>'):
                issues.append("Ungleiche Anzahl von BODY-Tags")
            
            if issues:
                console.print(f"\r    └── [yellow]Linter-Prüfung für HTML... {len(issues)} Probleme gefunden[/yellow]")
                return False
            
            console.print(f"\r    └── [green]Linter-Prüfung für HTML... OK[/green]")
            return True
            
        except Exception as e:
            console.print(f"\r    └── [red]Linter-Prüfung für HTML... FEHLER: {str(e)}[/red]")
            return False

    def _lint_css_file(self, file_path: str) -> bool:
        """Lintet eine CSS-Datei."""
        try:
            # Einfache CSS-Validierung
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prüfe auf grundlegende CSS-Probleme
            issues = []
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped and not stripped.startswith('/*') and not stripped.startswith('*/'):
                    if '{' in stripped and '}' not in stripped:
                        # Prüfe ob die schließende Klammer in den nächsten Zeilen ist
                        found_closing = False
                        for j in range(i, min(i + 10, len(lines))):
                            if '}' in lines[j]:
                                found_closing = True
                                break
                        if not found_closing:
                            issues.append(f"Zeile {i}: Möglicherweise fehlende schließende Klammer")
            
            if issues:
                console.print(f"\r    └── [yellow]Linter-Prüfung für CSS... {len(issues)} Probleme gefunden[/yellow]")
                return False
            
            console.print(f"\r    └── [green]Linter-Prüfung für CSS... OK[/green]")
            return True
            
        except Exception as e:
            console.print(f"\r    └── [red]Linter-Prüfung für CSS... FEHLER: {str(e)}[/red]")
            return False

    def _lint_config_file(self, file_path: str) -> bool:
        """Lintet eine Konfigurationsdatei (JSON, YAML)."""
        try:
            language = file_path.split('.')[-1].lower()
            
            if language == "json":
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validiert JSON-Syntax
                console.print(f"\r    └── [green]Linter-Prüfung für JSON... OK[/green]")
                return True
                
            elif language in ["yaml", "yml"]:
                import yaml
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)  # Validiert YAML-Syntax
                console.print(f"\r    └── [green]Linter-Prüfung für YAML... OK[/green]")
                return True
            
            console.print(f"\r    └── [blue]Linter-Prüfung für {language.upper()}... Übersprungen[/blue]")
            return True
            
        except Exception as e:
            console.print(f"\r    └── [red]Linter-Prüfung für {language.upper()}... FEHLER: {str(e)}[/red]")
            return False

    def _fix_python_lint_errors(self, code: str, lint_errors: str) -> str:
        """Versucht, Python Linting-Fehler automatisch zu beheben."""
        try:
            # Parse Linting-Fehler
            lines = code.split('\n')
            fixes = []
            
            for error_line in lint_errors.split('\n'):
                if not error_line.strip():
                    continue
                    
                # Parse flake8 Error: file:line:col:code message
                parts = error_line.split(':')
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1]) - 1  # 0-basiert
                        error_code = parts[3].strip()
                        message = ':'.join(parts[4:]).strip()
                        
                        if line_num < len(lines):
                            original_line = lines[line_num]
                            fixed_line = self._fix_python_line(original_line, error_code, message)
                            if fixed_line != original_line:
                                fixes.append((line_num, fixed_line))
                    except (ValueError, IndexError):
                        continue
            
            # Wende Fixes an
            for line_num, fixed_line in fixes:
                if line_num < len(lines):
                    lines[line_num] = fixed_line
            
            return '\n'.join(lines)
            
        except Exception:
            return code  # Bei Fehlern gib Original-Code zurück

    def _fix_python_line(self, line: str, error_code: str, message: str) -> str:
        """Behebt spezifische Python Linting-Fehler in einer Zeile."""
        # E101: indentation contains mixed spaces and tabs
        if error_code == "E101":
            return line.expandtabs(4)
        
        # E201: whitespace after '('
        elif error_code == "E201":
            return line.replace('( ', '(')
        
        # E202: whitespace before ')'
        elif error_code == "E202":
            return line.replace(' )', ')')
        
        # E203: whitespace before ':'
        elif error_code == "E203":
            return line.replace(' :', ':')
        
        # E211: whitespace before '('
        elif error_code == "E211":
            return line.replace(' (', '(')
        
        # E225: missing whitespace around operator
        elif error_code == "E225":
            # Einfache Operator-Fixes
            operators = ['+', '-', '*', '/', '=', '==', '!=', '<=', '>=', '<', '>']
            for op in operators:
                if op in line and f' {op} ' not in line and f'{op} ' not in line and f' {op}' not in line:
                    # Versuche intelligente Fixes
                    if op in ['+', '-', '*', '/']:
                        line = line.replace(f'{op}', f' {op} ')
                    elif op in ['=', '==', '!=']:
                        line = line.replace(f'{op}', f' {op} ')
        
        # E302: expected 2 blank lines, found 0
        elif error_code == "E302":
            # Wird in _fix_python_lint_errors behandelt
            pass
        
        # E501: line too long
        elif error_code == "E501":
            # Einfache Zeilenumbruch-Logik
            if len(line) > 79 and ',' in line:
                # Versuche nach Kommas umzubrechen
                parts = line.split(',')
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    new_indent = ' ' * (indent + 4)
                    line = parts[0] + ',\n' + new_indent + ',\n'.join(parts[1:])
        
        return line
    
    def debug_project(self, project_info: Dict[str, Any], test_results: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        Versucht, ein Projekt durch Analysieren von fehlgeschlagenen Tests und Anwenden von Fixes zu debuggen.
        Gibt True zurück, wenn alle Tests nach den Fixes erfolgreich sind.
        """
        project_path = project_info.get("path")
        if not project_path:
            return False

        for i in range(max_retries):
            console.print(f"🐞 Debugging-Versuch {i + 1}/{max_retries}...")
            
            output = test_results.get("output", "")
            if not output:
                return False # Kann ohne Test-Output nicht debuggen

            # Finde die erste fehlerhafte Datei (vereinfachte Annahme)
            failed_file_match = re.search(r"tests/test_(\w+)\.py", output)
            if not failed_file_match:
                console.print("[red]Konnte keine fehlerhafte Testdatei aus der Ausgabe extrahieren.[/red]")
                return False
            
            target_module_name = failed_file_match.group(1)
            source_file_path = os.path.join(project_path, "src", f"{target_module_name}.py")
            
            if not os.path.exists(source_file_path):
                 console.print(f"[red]Quelldatei '{source_file_path}' für fehlgeschlagenen Test nicht gefunden.[/red]")
                 return False

            # Generiere einen Fix
            fix_result = self.debug_error(
                error_description=output,
                context={
                    "project_name": project_info.get("name"),
                    "target_file": f"src/{target_module_name}.py",
                    "source_code": file_manager.read_file(source_file_path)
                }
            )

            # Wende den Fix an
            if fix_result.get("fixed_code"):
                file_manager.write_file(source_file_path, fix_result["fixed_code"])
                console.print(f"[yellow]Fix für '{source_file_path}' angewendet.[/yellow]")
                
                # Führe Tests erneut aus
                console.print("[yellow]Führe Tests nach dem Fix erneut aus...[/yellow]")
                from agents.test_runner import TestRunner # Lokaler Import, um zirkuläre Abhängigkeiten zu vermeiden
                new_test_results = TestRunner().run_tests(project_path)

                if new_test_results.get("success"):
                    return True # Erfolgreich!
                
                test_results = new_test_results # Bereite für nächsten Versuch vor
            else:
                console.print("[red]Konnte keinen Code-Fix generieren.[/red]")
                return False

        return False # Maximale Versuche erreicht

    def process_task(self, task: Task) -> Dict[str, Any]:
        """Verarbeite Debugging-Aufgabe"""
        if task.task_type == "debug_error":
            return self.debug_error(task.description, task.context)
        elif task.task_type == "fix_runtime_error":
            return self.fix_runtime_error(task.description, task.context)
        elif task.task_type == "fix_logic_error":
            return self.fix_logic_error(task.description, task.context)
        elif task.task_type == "performance_issue":
            return self.fix_performance_issue(task.description, task.context)
        else:
            return self.general_debugging(task.description, task.context)
    
    def debug_error(self, error_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Debug spezifischen Fehler"""
        project_name = context.get('project_name', 'myproject')
        error_type = context.get('error_type', 'runtime')
        
        # Lese relevante Dateien
        target_file = context.get('target_file', 'main.py')
        file_path = f"projects/{project_name}/src/{target_file}"
        source_code = file_manager.read_file(file_path)
        
        prompt = f"""
        Analysiere folgenden Fehler und erstelle eine detaillierte Lösung:
        
        FEHLER: {error_description}
        FEHLER-TYP: {error_type}
        DATEI: {target_file}
        
        SOURCE CODE:
        {source_code}
        
        Erstelle:
        1. Genauen Fehler-Report
        2. Root-Cause-Analyse
        3. Schritt-für-Schritt-Fix
        4. Korrekturen für den Source-Code
        5. Regression-Tests
        6. Erklärung der Lösung
        
        Gib alles im strukturierten JSON-Format zurück.
        """
        
        response = self.get_llm_response(prompt)
        
        try:
            debug_result = self._parse_debug_response(response)
            
            # Speichere Debug-Resultat
            self.debug_history.append({
                "error": error_description,
                "fix": debug_result,
                "timestamp": "now"
            })
            
            # Wende Fix an
            if "code_fixes" in debug_result:
                for fix in debug_result["code_fixes"]:
                    file_manager.write_file(
                        f"projects/{project_name}/src/{fix['file']}",
                        fix["fixed_code"]
                    )
            
            return debug_result
            
        except Exception as e:
            return {"error": str(e), "raw_response": response}
    
    def fix_runtime_error(self, error_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Behebe Laufzeitfehler"""
        project_name = context.get('project_name', 'myproject')
        
        # Führe Code aus und fange Fehler
        target_file = context.get('target_file', 'main.py')
        file_path = f"projects/{project_name}/src/{target_file}"
        
        execution_result = code_executor.execute_file(file_path, f"projects/{project_name}")
        
        if execution_result.get("success"):
            return {"status": "no_error", "message": "Code executed successfully"}
        
        error_output = execution_result.get("stderr", "")
        
        prompt = f"""
        Behebe folgenden Laufzeitfehler:
        
        FEHLER:
        {error_output}
        
        DATEI: {target_file}
        
        Analysiere:
        1. Fehler-Typ (SyntaxError, NameError, ImportError, etc.)
        2. Zeilennummer und Kontext
        3. Mögliche Ursachen
        4. Konkrete Lösung
        5. Code-Korrektur
        
        Erstelle einen vollständigen Fix.
        """
        
        response = self.get_llm_response(prompt)
        
        # Extrahiere und wende Fix an
        fix_result = self._extract_fix_from_response(response, target_file)
        
        if fix_result.get("fixed_code"):
            file_manager.write_file(file_path, fix_result["fixed_code"])
        
        return fix_result
    
    def fix_logic_error(self, error_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Behebe Logikfehler"""
        project_name = context.get('project_name', 'myproject')
        target_file = context.get('target_file', 'main.py')
        
        # Lese Source-Code
        file_path = f"projects/{project_name}/src/{target_file}"
        source_code = file_manager.read_file(file_path)
        
        # Erstelle Test-Case zur Reproduktion
        test_input = context.get('test_input', '')
        expected_output = context.get('expected_output', '')
        actual_output = context.get('actual_output', '')
        
        prompt = f"""
        Behebe Logikfehler im Code:
        
        PROBLEM: {error_description}
        
        SOURCE CODE:
        {source_code}
        
        TEST INPUT: {test_input}
        EXPECTED OUTPUT: {expected_output}
        ACTUAL OUTPUT: {actual_output}
        
        Analysiere:
        1. Was ist das erwartete Verhalten?
        2. Was ist das tatsächliche Verhalten?
        3. Wo liegt der Denkfehler?
        4. Wie kann man es korrigieren?
        5. Welche Tests würden das Problem abdecken?
        
        Erstelle korrigierten Code und Tests.
        """
        
        response = self.get_llm_response(prompt)
        
        fix_result = self._parse_logic_fix_response(response)
        
        # Wende Fix an
        if fix_result.get("fixed_code"):
            file_manager.write_file(file_path, fix_result["fixed_code"])
        
        # Erstelle Regression-Test
        if fix_result.get("regression_test"):
            test_path = f"projects/{project_name}/tests/test_{target_file}"
            file_manager.write_file(test_path, fix_result["regression_test"])
        
        return fix_result
    
    def fix_performance_issue(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Behebe Performance-Probleme"""
        project_name = context.get('project_name', 'myproject')
        target_file = context.get('target_file', 'main.py')
        
        # Lese Source-Code
        file_path = f"projects/{project_name}/src/{target_file}"
        source_code = file_manager.read_file(file_path)
        
        prompt = f"""
        Optimiere folgenden Code für bessere Performance:
        
        PROBLEM: {description}
        
        SOURCE CODE:
        {source_code}
        
        Analysiere:
        1. Performance-Engpässe identifizieren
        2. Algorithmen optimieren
        3. Datenstrukturen verbessern
        4. Redundante Operationen entfernen
        5. Caching/Mehrfachberechnung vermeiden
        6. Zeit- und Speicherkomplexität verbessern
        
        Erstelle optimierten Code mit Benchmarks.
        """
        
        response = self.get_llm_response(prompt)
        
        optimization_result = self._parse_optimization_response(response)
        
        # Wende Optimierung an
        if optimization_result.get("optimized_code"):
            file_manager.write_file(file_path, optimization_result["optimized_code"])
        
        return optimization_result
    
    def general_debugging(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Allgemeines Debugging"""
        project_name = context.get('project_name', 'myproject')
        
        prompt = f"""
        Debug folgendes Problem:
        
        BESCHREIBUNG: {description}
        KONTEXT: {json.dumps(context, indent=2)}
        
        Erstelle:
        1. Fehler-Analyse
        2. Mögliche Ursachen
        3. Systematisches Debugging-Vorgehen
        4. Konkrete Lösungsvorschläge
        5. Vorbeugende Maßnahmen
        """
        
        return {"analysis": self.get_llm_response(prompt)}
    
    def analyze_stack_trace(self, stack_trace: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiere Stack-Trace"""
        project_name = context.get('project_name', 'myproject')
        
        prompt = f"""
        Analysiere folgenden Stack-Trace:
        
        STACK TRACE:
        {stack_trace}
        
        Erstelle:
        1. Fehler-Typ und Ort
        2. Call-Stack-Analyse
        3. Wahrscheinliche Ursache
        4. Lösungsansatz
        5. Code-Fix
        """
        
        return {"analysis": self.get_llm_response(prompt)}
    
    def create_debug_report(self, project_name: str) -> Dict[str, Any]:
        """Erstelle Debug-Bericht"""
        # Sammle alle bekannten Fehler und Fixes
        
        report = {
            "project": project_name,
            "total_issues": len(self.debug_history),
            "recent_fixes": self.debug_history[-5:],  # Letzte 5 Fixes
            "common_patterns": self._identify_error_patterns()
        }
        
        return report
    
    def _parse_debug_response(self, response: str) -> Dict[str, Any]:
        """Parse Debug-Antwort"""
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # Extrahiere strukturiert aus Text
                return {
                    "error_analysis": response,
                    "root_cause": "Analyse erforderlich",
                    "fix_suggestions": [response]
                }
        except:
            return {
                "error_analysis": response,
                "raw_response": response
            }
    
    def _extract_fix_from_response(self, response: str, filename: str) -> Dict[str, Any]:
        """Extrahiere Fix aus Antwort"""
        # Suche nach Code-Blöcken
        code_blocks = re.findall(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
        
        if code_blocks:
            fixed_code = code_blocks[0].strip()
            return {
                "file": filename,
                "fixed_code": fixed_code,
                "fix_type": "code_replacement"
            }
        
        return {"fix_type": "analysis_only", "content": response}
    
    def _parse_logic_fix_response(self, response: str) -> Dict[str, Any]:
        """Parse Logik-Fix-Antwort"""
        code_blocks = re.findall(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
        
        fixed_code = code_blocks[0] if code_blocks else ""
        
        test_blocks = re.findall(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
        regression_test = test_blocks[1] if len(test_blocks) > 1 else ""
        
        return {
            "fixed_code": fixed_code,
            "regression_test": regression_test,
            "explanation": response
        }
    
    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """Parse Optimierungs-Antwort"""
        code_blocks = re.findall(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
        
        optimized_code = code_blocks[0] if code_blocks else ""
        
        return {
            "optimized_code": optimized_code,
            "explanation": response,
            "benchmarks": "Siehe Kommentare im Code"
        }
    
    def _identify_error_patterns(self) -> List[Dict[str, Any]]:
        """Identifiziere wiederkehrende Fehler-Muster"""
        patterns = []
        
        # Analysiere Debug-History nach Mustern
        for debug_item in self.debug_history:
            error = debug_item.get("error", "")
            
            # Klassifiziere Fehler
            if "SyntaxError" in error:
                patterns.append({"type": "syntax", "count": 1})
            elif "NameError" in error:
                patterns.append({"type": "undefined_variable", "count": 1})
            elif "ImportError" in error:
                patterns.append({"type": "import", "count": 1})
            elif "TypeError" in error:
                patterns.append({"type": "type_mismatch", "count": 1})
        
        return patterns
    
    def auto_fix_project(self, project_name: str) -> Dict[str, Any]:
        """Automatisches Fixen von Problemen"""
        results = {
            "syntax_issues": [],
            "runtime_issues": [],
            "fixes_applied": [],
            "summary": {}
        }
        
        # Prüfe Syntax aller Dateien
        src_dir = f"projects/{project_name}/src"
        if os.path.exists(src_dir):
            for filename in os.listdir(src_dir):
                if filename.endswith('.py'):
                    filepath = os.path.join(src_dir, filename)
                    syntax_check = self._check_syntax(filepath)
                    results["syntax_issues"].append(syntax_check)
                    
                    if not syntax_check["valid"]:
                        # Versuche automatischen Fix
                        fix = self.fix_runtime_error(
                            f"SyntaxError in {filename}",
                            {"project_name": project_name, "target_file": filename}
                        )
                        results["fixes_applied"].append(fix)
        
        # Führe Runtime-Tests durch
        runtime_check = self._check_runtime(project_name)
        results["runtime_issues"] = runtime_check
        
        results["summary"] = {
            "total_issues": len(results["syntax_issues"]) + len(results["runtime_issues"]),
            "fixed_issues": len(results["fixes_applied"]),
            "remaining_issues": len([i for i in results["syntax_issues"] if not i["valid"]])
        }
        
        return results
    
    def _check_syntax(self, filepath: str) -> Dict[str, Any]:
        """Prüfe Syntax"""
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            compile(code, filepath, 'exec')
            return {"file": filepath, "valid": True, "error": None}
        except SyntaxError as e:
            return {"file": filepath, "valid": False, "error": str(e)}
    
    def _check_runtime(self, project_name: str) -> List[Dict[str, Any]]:
        """Prüfe Runtime-Fehler"""
        src_dir = f"projects/{project_name}/src"
        issues = []
        
        for filename in os.listdir(src_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(src_dir, filename)
                result = code_executor.execute_file(filepath, f"projects/{project_name}")
                
                if not result.get("success"):
                    issues.append({
                        "file": filename,
                        "error": result.get("stderr", ""),
                        "type": "runtime"
                    })
        
        return issues