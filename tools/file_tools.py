import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import glob

class FileManager:
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
    
    def create_project_structure(self, project_name: str) -> Path:
        """Erstellt nur das Haupt-Projektverzeichnis.
        Unterverzeichnisse werden dynamisch beim Schreiben von Dateien erstellt.
        """
        project_path = self.base_path / "projects" / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    def read_file(self, file_path: str) -> str:
        """Lese Datei-Inhalt"""
        try:
            full_path = self.base_path / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Fehler beim Lesen: {str(e)}"
    
    def write_file(self, file_path: str, content: str, create_dirs: bool = True) -> bool:
        """Schreibe Inhalt in Datei"""
        try:
            full_path = self.base_path / file_path
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Fehler beim Schreiben: {str(e)}")
            return False
    
    def edit_file(self, file_path: str, old_text: str, new_text: str) -> bool:
        """Ersetze Text in Datei"""
        try:
            content = self.read_file(file_path)
            if old_text in content:
                new_content = content.replace(old_text, new_text)
                return self.write_file(file_path, new_content)
            return False
        except Exception as e:
            print(f"Fehler beim Editieren: {str(e)}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Lösche Datei"""
        try:
            full_path = self.base_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Fehler beim Löschen: {str(e)}")
            return False
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> List[str]:
        """Liste Dateien in Verzeichnis"""
        try:
            search_path = self.base_path / directory
            files = glob.glob(str(search_path / "**" / pattern), recursive=True)
            return [str(Path(f).relative_to(self.base_path)) for f in files]
        except Exception as e:
            print(f"Fehler beim Auflisten: {str(e)}")
            return []
    
    def file_exists(self, file_path: str) -> bool:
        """Prüfe ob Datei existiert"""
        full_path = self.base_path / file_path
        return full_path.exists()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Hole Datei-Informationen"""
        try:
            full_path = self.base_path / file_path
            if not full_path.exists():
                return {}
            
            stat = full_path.stat()
            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": full_path.is_file(),
                "is_dir": full_path.is_dir()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def copy_file(self, src_path: str, dest_path: str) -> bool:
        """Kopiere Datei"""
        try:
            src = self.base_path / src_path
            dest = self.base_path / dest_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            return True
        except Exception as e:
            print(f"Fehler beim Kopieren: {str(e)}")
            return False
    
    def create_directory(self, dir_path: str) -> bool:
        """Erstelle Verzeichnis"""
        try:
            full_path = self.base_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Fehler beim Erstellen: {str(e)}")
            return False
    
    def search_files(self, search_term: str, directory: str = ".") -> List[Dict[str, Any]]:
        """Suche in Dateien nach Text"""
        results = []
        try:
            search_path = self.base_path / directory
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        if search_term in content:
                            lines = content.split('\n')
                            matches = []
                            for i, line in enumerate(lines, 1):
                                if search_term in line:
                                    matches.append({
                                        "line": i,
                                        "content": line.strip()
                                    })
                            results.append({
                                "file": str(file_path.relative_to(self.base_path)),
                                "matches": matches
                            })
                    except Exception:
                        continue
        except Exception as e:
            print(f"Fehler bei Suche: {str(e)}")
        return results

# Globaler FileManager
file_manager = FileManager()