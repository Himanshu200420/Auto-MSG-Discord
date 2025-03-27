from http.client import HTTPSConnection 
from sys import stderr 
from json import dumps
from time import sleep 
import json
import threading
from datetime import datetime
import random
import os
import typer
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# Initialize typer app
app = typer.Typer()

# Initialize rich console
console = Console()

# ASCII Art
BANNER = """
 █████╗ ██╗   ██╗████████╗ ██████╗     ███╗   ███╗███████╗ ██████╗ 
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ████╗ ████║██╔════╝██╔════╝ 
███████║██║   ██║   ██║   ██║   ██║    ██╔████╔██║███████╗██║  ███╗
██╔══██║██║   ██║   ██║   ██║   ██║    ██║╚██╔╝██║╚════██║██║   ██║
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║ ╚═╝ ██║███████║╚██████╔╝
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝     ╚═╝╚══════╝ ╚═════╝ 
"""

# Global shutdown event
shutdown_event = threading.Event()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console, markup=True)]
)

logger = logging.getLogger("discord_bot")

def setup_config():
    if not os.path.exists('./config.json'):
        console.print(Panel.fit("No config file found. Let's create one!", title="Setup", border_style="blue"))
        channelid = Prompt.ask("Enter your Discord channel ID")
        token = Prompt.ask("Enter your Discord bot token")
        
        config = {
            "Config": [{
                "channelid": channelid,
                "token": token,
                "messages": []
            }]
        }
        
        with open('./config.json', 'w') as f:
            json.dump(config, f, indent=4)
        console.print("[green]Config file created successfully![/green]")
    else:
        console.print("[green]Config file found![/green]")

def add_message():
    message = Prompt.ask("Enter the message to send")
    min_interval = float(Prompt.ask("Enter minimum interval (in seconds)", default="10"))
    max_interval = float(Prompt.ask("Enter maximum interval (in seconds)", default="30"))
    
    with open('./config.json', 'r') as f:
        config = json.load(f)
    
    config['Config'][0]['messages'].append({
        "message": message,
        "min_interval": min_interval,
        "max_interval": max_interval
    })
    
    with open('./config.json', 'w') as f:
        json.dump(config, f, indent=4)
    console.print("[green]Message added successfully![/green]")

def load_config():
    with open('./config.json') as f:
        return json.load(f)

def get_connection(token): 
    return HTTPSConnection("discordapp.com", 443) 
 
def send_message(conn, channel_id, message_data, token): 
    try: 
        header_data = { 
            "content-type": "application/json", 
            "user-agent": "discordapp.com", 
            "authorization": token
        }
        conn.request("POST", f"/api/v9/channels/{channel_id}/messages", message_data, header_data) 
        resp = conn.getresponse() 
         
        if 199 < resp.status < 300: 
            console.print(f"[cyan]Message Sent at {datetime.now().strftime('%H:%M:%S')}[/cyan]")
        else: 
            console.print(f"[red]HTTP {resp.status}: {resp.reason}[/red]")
 
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

def message_loop(message, min_interval, max_interval, channel_id, token):
    while not shutdown_event.is_set():
        try:
            message_data = { 
                "content": message, 
                "tts": "false"
            } 
            send_message(get_connection(token), channel_id, dumps(message_data), token)
            shutdown_event.wait(timeout=random.uniform(min_interval, max_interval))
        except Exception as e:
            console.print(f"[red]Error in message loop: {str(e)}[/red]")
            break

def shutdown_handler():
    console.print("[yellow]Shutting down...[/yellow]")
    shutdown_event.set()

def show_menu():
    console.print("\n[bold cyan]Available Commands:[/bold cyan]")
    console.print("1. [green]Add new message[/green]")
    console.print("2. [green]Start bot[/green]")
    console.print("3. [red]Exit[/red]")

def start_bot():
    config = load_config()
    channelid = config['Config'][0]['channelid']
    token = config['Config'][0]['token']
    messages = config['Config'][0]['messages']
    
    if not messages:
        console.print("[yellow]No messages configured! Please add messages first.[/yellow]")
        return
    
    shutdown_event.clear()
    
    threads = []
    for msg_config in messages:
        message = msg_config['message']
        min_interval = msg_config['min_interval']
        max_interval = msg_config['max_interval']
        console.print(f"[green]Starting message thread for '{message}' with random interval between {min_interval} and {max_interval} seconds[/green]")
        
        thread = threading.Thread(
            target=message_loop,
            args=(message, min_interval, max_interval, channelid, token),
            daemon=True
        )
        threads.append(thread)
        thread.start()
    
    console.print(Panel.fit("Bot is running! Press Ctrl+C to stop.", title="Status", border_style="green"))
    try:
        while not shutdown_event.is_set():
            sleep(1)
    except KeyboardInterrupt:
        shutdown_handler()
    
    for thread in threads:
        thread.join(timeout=2.0)
    console.print("[green]Bot stopped successfully[/green]")

@app.command()
def main():
    # Display banner
    console.print(Panel.fit(BANNER, title="Discord Message Bot", border_style="blue"))
    
    setup_config()
    
    while True:
        show_menu()
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3"])
        
        if choice == "1":
            add_message()
        elif choice == "2":
            start_bot()
        elif choice == "3":
            if Confirm.ask("Are you sure you want to exit?", default=False): 
                console.print("[yellow]Goodbye![/yellow]")
                break
        else:
            console.print("[yellow]Invalid choice! Please try again.[/yellow]")

if __name__ == '__main__': 
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/yellow]")