import telegram
from telegram.ext import Updater, CommandHandler
import transmissionrpc
import settings
import re
import subprocess
# Set up the Telegram bot token
TOKEN = settings.tgram_token

# Set up the Transmission connection details
TRANSMISSION_HOST = settings.localhost
TRANSMISSION_PORT = settings.port
class StatusFinder:
    def is_name_in_title(self,name, title):
        # Escape special characters in the name for regex
        escaped_name = re.escape(name)
        
        # Construct a regex pattern to match variations of name in title
        pattern = r'\b' + escaped_name.replace(r'\ ', r'[\s._-]*') + r'\b'
        
        # Check if the pattern is found in the title
        return bool(re.search(pattern, title, flags=re.IGNORECASE))

    def progress_bar(self,percentage):
        filled_blocks = int(percentage // 5)
        empty_blocks = int((100 - percentage) // 5)
        progress_bar_temp = '█' * filled_blocks + '░' * empty_blocks
        return progress_bar_temp

    # Function to handle the /queue command
    def queue(self,update, context):
        
        message = ""
        title = update.message['text'].split("/status")[1].strip()
        # Create a Transmission client
        tc = transmissionrpc.Client(TRANSMISSION_HOST, port=TRANSMISSION_PORT)
        torrents = tc.get_torrents()
        torrents = sorted(torrents, key=lambda x: x.progress, reverse=True)
        torrentsMatched = 1
        # print(progress_bar(3))
        for torrent in torrents:
            if not self.is_name_in_title(title,torrent.name):
                continue
            progress = self.progress_bar(torrent.progress)
            message += f"\n{torrentsMatched}) Name: {torrent.name}\nStatus: {torrent.status}\nProgress: {progress} - {round(torrent.progress,2)}%\n\n"
            torrentsMatched += 1
            if torrentsMatched > 10:
                break        
        # Split message into chunks
        message_chunks = [message[i:i + 4000] for i in range(0, len(message), 4000)]
        
        # Send message chunks
        if not message_chunks:
            update.message.reply_text(f"{title} was not found...")
            return
        else:
            for chunk in message_chunks:
                update.message.reply_text(chunk)
            return
    
    def restart(self):
        subprocess.run(["docker", "compose", "up", "-d"], cwd="~/Docker/protonvpn", check=True)
