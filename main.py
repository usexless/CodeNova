#!/usr/bin/env python3

import click
import os
import sys
from typing import Dict, Any
import json # Added missing import for json

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Confirm
from rich.markdown import Markdown
from rich.table import Table

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

from agents.project_manager import ProjectManager
from agents.code_generator import CodeGenerator
from agents.test_runner import TestRunner
from agents.debugger import Debugger

from config.settings import (
    is_configured, save_configuration, get_current_provider_config, 
    get_current_model, AVAILABLE_PROVIDERS
)
from llm import llm_manager

console = Console()

def setup_wizard():
    """Führt den interaktiven Einrichtungsassistenten aus."""
    console.print(Panel(
        "[bold blue]Willkommen beim AI Programmer Setup Wizard![/bold blue]\n\n"
        "Lass uns die Anwendung für den ersten Gebrauch konfigurieren.",
        title="🔧 Ersteinrichtung",
        border_style="blue"
    ))

    # 1. Provider auswählen
    provider_options = list(AVAILABLE_PROVIDERS.keys())
    provider_map = {str(i+1): p for i, p in enumerate(provider_options)}
    
    table = Table(title="Verfügbare LLM Provider")
    table.add_column("Option", style="cyan")
    table.add_column("Provider", style="green")
    for num, name in provider_map.items():
        table.add_row(num, AVAILABLE_PROVIDERS[name]['name'])
    console.print(table)
    
    choice = IntPrompt.ask(
        "Wähle einen Provider", 
        choices=list(provider_map.keys()), 
        show_choices=False
    )
    provider = provider_map[str(choice)]

    # 2. API-Schlüssel eingeben
    # Da Prompt nicht mehr direkt importiert wird, nutzen wir console.input für Einfachheit
    console.print(f"Gib deinen [bold green]{AVAILABLE_PROVIDERS[provider]['name']}[/bold green] API-Schlüssel ein:")
    api_key = console.input()

    # 3. Modell auswählen
    model_options = AVAILABLE_PROVIDERS[provider]['models']
    model_map = {str(i+1): m for i, m in enumerate(model_options)}
    
    table = Table(title=f"Verfügbare Modelle für {AVAILABLE_PROVIDERS[provider]['name']}")
    table.add_column("Option", style="cyan")
    table.add_column("Modell", style="green")
    for num, name in model_map.items():
        table.add_row(num, name)
    console.print(table)
    
    model_choice = IntPrompt.ask(
        "Wähle ein Modell", 
        choices=list(model_map.keys()), 
        show_choices=False
    )
    model = model_map[str(model_choice)]

    # Konfiguration speichern
    save_configuration(provider, api_key, model)
    console.print("\n[bold green]✅ Einrichtung abgeschlossen![/bold green]")

