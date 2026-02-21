"""
Searcharr
Sonarr, Radarr & Readarr Telegram Bot
By Todd Roberts
https://github.com/toddrob99/searcharr
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Searcharr Bot
# Passwords can be set via environment variables for security
searcharr_password = os.environ["SEARCHARR_PASSWORD"]  # Used to authenticate as a regular user
searcharr_admin_password = os.getenv("SEARCHARR_ADMIN_PASSWORD", "")  # Used to authenticate as admin
searcharr_language = "en-us"  # yml file in the lang folder
searcharr_start_command_aliases = ["start"]  # Override /start command
searcharr_help_command_aliases = ["help"]  # Override /help command
searcharr_users_command_aliases = ["users"]  # Override /users command

# Telegram
tgram_token = os.environ["TELEGRAM_BOT_TOKEN"]
localhost = "localhost"
port = "9080"
# Sonarr
sonarr_enabled = True
sonarr_url = "http://localhost:8989"  # http://192.168.0.100:8989
sonarr_api_key = os.environ["SONARR_API_KEY"]
sonarr_quality_profile_id = ["Best Quality","Best Quality - Hindi"]  # can be name or id value - include multiple to allow the user to choose
sonarr_add_monitored = True
sonarr_search_on_add = True
sonarr_tag_with_username = True
sonarr_forced_tags = []  # e.g. ["searcharr", "friends-and-family"] - leave empty for none
sonarr_allow_user_to_select_tags = True
sonarr_user_selectable_tags = []  # e.g. ["custom-tag-1", "custom-tag-2"] - leave empty to let user choose from all tags in Sonarr
sonarr_series_command_aliases = ["series"]  # e.g. ["series", "tv", "t"]
sonarr_series_paths = ["/mnt/media/TV"]  # e.g. ["/tv", "/anime"] - can be full path or id value - leave empty to enable all
sonarr_season_monitor_prompt = False  # False - always monitor all seasons; True - prompt user to select from All, First, or Latest season(s)

# Radarr
radarr_enabled = True
radarr_url = "http://localhost:7878"  # http://192.168.0.100:7878
radarr_api_key = os.environ["RADARR_API_KEY"]
radarr_quality_profile_id = ["Best Quality","Best Quality - Hindi"]  # can be name or id value - include multiple to allow the user to choose
radarr_add_monitored = True
radarr_search_on_add = True
radarr_tag_with_username = True
radarr_forced_tags = []  # e.g. ["searcharr", "friends-and-family"] - leave empty for none
radarr_allow_user_to_select_tags = True
radarr_user_selectable_tags = []  # e.g. ["custom-tag-1", "custom-tag-2"] - leave empty to let user choose from all tags in Radarr
radarr_min_availability = "released"  # options: "announced", "inCinemas", "released"
radarr_movie_command_aliases = ["movie"]  # e.g. ["movie", "mv", "m"]
radarr_movie_paths = ["/mnt/media/Movies"]  # e.g. ["/movies", "/other-movies"] - can be full path or id value - leave empty to enable all

# Readarr
readarr_enabled = False
readarr_url = "http://localhost:8787"  # http://192.168.0.100:8787
readarr_api_key = os.environ.get("READARR_API_KEY", "")
readarr_quality_profile_id = ["eBook", "Spoken"]  # can be name or id value - include multiple to allow the user to choose
readarr_metadata_profile_id = ["Standard"]  # can be name or id value - include multiple to allow the user to choose
readarr_add_monitored = True
readarr_search_on_add = True
readarr_tag_with_username = True
readarr_forced_tags = []  # e.g. ["searcharr", "friends-and-family"] - leave empty for none
readarr_allow_user_to_select_tags = True
readarr_user_selectable_tags = []  # e.g. ["custom-tag-1", "custom-tag-2"] - leave empty to let user choose from all tags in Readarr
readarr_book_command_aliases = ["book"]  # e.g. ["book", "bk", "b"]
readarr_book_paths = []  # e.g. ["/books", "/other-books"] - can be full path or id value - leave empty to enable all

#Transmission
status_command_aliases = ["status"]
restart = ['restart']

admin_user_ids = ['1261554730']

# Rate Limiting
rate_limit_requests = 20  # Max requests per window
rate_limit_window = 60  # Window in seconds (1 minute)

# Request History
myrequests_command_aliases = ["myrequests", "requests", "history"]

# Docker Container Management
docker_container_management_enabled = True
docker_container_name = "TransmissionVPN"
docker_container_restart_command = "cd ~/Docker/protonvpn && docker compose up -d"
docker_status_check_interval = 300  # Check every 5 minutes
docker_restart_command_aliases = ["restart_vpn"]
