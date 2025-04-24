import telegram
from telegram.ext import Updater, CommandHandler
import transmissionrpc
import settings
import re
import subprocess
import time
from log import set_up_logger

# Set up the Telegram bot token
TOKEN = settings.tgram_token

# Set up the Transmission connection details
TRANSMISSION_HOST = settings.localhost
TRANSMISSION_PORT = settings.port

class StatusFinder:
    def __init__(self):
        self.logger = set_up_logger("searcharr.docker", False, False)
        self.last_check_time = 0
        self.last_status = None
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
    
    def restart(self, update=None, context=None):
        """Restart the Docker container.
        
        Can be called directly or as a command handler.
        
        Args:
            update: Telegram update object (optional)
            context: Telegram context object (optional)
        
        Returns:
            bool: True if restart was successful, False otherwise
        """
        self.logger.info("Attempting to restart container")
        
        try:
            # Check if user is authenticated and is admin if called as command
            if update and not self._is_admin_user(update):
                update.message.reply_text("You need admin privileges to restart containers.")
                return False
            
            # Execute the restart command
            restart_command = getattr(settings, "docker_container_restart_command",
                                     "cd ~/Docker/protonvpn && docker compose up -d")
            
            process = subprocess.run(
                restart_command,
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            success = process.returncode == 0
            
            if success:
                self.logger.info("Successfully restarted container")
                if update:
                    update.message.reply_text("Container restarted successfully.")
            else:
                self.logger.error(f"Failed to restart container: {process.stderr}")
                if update:
                    update.message.reply_text(f"Failed to restart container. Error: {process.stderr}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error restarting container: {e}")
            if update:
                update.message.reply_text(f"Error restarting container: {e}")
            return False
    
    def check_container_status(self):
        """Check if the container is running.
        
        Returns:
            bool: True if the container is running, False otherwise
        """
        container_name = getattr(settings, "docker_container_name", "protonvpn")
        self.logger.debug(f"Checking status of container: {container_name}")
        
        try:
            # Run docker ps command to check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # If the container name is in the output, it's running
            is_running = container_name in result.stdout
            
            # Log status change
            if self.last_status is not None and is_running != self.last_status:
                self.logger.info(f"Container {container_name} status changed: {'running' if is_running else 'stopped'}")
            
            self.last_status = is_running
            self.last_check_time = time.time()
            
            return is_running
        except Exception as e:
            self.logger.error(f"Error checking container status: {e}")
            return None
    
    def notify_if_container_down(self, bot):
        """Check container status and notify admins if it's down.
        
        Args:
            bot: Telegram bot instance
        """
        # Only check if enough time has passed since last check
        current_time = time.time()
        check_interval = getattr(settings, "docker_status_check_interval", 300)  # Default: 5 minutes
        
        if (current_time - self.last_check_time) < check_interval:
            return
        
        # Check container status
        is_running = self.check_container_status()
        
        # If container is down, notify admins
        if is_running is False:  # Explicitly check for False (not None)
            self.logger.warning(f"Container {getattr(settings, 'docker_container_name', 'protonvpn')} is down!")
            
            # Get admin user IDs from settings
            admin_ids = getattr(settings, "admin_user_ids", [])
            
            # Send notification to each admin
            for admin_id in admin_ids:
                try:
                    bot.send_message(
                        chat_id=admin_id,
                        text=f"⚠️ Container {getattr(settings, 'docker_container_name', 'protonvpn')} is down! Use /{getattr(settings, 'docker_restart_command_aliases', ['restart_vpn'])[0]} to restart it.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to send notification to admin {admin_id}: {e}")
    
    def _is_admin_user(self, update):
        """Check if the user is an admin.
        
        Args:
            update: Telegram update object
            
        Returns:
            bool: True if user is admin, False otherwise
        """
        user_id = str(update.message.from_user.id)
        admin_ids = getattr(settings, "admin_user_ids", ['1261554730'])
        
        return user_id in admin_ids
