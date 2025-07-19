# AI Programmer - Erweiterte Tools & Workflows

Dieses Dokument beschreibt die neuen Core-Tools und Workflow-Engines des AI-Programmier-Frameworks.

## 🛠️ Core Tools

### Datei-Operationen

#### `read_file(path: str) -> str`
Liest den Inhalt einer Datei.
```json
{
  "tool": "read_file",
  "params": {"path": "main.py"}
}
```

#### `write_file(path: str, content: str) -> dict`
Überschreibt eine Datei mit neuem Inhalt.
```json
{
  "tool": "write_file",
  "params": {
    "path": "new_file.py",
    "content": "print('Hello World')"
  }
}
```

#### `edit_file_line(path: str, line: int, new_line: str) -> dict`
Ersetzt eine spezifische Zeile in einer Datei.
```json
{
  "tool": "edit_file_line",
  "params": {
    "path": "main.py",
    "line": 5,
    "new_line": "print('Updated line')"
  }
}
```

#### `append_file(path: str, content: str) -> dict`
Hängt Inhalt an eine Datei an.
```json
{
  "tool": "append_file",
  "params": {
    "path": "log.txt",
    "content": "\nNew log entry"
  }
}
```

### Code-Suche

#### `search_code(pattern: str, path: str|None) -> list`
Grep-ähnliche Suche mit Regex-Pattern.
```json
{
  "tool": "search_code",
  "params": {
    "pattern": "class.*Agent",
    "path": "agents/"
  }
}
```

### Ausführung

#### `run_cmd(command: str, timeout: int=120) -> dict`
Führt Shell-Kommando aus.
```json
{
  "tool": "run_cmd",
  "params": {
    "command": "pytest -v",
    "timeout": 60
  }
}
```

#### `run_py(code: str) -> dict`
Führt Python-Code im REPL aus.
```json
{
  "tool": "run_py",
  "params": {
    "code": "import math; print(math.pi)"
  }
}
```

### Testing

#### `create_test(name: str, code: str) -> dict`
Erstellt eine neue Testdatei.
```json
{
  "tool": "create_test",
  "params": {
    "name": "calculator",
    "code": "def test_add(): assert 2 + 2 == 4"
  }
}
```

#### `run_tests() -> dict`
Führt alle Tests mit pytest aus.
```json
{
  "tool": "run_tests",
  "params": {}
}
```

## 🔧 Tool Router

### JSON-RPC Interface

```python
from agents.tool_router import json_rpc

# Tool-Aufruf
request = {
    "jsonrpc": "2.0",
    "method": "tool.read_file",
    "params": {"path": "main.py"},
    "id": 1
}

result = json_rpc.handle_request(request)
```

### Workflow-Phasen

#### Plan-Phase
```json
{
  "jsonrpc": "2.0",
  "method": "workflow.plan",
  "params": {"description": "Implement calculator class"},
  "id": 1
}
```

#### Code-Gen-Phase
```json
{
  "jsonrpc": "2.0",
  "method": "workflow.code_gen",
  "params": {
    "target": "calculator.py",
    "requirements": "Basic arithmetic operations"
  },
  "id": 2
}
```

#### Test-Phase
```json
{
  "jsonrpc": "2.0",
  "method": "workflow.test",
  "params": {},
  "id": 3
}
```

## 🪝 Hook-Engine

### Konfiguration
Erstelle `.agent_hooks.json`:

```json
{
  "on_write": ["run_tests"],
  "on_edit": ["run_tests"],
  "on_create_test": ["run_tests"]
}
```

### Automatische Hooks
Hooks werden automatisch nach Tool-Ausführung ausgelöst:
- `on_write`: Nach `write_file`
- `on_edit`: Nach `edit_file_line`
- `on_create_test`: Nach `create_test`


## 📊 Logging & Monitoring

### Trace-Log
Alle Tool-Aktionen werden in `/state/trace.log` gespeichert:

```json
{
  "tool": "write_file",
  "args": {"path": "calculator.py", "content": "..."},
  "result": "success",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Workflow-Log
Workflow-Schritte werden in `/state/workflow.log` gespeichert:

```json
{
  "phase": "test",
  "result": {...},
  "timestamp": "2024-01-15T10:31:00.789012"
}
```


## 🔄 Komplettes Beispiel

### End-to-End Workflow

```python
# 1. Plan erstellen
router.execute_tool("write_file", 
    path="plan.md", 
    content="# Calculator Implementation Plan\n\n## Steps\n1. Create calculator.py\n2. Write unit tests\n3. Run tests\n4. Fix issues"
)

# 2. Code generieren
router.execute_tool("write_file",
    path="calculator.py",
    content="''\"Calculator module''\"\n\ndef add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b"
)

# 3. Tests erstellen
router.execute_tool("create_test", 
    name="calculator",
    code="''\"Test calculator''\"\nfrom calculator import add, multiply\n\ndef test_add():\n    assert add(2, 3) == 5\n\ndef test_multiply():\n    assert multiply(3, 4) == 12"
)

# 4. Tests ausführen
router.execute_tool("run_tests")

# 5. Status prüfen
router.execute_tool("run_cmd", command="git status")
```

## 🎯 Integration mit bestehenden Agenten

Die neuen Tools können direkt in Agenten verwendet werden:

```python
from agents.tool_router import router

class EnhancedCodeGenerator:
    def generate_with_tools(self, requirements: str):
        # Plan erstellen
        router.execute_tool("write_file", path="plan.txt", content=requirements)
        
        # Code generieren
        code = self.create_code(requirements)
        router.execute_tool("write_file", path="generated.py", content=code)
        
        # Tests erstellen
        tests = self.create_tests(code)
        router.execute_tool("create_test", name="generated", code=tests)
        
        # Tests ausführen
        return router.execute_tool("run_tests")
```

## 🔍 Debugging

### Fehlerbehebung mit Tools

```python
# Fehleranalyse
error_result = router.execute_tool("run_tests")
if not error_result["success"]:
    # Code-Suche nach Fehlern
    errors = router.execute_tool("search_code", pattern="assert.*False")
    
    # Logs anzeigen
    logs = router.execute_tool("read_file", path="/state/trace.log")
    
    # Fix anwenden
    router.execute_tool("edit_file_line", 
        path="test_file.py", 
        line=10, 
        new_line="assert result == expected"
    )
```

## 📈 Performance Monitoring

### Zeitmessung
Alle Tool-Ausführungen werden mit Zeitstempeln geloggt für Performance-Analyse.

### Resource-Tracking
Typische Ausführungszeiten:
- Setup: ~2-5 Sekunden
- Lint: ~1-3 Sekunden
- Tests: ~0.5-2 Sekunden
- Coverage: ~2-4 Sekunden

## 🚀 Erweiterte Nutzung

### Custom Hooks
```json
{
  "on_write": ["run_cmd", "create_test"],
  "on_test_failure": ["debug_phase"],
  "on_success": ["commit_phase"]
}
```


Diese Tools bieten ein vollständiges Entwicklungs-Ökosystem mit automatischer Code-Qualitätssicherung und Continuous Integration-Funktionen.