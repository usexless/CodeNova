"""
Tool Router für autonome Agenten-Ausführung
Verwaltet Tool-Registrierung und Hook-Engine
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Callable
import traceback
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.core_tools import registry


class ToolRouter:
    """Router für Tool-Ausführung mit Hook-Unterstützung"""
    
    def __init__(self):
        self.registry = registry
        self.hooks = {}
        self.load_hooks()
        self.state_dir = Path("/state")
        self.state_dir.mkdir(exist_ok=True)
    
    def load_hooks(self):
        """Lade Hook-Konfiguration aus .agent_hooks.json"""
        hooks_file = Path(".agent_hooks.json")
        if hooks_file.exists():
            with open(hooks_file, 'r') as f:
                self.hooks = json.load(f)
        else:
            # Standard-Hooks
            self.hooks = {
                "on_write": ["run_tests"],
                "on_edit": ["run_tests"],
                "on_create_test": ["run_tests"]
            }
            self.save_hooks()
    
    def save_hooks(self):
        """Speichere Hook-Konfiguration"""
        with open(".agent_hooks.json", 'w') as f:
            json.dump(self.hooks, f, indent=2)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Führe ein Tool aus und triggere zugehörige Hooks"""
        try:
            # Tool ausführen
            result = self.registry.execute(tool_name, **kwargs)
            
            # Erfolg in Log schreiben
            self._log_execution(tool_name, kwargs, result)
            
            # Hooks ausführen
            hooks_to_run = []
            
            if tool_name == "write_file":
                hooks_to_run.extend(self.hooks.get("on_write", []))
            elif tool_name == "edit_file_line":
                hooks_to_run.extend(self.hooks.get("on_edit", []))
            elif tool_name == "create_test":
                hooks_to_run.extend(self.hooks.get("on_create_test", []))
            
            # Hooks ausführen
            hook_results = []
            for hook_tool in hooks_to_run:
                try:
                    hook_result = self.registry.execute(hook_tool)
                    hook_results.append({"hook": hook_tool, "result": hook_result})
                except Exception as e:
                    hook_results.append({"hook": hook_tool, "error": str(e)})
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "hooks": hook_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_result = {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
            self._log_execution(tool_name, kwargs, error_result)
            return error_result
    
    def _log_execution(self, tool: str, args: Dict[str, Any], result: Any):
        """Logge Tool-Ausführung"""
        log_file = self.state_dir / "tool_execution.log"
        
        entry = {
            "tool": tool,
            "args": args,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def list_tools(self) -> List[str]:
        """Liste alle verfügbaren Tools"""
        return list(self.registry.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Hole Informationen über ein spezifisches Tool"""
        if tool_name not in self.registry.tools:
            return {"error": "Tool not found"}
        
        tool_func = self.registry.tools[tool_name]
        import inspect
        
        return {
            "name": tool_name,
            "docstring": tool_func.__doc__,
            "signature": str(inspect.signature(tool_func))
        }


class AgentWorkflow:
    """Workflow-Engine für Build-Debug-Commit Cycle"""
    
    def __init__(self):
        self.router = ToolRouter()
        self.current_step = 0
        self.workflow_log = Path("/state") / "workflow.log"
    
    def plan_phase(self, description: str) -> Dict[str, Any]:
        """Planungsphase"""
        step = {
            "phase": "plan",
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self._log_workflow_step(step)
        return step
    
    def code_gen_phase(self, target: str, requirements: str) -> Dict[str, Any]:
        """Code-Generierungsphase"""
        step = {
            "phase": "code_gen",
            "target": target,
            "requirements": requirements,
            "timestamp": datetime.now().isoformat()
        }
        self._log_workflow_step(step)
        return step
    
    def test_phase(self) -> Dict[str, Any]:
        """Test-Phase mit automatischem Debugging"""
        result = self.router.execute_tool("run_tests")
        
        step = {
            "phase": "test",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self._log_workflow_step(step)
        
        # Auto-debug bei Fehlschlägen
        if not result.get("result", {}).get("success", True):
            return self.debug_phase(result)
        
        return step
    
    def debug_phase(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Debug-Phase bei Test-Fehlern"""
        step = {
            "phase": "debug",
            "test_result": test_result,
            "actions": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Analysiere Fehler und versuche automatische Fixes
        stderr = test_result.get("result", {}).get("stderr", "")
        if stderr:
            # Suche nach fehlenden Imports
            if "ImportError" in stderr:
                missing_module = self._extract_missing_module(stderr)
                if missing_module:
                    install_result = self.router.execute_tool("run_cmd", command=f"pip install {missing_module}")
                    step["actions"].append({"type": "install", "module": missing_module, "result": install_result})
            
            # Versuche erneut
            retry_result = self.router.execute_tool("run_tests")
            step["actions"].append({"type": "retry", "result": retry_result})
        
        self._log_workflow_step(step)
        return step
    
    def commit_phase(self, message: str) -> Dict[str, Any]:
        """Commit-Phase"""
        step = {
            "phase": "commit",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Git commit ausführen
        commit_result = self.router.execute_tool("run_cmd", command=f'git add . && git commit -m "{message}"')
        step["result"] = commit_result
        
        self._log_workflow_step(step)
        return step
    
    def _log_workflow_step(self, step: Dict[str, Any]):
        """Logge Workflow-Schritt"""
        with open(self.workflow_log, "a") as f:
            f.write(json.dumps(step) + "\n")
    
    def _extract_missing_module(self, stderr: str) -> Optional[str]:
        """Extrahiere fehlendes Modul aus ImportError"""
        match = re.search(r"No module named '([^']+)'", stderr)
        return match.group(1) if match else None


# JSON-RPC Interface
class JSONRPCInterface:
    """JSON-RPC Interface für Tool-Aufrufe"""
    
    def __init__(self):
        self.router = ToolRouter()
        self.workflow = AgentWorkflow()
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeite JSON-RPC Request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            id = request.get("id")
            
            if method.startswith("tool."):
                tool_name = method[5:]  # Entferne "tool." Präfix
                result = self.router.execute_tool(tool_name, **params)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": id
                }
            
            elif method.startswith("workflow."):
                workflow_method = method[9:]  # Entferne "workflow." Präfix
                workflow_func = getattr(self.workflow, f"{workflow_method}_phase")
                result = workflow_func(**params)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": id
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    },
                    "id": id
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": traceback.format_exc()
                },
                "id": request.get("id")
            }


# Global instances
router = ToolRouter()
workflow = AgentWorkflow()
json_rpc = JSONRPCInterface() 

import re  # Für die extract_missing_module Funktion
import datetime  # Für Zeitstempel
from typing import Optional


# Example usage
if __name__ == "__main__":
    # Teste Tool-Registry
    print("Available tools:", router.list_tools())
    
    # Beispiel-Tool-Aufruf
    result = router.execute_tool("read_file", path="main.py")
    print("Tool result:", result)
    
    # Beispiel-Workflow
    workflow.plan_phase("Test workflow")
    workflow.test_phase()