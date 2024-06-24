import logging
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request
import os

# logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

ANILIST_API_URL = "https://graphql.anilist.co"

# st command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.message.from_user.first_name}, Welcome to Anime info.\n"
                                    f"🔥 Get details about animes 💯 and 🍿 Enjoy it.")
    await update.message.reply_text("👇 Enter Anime Name 👇")

# for fetch anime details from AniList API
def get_anime_details(anime_name: str) -> dict:
    query = '''
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            id
            title {
                romaji
            }
            episodes
            genres
            season
            seasonYear
            description(asHtml: false)
            siteUrl
        }
    }
    '''
    variables = {
        'search': anime_name
    }
    logger.info(f"Searching for anime with name: {anime_name}")
    response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables})
    logger.info(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Response JSON: {data}")
        if data.get('data') and data['data'].get('Media'):
            media = data['data']['Media']
            details = {
                'title': media['title']['romaji'],
                'episodes': media['episodes'],
                'genres': ', '.join(media['genres']),
                'season': media['season'],
                'season_year': media['seasonYear'],
                'description': clean_description(media['description']),
                'url': media['siteUrl']
            }
            return details
        else:
            return None
    else:
        return None

# clr description text
def clean_description(description: str) -> str:
    # Remove HTML tags
    clean = re.compile('<.*?>')
    return re.sub(clean, '', description)

# time to finish particular anime
def calculate_watch_time(episodes: int) -> str:
    if episodes:
        minutes_per_episode = 25  # Assuming an average of 25 minutes per episode
        total_minutes = episodes * minutes_per_episode
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f"{hours} hours and {minutes} minutes"
        else:
            return f"{minutes} minutes"
    else:
        return "N/A"

# msg handling
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    anime_name = update.message.text
    await update.message.reply_text(f"🔍 Searching for anime: {anime_name}...")
    details = get_anime_details(anime_name)
    
    if details:
        # Calculation approximate time
        episodes = details['episodes'] if details['episodes'] else 0
        watch_time = calculate_watch_time(episodes)
        
        
        message_text = (
            f"🌟 **Anime**: {details['title']}\n"
            f"📺 **Episodes**: {details['episodes'] if details['episodes'] else 'N/A'}\n"
            f"🎭 **Genres**: {details['genres']}\n"
            f"📅 **Season**: {details['season']} {details['season_year']}\n"
            f"⏳ **Approx. Time to Finish**: {watch_time}\n\n"
            f"📝 **Description**:\n{details['description']}\n\n"
            f"🔗 **Watch Here**: [HiAnime](https://hianime.to/search?keyword={anime_name})"
        )
        await update.message.reply_text(message_text, parse_mode='Markdown')
        
        # addition info url
        if details['url']:
            await update.message.reply_text(f"🔗 **More Info**: [AniList]({details['url']})")
    else:
        await update.message.reply_text("⚠️ Anime not found.")

# error handling
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    # tg token
    application = Application.builder().token("ADD YOUR TG BOT TOKEN HERE!!").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error)
    application.run_polling()

if __name__ == '__main__':
    main()

# Dummy Flask 
app = Flask(__name__)

@app.route('/')
def home():
    return "This is a dummy web service for the Telegram bot."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
