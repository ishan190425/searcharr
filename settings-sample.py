"""
Searcharr
Sonarr, Radarr & Readarr Telegram Bot
Sample Settings File
By Todd Roberts
https://github.com/toddrob99/searcharr
"""

# Searcharr Bot
searcharr_password = "password"  # Password users will use to authenticate with the bot
searcharr_admin_password = "admin_password"  # Password for admin access
searcharr_language = "en-us"  # Language for bot messages (see lang/ directory for available languages)
searcharr_start_command_aliases = ["start"]  # Command aliases for the start command
searcharr_help_command_aliases = ["help"]  # Command aliases for the help command
searcharr_users_command_aliases = ["users"]  # Command aliases for the users command

# Telegram Bot
tgram_token = "YOUR_TELEGRAM_BOT_TOKEN"  # Get from BotFather

# Sonarr
sonarr_enabled = True  # Set to False to disable Sonarr functionality
sonarr_url = "http://localhost:8989"  # URL to your Sonarr instance
sonarr_api_key = "YOUR_SONARR_API_KEY"  # Get from Sonarr > Settings > General > API Key
sonarr_quality_profile_id = [1]  # Quality profile ID(s) to use (can be name or ID)
sonarr_series_paths = ["/path/to/tv"]  # Path(s) to store series (can be path or ID)
sonarr_tag_with_username = True  # Tag series with the username of the user who added it
sonarr_season_monitor_prompt = False  # Prompt user to choose which seasons to monitor
sonarr_forced_tags = []  # Tags to add to all series
sonarr_allow_user_to_select_tags = False  # Allow users to select tags when adding series
sonarr_user_selectable_tags = []  # Tags users can select (empty list = all tags)
sonarr_series_command_aliases = ["series", "tv"]  # Command aliases for the series command

# Radarr
radarr_enabled = True  # Set to False to disable Radarr functionality
radarr_url = "http://localhost:7878"  # URL to your Radarr instance
radarr_api_key = "YOUR_RADARR_API_KEY"  # Get from Radarr > Settings > General > API Key
radarr_quality_profile_id = [1]  # Quality profile ID(s) to use (can be name or ID)
radarr_movie_paths = ["/path/to/movies"]  # Path(s) to store movies (can be path or ID)
radarr_tag_with_username = True  # Tag movies with the username of the user who added it
radarr_min_availability = "released"  # Minimum availability for movies (released, announced, inCinema)
radarr_forced_tags = []  # Tags to add to all movies
radarr_allow_user_to_select_tags = True  # Allow users to select tags when adding movies
radarr_user_selectable_tags = []  # Tags users can select (empty list = all tags)
radarr_movie_command_aliases = ["movie", "mv"]  # Command aliases for the movie command

# Readarr
readarr_enabled = True  # Set to False to disable Readarr functionality
readarr_url = "http://localhost:8787"  # URL to your Readarr instance
readarr_api_key = "YOUR_READARR_API_KEY"  # Get from Readarr > Settings > General > API Key
readarr_quality_profile_id = [1]  # Quality profile ID(s) to use (can be name or ID)
readarr_metadata_profile_id = [1]  # Metadata profile ID(s) to use (can be name or ID)
readarr_book_paths = ["/path/to/books"]  # Path(s) to store books (can be path or ID)
readarr_tag_with_username = True  # Tag books with the username of the user who added it
readarr_forced_tags = []  # Tags to add to all books
readarr_allow_user_to_select_tags = True  # Allow users to select tags when adding books
readarr_user_selectable_tags = []  # Tags users can select (empty list = all tags)
readarr_book_command_aliases = ["book", "bk"]  # Command aliases for the book command

# Transmission
localhost = "localhost"  # Transmission host
port = 9091  # Transmission port
status_command_aliases = ["status"]  # Command aliases for the status command

# Docker Container Management
docker_container_management_enabled = True  # Enable Docker container management
docker_container_name = "protonvpn"  # Name of the Docker container to monitor
docker_container_restart_command = "cd ~/Docker/protonvpn && docker compose up -d"  # Command to restart the container
docker_status_check_interval = 300  # Check container status every 5 minutes (in seconds)
docker_restart_command_aliases = ["restart_vpn"]  # Command aliases for the restart command
restart = ["restart"]  # Legacy setting for restart command aliases
admin_user_ids = [123456789]  # Telegram user IDs of admins to notify when container is down