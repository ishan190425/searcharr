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