class CodeNova: # Umbenennung von AIProgrammer
    def __init__(self):
        self.modes = ["Chat", "Auto"]
        self.current_mode_index = 0
        self.shared_context = {"history": []} # Geteilter Kontext mit Gedächtnis
        
        self.project_manager = ProjectManager()
        self.code_generator = CodeGenerator()
        self.test_runner = TestRunner()
        self.debugger = Debugger()

    def get_bottom_toolbar(self):
        """Erzeugt die Toolbar, die den aktuellen Modus anzeigt."""
        mode = self.modes[self.current_mode_index]
        color_map = {"Chat": 'bg="#00aa00"', "Auto": 'bg="#5f00d7"'} # Farbe für Auto-Modus
        color = color_map.get(mode, 'bg="#444444"')
        
        toolbar_text = (
            f' <b><style fg="white" {color}> {mode.upper()} </style></b>'
            f' Drücke <b>&lt;Tab&gt;</b> um den Modus zu wechseln.'
            f' <b>&lt;Ctrl-C&gt;</b> zum Beenden.'
        )
        return HTML(toolbar_text)

    def interactive_mode(self):
        """Startet den interaktiven Modus mit prompt_toolkit."""
        self._print_welcome()
        
        bindings = KeyBindings()
        @bindings.add('tab')
        def _(event):
            self.current_mode_index = (self.current_mode_index + 1) % len(self.modes)
        
        session = PromptSession(
            key_bindings=bindings,
            bottom_toolbar=self.get_bottom_toolbar,
            refresh_interval=0.5
        )
        
        while True:
            try:
                prompt_text = HTML('<ansigreen><b>&gt; </b></ansigreen>')
                user_input = session.prompt(prompt_text)
                self._handle_input(user_input)
            except (KeyboardInterrupt, EOFError):
                console.print("\nAuf Wiedersehen!")
                break

    def _handle_input(self, user_input: str):
        """Behandelt Benutzereingaben basierend auf dem expliziten Modus."""
        if not user_input.strip(): return
        if user_input.lower() in ['/exit', '/quit']:
            console.print("\nAuf Wiedersehen!"); sys.exit(0)

        mode = self.modes[self.current_mode_index]
        
        if mode == "Chat":
            self._handle_chat_message(user_input)
        elif mode == "Auto":
            self._handle_auto_mode(user_input)

    def _handle_chat_message(self, user_input: str):
        """Führt eine Chat-Interaktion mit Tool-Unterstützung durch und speichert den Verlauf."""
        self.shared_context["history"].append({"role": "user", "content": user_input})
        console.print("\n[bold blue]🤖 CodeNova:[/bold blue]")

        # Verwende den ToolAgent für alle Provider im Chat-Modus (nur lesende Tools)
        from agents.tool_agent import ToolAgent
        tool_agent = ToolAgent(chat_mode=True)  # Chat-Modus: nur lesende/analysierende Tools
        from agents.base_agent import Task
        task = Task(
            description=user_input,
            task_type="chat"
        )
        result = tool_agent.process_task(task)
        if result.get("status") == "completed":
            answer = result.get("final_response", "Ich konnte die Aufgabe nicht abschließen.")
        else:
            from llm import llm_manager
            answer = llm_manager.generate_response(
                system_prompt="Du bist ein hilfreicher KI-Programmier-Assistent auf Windows 11 mit PowerShell. Deine Aufgabe ist es, Projektanforderungen mit dem Benutzer zu planen und zu verfeinern. Gib klare und prägnante Antworten. WICHTIG: Du arbeitest in einer Windows PowerShell-Umgebung. Verwende nur Windows-kompatible Befehle und Pfade.",
                user_prompt=user_input,
                context=self.shared_context["history"]
            )
        from rich.markdown import Markdown
        console.print(Markdown(answer))
        self.shared_context["history"].append({"role": "assistant", "content": answer})
        if len(self.shared_context["history"]) > 10:
            self.shared_context["history"] = self.shared_context["history"][-10:]

    def _should_build_project(self, user_input: str) -> bool:
        """KI-basierte Intent-Erkennung: Entscheidet intelligent, ob eine Projektanforderung vorliegt."""
        prompt = f"""
        Analysiere die folgende Benutzereingabe und entscheide, ob der Benutzer ein neues Softwareprojekt erstellen möchte oder nur eine Frage stellt.

        BENUTZEREINGABE: "{user_input}"

        Entscheide basierend auf:
        1. **Projektanforderung**: Benutzer möchte eine neue Anwendung, Website, API, Tool, etc. erstellen
        2. **Normale Frage**: Benutzer stellt eine Frage, sucht Hilfe, möchte etwas lernen, etc.

        Antworte nur mit "PROJEKT" oder "FRAGE".

        Beispiele:
        - "erstelle eine website" → PROJEKT
        - "was ist Python?" → FRAGE  
        - "wie funktioniert das?" → FRAGE
        - "mache ein tool für..." → PROJEKT
        - "was siehst du hier?" → FRAGE
        - "baue eine app die..." → PROJEKT
        """

        try:
            response = llm_manager.generate_response(
                system_prompt="Du bist ein Experte für Intent-Erkennung. Deine Aufgabe ist es, zu entscheiden, ob eine Benutzereingabe eine Projektanforderung oder eine normale Frage ist. Antworte nur mit 'PROJEKT' oder 'FRAGE'.",
                user_prompt=prompt
            ).strip().upper()
            
            return response == "PROJEKT"
        except Exception as e:
            # Fallback: Bei Fehlern behandle als normale Frage
            console.print(f"[yellow]⚠️  Intent-Erkennung fehlgeschlagen: {e}[/yellow]")
            return False

    def _handle_auto_mode(self, user_input: str):
        """KI-basierte Intent-Erkennung und autonome Entscheidungsfindung."""
        # KI-basierte Intent-Erkennung
        with console.status("[bold blue]🤖 KI analysiert deine Eingabe...", spinner="dots"):
            is_project_request = self._should_build_project(user_input)
        
        if not is_project_request:
            # KI hat entschieden: Normale Frage
            console.print("[blue]🤖 KI-Entscheidung:[/blue] [green]Normale Frage erkannt[/green] - Behandle als Chat-Nachricht")
            self._handle_chat_message(user_input)
            return
        
        # KI hat entschieden: Projektanforderung
        console.print("[blue]🤖 KI-Entscheidung:[/blue] [yellow]Projektanforderung erkannt[/yellow] - Starte autonome Projekterstellung")
        
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.shared_context["history"]])
        
        prompt = f"""
        Basierend auf der folgenden Konversation und der letzten Anweisung des Benutzers, fasse die endgültigen Projektanforderungen in einem einzigen Satz zusammen.

        Konversation:
        {history_str}

        Letzte Anweisung des Benutzers: "{user_input}"

        Zusammengefasste Projektanforderungen:
        """
        
        with console.status("[bold yellow]Analysiere Anforderungen aus dem Chat-Verlauf...", spinner="dots"):
            requirements = llm_manager.generate_response(
                system_prompt="Du bist ein Experte für die Zusammenfassung von Anforderungen auf Windows 11. WICHTIG: Du arbeitest in einer Windows PowerShell-Umgebung. Verwende nur Windows-kompatible Befehle und Pfade.",
                user_prompt=prompt
            ).strip()

        console.print(f"[green]Anforderungen extrahiert:[/green] [italic]{requirements}[/italic]")

        project_name = self.project_manager.generate_project_name(requirements)
        self.build_project(project_name, requirements)

    def build_project(self, name: str, requirements: str):
        """Führt den gesamten Build-Prozess für ein Projekt transparent und interaktiv aus."""
        console.print(Panel(f"Baue Projekt [bold cyan]{name}[/bold cyan]...", border_style="green"))
        
        try:
            # 1. Plan generieren
            with console.status("[bold green]1. Erstelle Projektstruktur und Plan...", spinner="dots"):
                project_info = self.project_manager.create_project(name, requirements)
                plan = self.project_manager.plan_project(project_info)
            console.print("[green]✅ Plan erstellt.[/green]")

            files_to_create = plan.get("plan", {}).get("files", [])
            if not files_to_create:
                console.print("[bold red]Fehler: Der Plan enthält keine zu erstellenden Dateien.[/bold red]")
            return
        
            # 2. Dateien einzeln generieren und linten
            console.print(f"[bold green]2. Generiere {len(files_to_create)} Dateien...[/bold green] ([Ctrl-C] zum Abbrechen)")
            generated_files = []
            test_files = []
            
            for i, file_info in enumerate(files_to_create):
                path = file_info.get("path", "unbekannte_datei.txt")
                console.print(f"  [{(i+1)}/{len(files_to_create)}] [cyan]{path}[/cyan]")
                
                # Datei generieren
                console.print(f"    └── [yellow]Generiere Code...[/yellow]", end="")
                file_list = self.code_generator.generate_code({"plan": {"files": [file_info]}, "path": project_info["path"]})
                if not file_list:
                    console.print(f"\r    └── [red]Generierung fehlgeschlagen.[/red]")
                continue
                console.print(f"\r    └── [green]Generiere Code... OK[/green]")
                
                # Linter ausführen
                file_path = file_list[0]
                self.debugger.lint_and_fix_file(file_path)

                if file_info.get("is_test_file", False):
                    test_files.append(file_path)
                else:
                    generated_files.append(file_path)

            # 3. Finale Tests ausführen
            console.print("[bold green]3. Führe finale Tests aus...[/bold green]")
            if not test_files:
                console.print("[yellow]Keine Testdateien gefunden. Überspringe Tests.[/yellow]")
            else:
                test_results = self.test_runner.run_tests(project_info['path'])
                if test_results.get("success"):
                    console.print("[bold green]✅ Alle Tests erfolgreich![/bold green]")
                else:
                    console.print("[bold yellow]⚠️ Tests fehlgeschlagen. Starte Debugger...[/bold yellow]")
                    self.debugger.debug_project(project_info, test_results)

            # 4. Abschlussbericht generieren
            console.print("[bold green]4. Generiere Abschlussbericht...[/bold green]")
            summary = self.project_manager.generate_project_summary(project_info)
            console.print(Panel(Markdown(summary), title="🚀 Projekt-Zusammenfassung", border_style="green", expand=False))
                
        except KeyboardInterrupt:
            console.print("\n\n[bold red]Build-Prozess vom Benutzer abgebrochen.[/bold red]")
            return
        

    def _print_welcome(self):
        provider_config = get_current_provider_config()
        model = get_current_model()
        
        console.clear()
        console.print(Panel(
            f"Willkommen bei CodeNova! Deine interaktive Kommandozeile ist startklar.\n"
            f"Aktueller Provider: [bold blue]{provider_config['name']}[/bold blue] | Modell: [bold green]{model}[/bold green]\n\n"
            f"[bold yellow]Professionelle KI-Modi (10.000€ System):[/bold yellow]\n"
            f"• [green]CHAT[/green]: Normale Fragen und Diskussionen\n"
            f"• [blue]AUTO[/blue]: KI entscheidet selbst, wann Projekte erstellt werden\n\n"
            f"[bold cyan]Erweiterte KI-Fähigkeiten:[/bold cyan]\n"
            f"• [bold]Autonome Problemlösung[/bold]: KI arbeitet selbstständig bis zur vollständigen Lösung\n"
            f"• [bold]Semantische Codebase-Suche[/bold]: Intelligente Code-Exploration und -Analyse\n"
            f"• [bold]Erweiterte Datei-Operationen[/bold]: Präzise Bearbeitung, Chunk-Ansicht, Code-Element-Analyse\n"
            f"• [bold]Web-Deployment[/bold]: Automatisches Deployen von Webanwendungen (Netlify, etc.)\n"
            f"• [bold]Browser-Vorschau[/bold]: Interaktive Webserver-Vorschau\n"
            f"• [bold]Web-Recherche[/bold]: Intelligente Websuche und URL-Inhaltsanalyse\n"
            f"• [bold]Memory-System[/bold]: Kontext-Speicherung und -Wiederherstellung\n"
            f"• [bold]Befehlsüberwachung[/bold]: Erweiterte Terminal-Befehls-Kontrolle\n"
            f"• [bold]Proaktive Tool-Verwendung[/bold]: Verwendet Tools ohne zu fragen\n"
            f"• [bold]Vollständige Lösungen[/bold]: Löst Probleme komplett, nicht nur teilweise\n\n"
            f"[bold cyan]Tipps:[/bold cyan]\n"
            f"• Drücke [bold]Tab[/bold] um zwischen Modi zu wechseln\n"
            f"• Die KI entscheidet selbst, was zu tun ist - du musst nichts vorgeben\n"
            f"• Im AUTO-Modus: KI erkennt automatisch Projektanforderungen vs. normale Fragen\n"
            f"• Die KI arbeitet autonom und löst Probleme vollständig mit erweiterten Fähigkeiten",
            title="🤖 CodeNova v3.0 - Erweiterte Professionelle KI (10.000€ System)",
            border_style="green"
        ))

@click.command()
def main_cli():
    """Der Haupteinstiegspunkt für CodeNova.""" # Umbenannt
    if not is_configured():
        setup_wizard()
    
    try:
        llm_manager.reload_config()
        app = CodeNova() # Umbenannt
        app.interactive_mode()
    except Exception as e:
        console.print(f"[bold red]Ein kritischer Fehler ist aufgetreten: {e}[/bold red]")
        console.print("Bitte überprüfe deine `.env`-Datei oder führe die Einrichtung erneut aus.")
        if Confirm.ask("Möchtest du die Konfiguration jetzt zurücksetzen und neu starten?"):
            # Erstelle eine leere .env, um die Einrichtung zu erzwingen
            open(".env", "w").close()
            setup_wizard()
            llm_manager.reload_config()
            app = CodeNova()
            app.interactive_mode()

if __name__ == "__main__":
    main_cli()