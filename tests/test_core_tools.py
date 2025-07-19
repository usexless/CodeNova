"""
Tests für die Core-Tools
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys
import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.core_tools import CoreTools


class TestCoreTools:
    
    def setup_method(self):
        self.tools = CoreTools()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_read_file(self):
        """Test das Lesen einer Datei"""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello World")
        
        content = self.tools.read_file(str(test_file))
        assert content == "Hello World"
    
    def test_write_file(self):
        """Test das Schreiben einer Datei"""
        test_file = Path(self.temp_dir) / "write_test.txt"
        
        result = self.tools.write_file(str(test_file), "Test content")
        assert result["success"] is True
        assert test_file.read_text() == "Test content"
    
    def test_edit_file_line(self):
        """Test das Editieren einer Zeile"""
        test_file = Path(self.temp_dir) / "edit_test.txt"
        test_file.write_text("line1\nline2\nline3")
        
        result = self.tools.edit_file_line(str(test_file), 2, "new_line2")
        assert result["success"] is True
        assert test_file.read_text() == "line1\nnew_line2\nline3"
    
    def test_append_file(self):
        """Test das Anhängen an eine Datei"""
        test_file = Path(self.temp_dir) / "append_test.txt"
        test_file.write_text("initial")
        
        result = self.tools.append_file(str(test_file), "\nappended")
        assert result["success"] is True
        assert test_file.read_text() == "initial\nappended"
    
    def test_search_code(self):
        """Test die Code-Suche"""
        test_file = Path(self.temp_dir) / "search_test.py"
        test_file.write_text("class TestClass:\n    def test_method(self):\n        pass")
        
        results = self.tools.search_code("class.*Test", str(self.temp_dir))
        assert len(results) > 0
        assert "TestClass" in results[0]["content"]
    
    def test_run_cmd(self):
        """Test das Ausführen von Kommandos"""
        result = self.tools.run_cmd("echo 'test'", timeout=5)
        assert result["success"] is True
        assert "test" in result["stdout"]
    
    def test_run_py(self):
        """Test das Ausführen von Python-Code"""
        code = "print('Hello from Python')"
        result = self.tools.run_py(code)
        assert result["success"] is True
        assert "Hello from Python" in result["stdout"]
    
    def test_create_test(self):
        """Test das Erstellen von Tests"""
        result = self.tools.create_test("example", "def test_example(): assert True")
        assert result["success"] is True
        
        test_file = Path("tests") / "test_example.py"
        assert test_file.exists()
        content = test_file.read_text()
        assert "test_example" in content
    
    def test_run_tests(self):
        """Test das Ausführen von Tests"""
        result = self.tools.run_tests()
        # Erwartet, dass pytest installiert ist
        assert isinstance(result, dict)
        assert "exit_code" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])