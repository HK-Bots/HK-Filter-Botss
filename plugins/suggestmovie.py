import random
from pyrogram import Client, filters
import requests

# OMDb API configuration
OMDB_API_KEY = 'http://www.omdbapi.com/?i=tt3896198&apikey=55be1c7d'
OMDB_BASE_URL = 'http://www.omdbapi.com/'

# Function to fetch a random movie suggestion from OMDb API
def get_random_movie():
    params = {
        'apikey': OMDB_API_KEY,
        'type': 'movie',
        'r': 'json',
        'page': random.randint(1, 100)  # Adjust page range as needed
    }
    response = requests.get(OMDB_BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        random_movie = random.choice(data['Search'])
        return random_movie['Title']
    else:
        return None

@Client.on_message(filters.command("suggestmovie"))
async def suggest_movie(client, message):
    # Fetch a random movie suggestion from OMDb API
    random_movie = get_random_movie()
    
    if random_movie:
        # Reply with the movie suggestion
        await message.reply_text(f"🎬 Random Movie Suggestion: {random_movie}")
    else:
        # Reply if failed to fetch movie suggestion
        await message.reply_text("Failed to fetch movie suggestion. Please try again later.")


