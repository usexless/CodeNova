import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from pathlib import Path

try:
    import faiss
    import openai
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    openai = None
    FAISS_AVAILABLE = False


class VectorMemory:
    def __init__(self, storage_path: str = "memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.index_path = self.storage_path / "index.faiss"
        self.metadata_path = self.storage_path / "metadata.json"
        
        self.index: Union['faiss.Index', 'SimpleMemory']
        self.dimension = 1536  # Standard-Dimension für den Fall, dass FAISS nicht verfügbar ist

        if FAISS_AVAILABLE:
            self.dimension = 1536  # OpenAI embedding dimension
            self._load_or_create_faiss_index()
        else:
            print("FAISS nicht verfügbar, nutze einfaches In-Memory Storage")
            self.index = SimpleMemory()
        
        self.metadata: List[Dict[str, Any]] = self._load_metadata()
    
    def _load_or_create_faiss_index(self):
        """Lädt einen FAISS-Index oder erstellt einen neuen."""
        if not FAISS_AVAILABLE or not faiss:
            self.index = SimpleMemory()
            return
            
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
        except Exception as e:
            print(f"Fehler beim Laden des FAISS-Indexes: {e}. Erstelle einen neuen Index.")
            self.index = faiss.IndexFlatL2(self.dimension)
            
    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Lädt Metadaten aus der JSON-Datei."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Fehler beim Laden der Metadaten: {e}. Erstelle eine neue Liste.")
        return []

    def add_memory(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Füge neue Erinnerung hinzu"""
        try:
            embedding = self._create_embedding(content)
            if embedding is None:
                return False

            # Füge zum Index hinzu
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Speichere Metadaten
            self.metadata.append({
                "content": content,
                **metadata,
                "id": len(self.metadata)
            })
            
            self._save()
            return True
                
        except Exception as e:
            print(f"Fehler beim Hinzufügen der Erinnerung: {e}")
        
        return False
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Suche nach ähnlichen Erinnerungen"""
        try:
            if self.index.ntotal > 0:
                # Erstelle Query-Embedding
                query_embedding = self._create_embedding(query)
                if query_embedding is not None:
                    # Suche im Index
                    k = min(k, self.index.ntotal)
                    distances, indices = self.index.search(
                        np.array([query_embedding], dtype=np.float32), k
                    )
                    
                    # Erstelle Ergebnisse
                    results = []
                    for distance, idx in zip(distances[0], indices[0]):
                        if idx >= 0 and idx < len(self.metadata):
                            result = dict(self.metadata[idx])
                            result["score"] = float(distance)
                            results.append(result)
                    
                    return results
            
            # Fallback auf einfache Text-Suche
            results = []
            query_lower = query.lower()
            for item in self.metadata:
                content = item.get("content")
                if content and query_lower in str(content).lower():
                    results.append(item)
            return results[:k]
                
        except Exception as e:
            print(f"Fehler bei der Suche: {e}")
        
        return []
    
    def get_memory_by_type(self, memory_type: str) -> List[Dict[str, Any]]:
        """Hole Erinnerungen nach Typ"""
        return [item for item in self.metadata if item.get("type") == memory_type]
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Hole letzte Erinnerungen"""
        return self.metadata[-limit:] if self.metadata else []
    
    def clear_memory(self) -> bool:
        """Lösche alle Erinnerungen"""
        try:
            if FAISS_AVAILABLE and faiss:
                self.index = faiss.IndexFlatL2(self.dimension)
            else:
                self.index = SimpleMemory()

            self.metadata = []
            
            # Lösche Dateien
            if self.index_path.exists():
                self.index_path.unlink()
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            
            return True
        except Exception as e:
            print(f"Fehler beim Löschen der Erinnerungen: {e}")
            return False
    
    def _create_embedding(self, text: str) -> Optional[np.ndarray]:
        """Erstelle Text-Embedding"""
        if not openai:
            print("OpenAI-Modul nicht verfügbar, kann keine Embeddings erstellen.")
            return None
        try:
            # Verwende OpenAI Embeddings
            client = openai.OpenAI()
            
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return np.array(response.data[0].embedding)
            
        except Exception as e:
            print(f"Fehler beim Erstellen des Embeddings: {e}")
            return None
    
    def _save(self) -> bool:
        """Speichere Index und Metadaten"""
        try:
            if FAISS_AVAILABLE and isinstance(self.index, faiss.Index):
                faiss.write_index(self.index, str(self.index_path))
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Hole Memory-Statistiken"""
        return {
            "total_memories": len(self.metadata),
            "storage_path": str(self.storage_path),
            "faiss_available": FAISS_AVAILABLE,
            "types": list(set(item.get("type", "unknown") for item in self.metadata))
        }

class SimpleMemory:
    """Einfache In-Memory Alternative für FAISS, die die Schnittstelle nachbildet."""
    
    def __init__(self):
        self.data: List[np.ndarray] = []
        self.ntotal = 0
    
    def add(self, x: np.ndarray):
        """Füge Embedding hinzu"""
        # FAISS erwartet eine 2D-Array
        if x.ndim == 1:
            x = np.array([x])
        self.data.extend(x)
        self.ntotal = len(self.data)
    
    def search(self, x: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Führt eine Ähnlichkeitssuche durch."""
        if not self.data:
            return np.array([[]], dtype='float32'), np.array([[]], dtype='int64')

        # Berechne L2-Distanzen
        all_data = np.array(self.data)
        distances = np.linalg.norm(all_data - x, axis=1)
        
        # Sortiere und finde die k nächsten
        k = min(k, len(distances))
        indices = np.argsort(distances)[:k]
        
        return np.array([distances[indices]], dtype='float32'), np.array([indices], dtype='int64')

# Globaler VectorMemory
vector_memory = VectorMemory()

# Exportiere für einfachen Zugriff
def add_project_memory(content: str, project_name: str, memory_type: str = "general"):
    """Füge Projekt-Erinnerung hinzu"""
    return vector_memory.add_memory(content, {
        "type": memory_type,
        "project": project_name,
        "timestamp": str(__import__('datetime').datetime.now())
    })

def search_project_memory(query: str, project_name: Optional[str] = None, k: int = 5):
    """Suche in Projekt-Erinnerungen"""
    results = vector_memory.search_similar(query, k)
    
    if project_name:
        results = [r for r in results if r.get('project') == project_name]
    
    return results