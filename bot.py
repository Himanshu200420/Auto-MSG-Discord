from http.client import HTTPSConnection 
from sys import stderr 
from json import dumps 
from time import sleep 
import json
import threading
from datetime import datetime

# Load Config
with open('./config.json') as f:
    data = json.load(f)
    for c in data['Config']:
        print('Loading configuration...')
        channelid = c['channelid']
        token = c['token']
        messages = c['messages']

header_data = { 
    "content-type": "application/json", 
    "user-agent": "discordapp.com", 
    "authorization": token
} 
 
def get_connection(): 
    return HTTPSConnection("discordapp.com", 443) 
 
def send_message(conn, channel_id, message_data): 
    try: 
        conn.request("POST", f"/api/v9/channels/{channel_id}/messages", message_data, header_data) 
        resp = conn.getresponse() 
         
        if 199 < resp.status < 300: 
            print(f"Message Sent at {datetime.now().strftime('%H:%M:%S')}")
            pass 
        else: 
            stderr.write(f"HTTP {resp.status}: {resp.reason}\n") 
            pass 
 
    except Exception as e:
        stderr.write(f"Error: {str(e)}\n") 

def message_loop(message, interval):
    while True:
        message_data = { 
            "content": message, 
            "tts": "false"
        } 
        send_message(get_connection(), channelid, dumps(message_data))
        sleep(interval)

def main(): 
    threads = []
    for msg_config in messages:
        message = msg_config['message']
        interval = msg_config['interval']
        print(f"Starting message thread for '{message}' with interval {interval} seconds")
        
        thread = threading.Thread(
            target=message_loop,
            args=(message, interval),
            daemon=True
        )
        threads.append(thread)
        thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        for thread in threads:
            thread.join()
        print("Bot stopped successfully")

if __name__ == '__main__': 
    main()