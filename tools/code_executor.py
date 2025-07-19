import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
import signal

class CodeExecutor:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.supported_languages = {
            'python': {
                'extension': '.py',
                'command': [sys.executable],
                'test_command': [sys.executable, '-m', 'pytest']
            },
            'javascript': {
                'extension': '.js',
                'command': ['node'],
                'test_command': ['npm', 'test']
            },
            'java': {
                'extension': '.java',
                'command': ['java'],
                'compile_command': ['javac']
            },
            'cpp': {
                'extension': '.cpp',
                'command': ['./compiled'],
                'compile_command': ['g++', '-o', 'compiled']
            }
        }
    
    def detect_language(self, filename: str) -> str:
        """Erkenne Sprache anhand Dateiendung"""
        extension = Path(filename).suffix.lower()
        for lang, config in self.supported_languages.items():
            if config['extension'] == extension:
                return lang
        return 'python'  # Default
    
    def execute_python(self, code: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Führe Python-Code aus"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            cmd = [sys.executable, temp_file]
            result = self._run_command(cmd, working_dir)
            
            # Cleanup
            os.unlink(temp_file)
            return result
            
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}
    
    def execute_file(self, filepath: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Führe Datei aus"""
        if not os.path.exists(filepath):
            return {"success": False, "stdout": "", "stderr": f"Datei nicht gefunden: {filepath}", "return_code": 1}
        
        language = self.detect_language(filepath)
        
        if language == 'python':
            cmd = [sys.executable, filepath]
        elif language == 'javascript':
            cmd = ['node', filepath]
        else:
            return {"success": False, "stdout": "", "stderr": f"Sprache {language} nicht unterstützt", "return_code": 1}
        
        return self._run_command(cmd, working_dir)
    
    def run_shell(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Führt einen beliebigen Shell-Befehl aus (Windows PowerShell)."""
        # Ensure we're using PowerShell on Windows
        if os.name == 'nt':  # Windows
            # Use PowerShell for Windows commands
            ps_command = f'powershell.exe -Command "{command}"'
            cmd_parts = [ps_command]
        else:
            # Fallback for other systems
            cmd_parts = command.split()
        
        return self._run_command(cmd_parts, working_dir)

    def _run_command(self, cmd: List[str], working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Führe System-Command aus"""
        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": f"Timeout nach {self.timeout}s", "return_code": 124}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}
    
    def run_tests(self, test_dir: str) -> Dict[str, Any]:
        """Führe Tests aus"""
        if not os.path.exists(test_dir):
            return {"success": False, "stdout": "", "stderr": f"Test-Verzeichnis nicht gefunden: {test_dir}", "return_code": 1}
        
        # Versuche pytest
        cmd = [sys.executable, '-m', 'pytest', test_dir, '-v']
        result = self._run_command(cmd)
        
        if result['return_code'] == 2:  # pytest nicht gefunden
            # Fallback zu unittest
            cmd = [sys.executable, '-m', 'unittest', 'discover', test_dir, '-v']
            result = self._run_command(cmd)
        
        return result
    
    def install_package(self, package: str) -> Dict[str, Any]:
        """Installiere Python-Paket"""
        cmd = [sys.executable, '-m', 'pip', 'install', package]
        return self._run_command(cmd)
    
    def check_dependencies(self, requirements_file: str) -> Dict[str, Any]:
        """Prüfe und installiere Dependencies"""
        if not os.path.exists(requirements_file):
            return {"success": False, "stdout": "", "stderr": f"requirements.txt nicht gefunden", "return_code": 1}
        
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', requirements_file]
        return self._run_command(cmd)
    
    def get_python_info(self) -> Dict[str, Any]:
        """Hole Python-Informationen"""
        try:
            version = sys.version
            site_packages = [p for p in sys.path if 'site-packages' in p]
            
            cmd = [sys.executable, '-m', 'pip', 'list', '--format=json']
            result = self._run_command(cmd)
            
            packages = []
            if result['success']:
                try:
                    packages = json.loads(result['stdout'])
                except:
                    packages = []
            
            return {
                "python_version": version,
                "executable": sys.executable,
                "site_packages": site_packages,
                "installed_packages": packages
            }
        except Exception as e:
            return {"error": str(e)}
    
    def execute_code_block(self, code: str, language: str = 'python', working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Führe Code-Block aus (für Markdown)"""
        if language == 'python':
            return self.execute_python(code, working_dir)
        else:
            return {"success": False, "stdout": "", "stderr": f"Sprache {language} nicht unterstützt", "return_code": 1}
    
    def create_and_run_script(self, filename: str, content: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Erstelle und führe Skript aus"""
        try:
            current_dir = Path(working_dir or '.')
            filepath = current_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return self.execute_file(str(filepath), working_dir)
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}

# Globaler CodeExecutor
code_executor = CodeExecutor()