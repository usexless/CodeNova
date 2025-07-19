from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from llm import llm_manager, ChatMessage

class Task:
    def __init__(self, description: str, task_type: str = "general", context: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())
        self.description = description
        self.task_type = task_type
        self.context = context or {}
        self.status = "pending"
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.id = str(uuid.uuid4())
        self.tasks = []
        self.memory = []
    
    @abstractmethod
    def system_prompt(self) -> str:
        """Definiere die System-Prompt für diesen Agenten"""
        pass
    
    @abstractmethod
    def process_task(self, task: Task) -> Dict[str, Any]:
        """Verarbeite eine spezifische Aufgabe"""
        pass
    
    def execute_task(self, task: Task) -> Task:
        """Führe eine Aufgabe aus mit Error-Handling"""
        try:
            task.status = "in_progress"
            result = self.process_task(task)
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()
            
            # Speichere in Memory
            self.memory.append({
                "task_id": task.id,
                "task": task.description,
                "result": result,
                "timestamp": datetime.now()
            })
            
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.completed_at = datetime.now()
        
        return task
    
    def add_task(self, description: str, task_type: str = "general", context: Optional[Dict[str, Any]] = None) -> Task:
        """Füge neue Aufgabe hinzu"""
        task = Task(description, task_type, context)
        self.tasks.append(task)
        return task
    
    def get_llm_response(self, prompt: str, context: Optional[List[ChatMessage]] = None) -> str:
        """Hole Antwort vom LLM"""
        # Der llm_manager erwartet möglicherweise ein spezifisches Format, aber für die
        # interne Typisierung ist dies korrekt. Wir übergeben den Kontext einfach weiter.
        return llm_manager.generate_response(
            system_prompt=self.system_prompt(),
            user_prompt=prompt,
            context=context
        )
    
    def get_task_status(self) -> Dict[str, int]:
        """Zeige Task-Status"""
        return {
            "total": len(self.tasks),
            "pending": len([t for t in self.tasks if t.status == "pending"]),
            "in_progress": len([t for t in self.tasks if t.status == "in_progress"]),
            "completed": len([t for t in self.tasks if t.status == "completed"]),
            "failed": len([t for t in self.tasks if t.status == "failed"])
        }