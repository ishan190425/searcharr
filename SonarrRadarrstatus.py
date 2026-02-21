from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import settings
# Replace with your actual tokens and URLs
TELEGRAM_TOKEN = settings.tgram_token
SONARR_API_KEY = settings.sonarr_api_key
RADARR_API_KEY = settings.radarr_api_key
SONARR_URL = settings.sonarr_url
RADARR_URL = settings.radarr_url

async def statusMovie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    radarr_downloads = get_radarr_downloads()
    message = format_status_message(radarr_downloads)
    await update.message.reply_text(message, parse_mode='HTML')

async def statusShow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sonarr_downloads = get_sonarr_downloads()
    message = format_status_message(sonarr_downloads)
    await update.message.reply_text(message, parse_mode='HTML')

def get_sonarr_downloads():
    url = f'{SONARR_URL}/api/v3/queue?'
    params = {'apikey': SONARR_API_KEY}
    response = requests.get(url, params=params)
    return response.json()

def get_radarr_downloads():
    url = f'{RADARR_URL}/api/v3/queue?'
    params = {'apikey': RADARR_API_KEY}
    response = requests.get(url, params=params)
    return response.json()

def format_status_message(radarr_downloads) -> str:
    # Extract the relevant information
    message = ""
    for record in radarr_downloads['records']:
        movie_title = record['title']
        size_total = record['size']
        size_left = record['sizeleft']
        # Calculate completion percentage
        completion_percentage = round(((size_total - size_left) / size_total) * 100,2)
        message+= f"{movie_title} ------ {completion_percentage}%\n\n"

    return message


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("statusMovie", statusMovie))
    application.add_handler(CommandHandler("statusShows", statusShow))

    application.run_polling()

if __name__ == '__main__':
    main()
