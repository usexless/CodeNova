"""
Core Tools für das AI-Programmier-Framework
Enthält alle erweiterten Datei- und Codeverarbeitungs-Tools
"""

import os
import re
import subprocess
import json
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import ast


class CoreTools:
    """Sammlung von Core Development Tools"""
    
    def __init__(self):
        self.state_dir = Path("/state")
        self.state_dir.mkdir(exist_ok=True)
        self.trace_log = self.state_dir / "trace.log"
    
    def _log_action(self, tool: str, args: Dict[str, Any], result: Any = None):
        """Logge jede Aktion in die trace.log"""
        entry = {
            "tool": tool,
            "args": args,
            "result": str(result) if result else None,
            "timestamp": str(datetime.datetime.now())
        }
        
        with open(self.trace_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def read_file(self, path: str) -> str:
        """Lies den Inhalt einer Datei"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._log_action("read_file", {"path": path}, "success")
            return content
        except Exception as e:
            self._log_action("read_file", {"path": path}, f"error: {str(e)}")
            raise e
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Überschreibe eine Datei mit neuem Inhalt"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_action("write_file", {"path": path}, f"written {len(content)} chars")
            return {"success": True, "path": path, "size": len(content)}
        except Exception as e:
            self._log_action("write_file", {"path": path}, f"error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def edit_file_line(self, path: str, line: int, new_line: str) -> Dict[str, Any]:
        """Ersetze eine spezifische Zeile in einer Datei"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if line < 1 or line > len(lines):
                raise ValueError(f"Line {line} out of range (1-{len(lines)})")
            
            old_line = lines[line-1]
            lines[line-1] = new_line + '\n' if not new_line.endswith('\n') else new_line
            
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self._log_action("edit_file_line", {"path": path, "line": line}, "success")
            return {
                "success": True,
                "path": path,
                "line": line,
                "old_line": old_line.strip(),
                "new_line": new_line
            }
        except Exception as e:
            self._log_action("edit_file_line", {"path": path, "line": line}, f"error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """Hänge Inhalt an eine Datei an"""
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            self._log_action("append_file", {"path": path}, f"appended {len(content)} chars")
            return {"success": True, "path": path, "appended": len(content)}
        except Exception as e:
            self._log_action("append_file", {"path": path}, f"error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_code(self, pattern: str, path: str = None) -> List[Dict[str, Any]]:
        """Grep-ähnliche Suche mit Regex-Pattern"""
        try:
            results = []
            search_path = Path(path) if path else Path(".")
            
            for file_path in search_path.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            results.append({
                                "file": str(file_path),
                                "line": line_num,
                                "content": line.strip()
                            })
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            self._log_action("search_code", {"pattern": pattern, "path": str(search_path)}, f"found {len(results)} matches")
            return results
        except Exception as e:
            self._log_action("search_code", {"pattern": pattern, "path": str(search_path)}, f"error: {str(e)}")
            return []
    
    def run_cmd(self, command: str, timeout: int = 120) -> Dict[str, Any]:
        """Führe Shell-Kommando aus (Windows PowerShell)"""
        try:
            # Ensure we're using PowerShell on Windows
            if os.name == 'nt':  # Windows
                # Use PowerShell for Windows commands
                ps_command = f'powershell.exe -Command "{command}"'
                process = subprocess.run(
                    ps_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                # Fallback for other systems
                process = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            result = {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "success": process.returncode == 0
            }
            
            self._log_action("run_cmd", {"command": command}, f"exit_code: {process.returncode}")
            return result
        except subprocess.TimeoutExpired:
            self._log_action("run_cmd", {"command": command}, "timeout")
            return {"success": False, "error": "Command timed out", "exit_code": -1}
        except Exception as e:
            self._log_action("run_cmd", {"command": command}, f"error: {str(e)}")
            return {"success": False, "error": str(e), "exit_code": -1}
    
    def run_py(self, code: str) -> Dict[str, Any]:
        """Führe Python-Code im REPL aus"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = self.run_cmd(f"python {temp_file}")
            
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass
            
            self._log_action("run_py", {"code_length": len(code)}, f"success: {result['success']}")
            return result
        except Exception as e:
            self._log_action("run_py", {"code_length": len(code)}, f"error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_test(self, name: str, code: str) -> Dict[str, Any]:
        """Erstelle eine Unit-Testdatei"""
        try:
            test_dir = Path("tests")
            test_dir.mkdir(exist_ok=True)
            
            test_file = test_dir / f"test_{name}.py"
            
            # Basic test template
            test_content = f'''"""
Test für {name}
"""
import pytest
from unittest.mock import Mock, patch

{code}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
            
            return self.write_file(str(test_file), test_content)
        except Exception as e:
            self._log_action("create_test", {"name": name}, f"error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def run_tests(self) -> Dict[str, Any]:
        """Führe alle Tests mit pytest aus"""
        return self.run_cmd("pytest -q")


# Import für die Datei
import datetime


# Tool-Registry für JSON-RPC
class ToolRegistry:
    """Registry für alle verfügbaren Tools"""
    
    def __init__(self):
        self.core_tools = CoreTools()
        self.tools = {
            "read_file": self.core_tools.read_file,
            "write_file": self.core_tools.write_file,
            "edit_file_line": self.core_tools.edit_file_line,
            "append_file": self.core_tools.append_file,
            "search_code": self.core_tools.search_code,
            "run_cmd": self.core_tools.run_cmd,
            "run_py": self.core_tools.run_py,
            "create_test": self.core_tools.create_test,
            "run_tests": self.core_tools.run_tests,
        }
    
    def execute(self, tool_name: str, **kwargs) -> Any:
        """Führe ein Tool mit gegebenen Argumenten aus"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        return self.tools[tool_name](**kwargs)


# Global instance
registry = ToolRegistry()