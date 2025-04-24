# Docker Container Management for Searcharr

This document outlines the implementation plan for adding Docker container management features to Searcharr.

## Features to Implement

1. Check status of Docker container (ProtonVPN)
2. Prompt user to restart container if it stops
3. Add a restart command to restart the container

## Implementation Details

### 1. Create a Docker Manager Module

Create a new file `docker_manager.py` with the following content:

```python
"""
Searcharr
Docker Container Management Module
"""
import subprocess
import time
import os
from log import set_up_logger


class DockerManager:
    def __init__(self, container_name, restart_command, verbose=False):
        """Initialize the Docker Manager.
        
        Args:
            container_name (str): Name of the Docker container to manage
            restart_command (str): Command to restart the container
            verbose (bool): Enable verbose logging
        """
        self.logger = set_up_logger("searcharr.docker", verbose, False)
        self.logger.debug("Docker Manager logging started!")
        self.container_name = container_name
        self.restart_command = restart_command
        self.last_status = None
        self.last_check_time = 0
    
    def check_container_status(self):
        """Check if the container is running.
        
        Returns:
            bool: True if the container is running, False otherwise
        """
        self.logger.debug(f"Checking status of container: {self.container_name}")
        try:
            # Run docker ps command to check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # If the container name is in the output, it's running
            is_running = self.container_name in result.stdout
            
            # Log status change
            if self.last_status is not None and is_running != self.last_status:
                self.logger.info(f"Container {self.container_name} status changed: {'running' if is_running else 'stopped'}")
            
            self.last_status = is_running
            self.last_check_time = time.time()
            
            return is_running
        except Exception as e:
            self.logger.error(f"Error checking container status: {e}")
            return None
    
    def restart_container(self):
        """Restart the Docker container.
        
        Returns:
            bool: True if restart was successful, False otherwise
        """
        self.logger.info(f"Attempting to restart container: {self.container_name}")
        try:
            # Execute the restart command
            process = subprocess.run(
                self.restart_command,
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                self.logger.info(f"Successfully restarted container: {self.container_name}")
                return True
            else:
                self.logger.error(f"Failed to restart container: {process.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error restarting container: {e}")
            return False
    
    def get_container_logs(self, lines=10):
        """Get the most recent logs from the container.
        
        Args:
            lines (int): Number of log lines to retrieve
            
        Returns:
            str: Container logs or error message
        """
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), self.container_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error retrieving logs: {result.stderr}"
        except Exception as e:
            return f"Exception retrieving logs: {e}"
```

### 2. Update Settings

Add the following settings to your `settings.py` file:

```python
# Docker Container Management
docker_container_management_enabled = True
docker_container_name = "protonvpn"  # Name of the container to monitor
docker_container_restart_command = "cd ~/Docker/protonvpn && docker compose up -d"
docker_status_check_interval = 300  # Check status every 5 minutes (in seconds)
docker_restart_command_aliases = ["restart_vpn"]  # Command aliases
```

### 3. Integrate with Searcharr

Modify `searcharr.py` to integrate the Docker manager:

#### 3.1. Import the Docker Manager

Add this import at the top of the file:

```python
from docker_manager import DockerManager
```

#### 3.2. Initialize the Docker Manager in the Searcharr class

Add this to the `__init__` method of the Searcharr class:

```python
# Initialize Docker Manager if enabled
if hasattr(settings, "docker_container_management_enabled") and settings.docker_container_management_enabled:
    self.docker_manager = DockerManager(
        container_name=settings.docker_container_name,
        restart_command=settings.docker_container_restart_command,
        verbose=args.verbose
    )
    # Check container status on startup
    is_running = self.docker_manager.check_container_status()
    logger.info(f"Docker container '{settings.docker_container_name}' status: {'running' if is_running else 'stopped'}")
else:
    self.docker_manager = None
    logger.warning(
        "Docker container management is not enabled. If you want to use this feature, "
        "please add docker_container_management_enabled=True to settings.py."
    )
```

#### 3.3. Add Command Handler for Restarting Container

Add this method to the Searcharr class:

```python
def cmd_restart_container(self, update, context):
    logger.debug(f"Received restart container cmd from [{update.message.from_user.username}]")
    
    # Check if user is authenticated and is admin
    if not self._authenticated(update.message.from_user.id):
        update.message.reply_text(
            self._xlate(
                "auth_required",
                commands=" OR ".join(
                    [
                        f"`/{c} <{self._xlate('password')}>`"
                        for c in settings.searcharr_start_command_aliases
                    ]
                ),
            )
        )
        return
    
    # Check if user is admin
    user = self._get_con_cur()[1].execute(
        "SELECT admin FROM users WHERE id = ?", (update.message.from_user.id,)
    ).fetchone()
    
    if not user or not user[0]:
        update.message.reply_text("You need admin privileges to restart containers.")
        return
    
    # Check if Docker manager is enabled
    if not self.docker_manager:
        update.message.reply_text("Docker container management is not enabled.")
        return
    
    # Send message that we're restarting the container
    update.message.reply_text(f"Attempting to restart container: {settings.docker_container_name}...")
    
    # Restart the container
    success = self.docker_manager.restart_container()
    
    # Send result message
    if success:
        update.message.reply_text(f"Container {settings.docker_container_name} restarted successfully.")
    else:
        update.message.reply_text(f"Failed to restart container {settings.docker_container_name}. Check logs for details.")
```

#### 3.4. Add Periodic Status Checking

Add this method to the Searcharr class:

```python
def _check_container_status(self):
    """Periodically check container status and notify admins if it's down."""
    if not self.docker_manager:
        return
    
    # Only check if enough time has passed since last check
    current_time = time.time()
    if (current_time - self.docker_manager.last_check_time) < settings.docker_status_check_interval:
        return
    
    # Check container status
    is_running = self.docker_manager.check_container_status()
    
    # If container is down, notify admins
    if is_running is False:  # Explicitly check for False (not None)
        logger.warning(f"Container {settings.docker_container_name} is down!")
        
        # Get all admin users
        admins = self._get_users(admin=True)
        
        # Send notification to each admin
        for admin in admins:
            try:
                self.updater.bot.send_message(
                    chat_id=admin["id"],
                    text=f"⚠️ Container {settings.docker_container_name} is down! Use /{settings.docker_restart_command_aliases[0]} to restart it.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin['username']}: {e}")
```

#### 3.5. Register Command Handlers

Add this to the `run` method of the Searcharr class:

```python
# Register Docker container management commands if enabled
if self.docker_manager:
    for command in settings.docker_restart_command_aliases:
        self.dispatcher.add_handler(CommandHandler(command, self.cmd_restart_container))
```

#### 3.6. Add Periodic Status Checking to the Main Loop

Add this to the `run` method of the Searcharr class, inside the `while True` loop:

```python
# Check container status periodically
if self.docker_manager:
    self._check_container_status()
```

### 4. Update Requirements

Add any necessary dependencies to `requirements.txt`:

```
# No new dependencies needed for Docker management
```

## Testing

1. Test container status checking:
   - Start the container and verify it's detected as running
   - Stop the container and verify it's detected as stopped

2. Test restart functionality:
   - Stop the container
   - Use the restart command
   - Verify the container is running again

3. Test notifications:
   - Stop the container
   - Wait for the status check interval
   - Verify that admin users receive notifications

## Notes

- The Docker commands require that the user running Searcharr has permission to execute Docker commands
- The restart command uses shell=True, which can be a security risk if user input is not properly sanitized
- Consider adding more robust error handling and logging for production use