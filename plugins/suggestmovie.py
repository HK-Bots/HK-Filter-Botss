from pyrogram import Client, filters
import random
from imdb import IMDb

# Create an instance of the IMDb class
ia = IMDb()

# Fetch top 250 movies
top_250_movies = ia.get_top250_movies()

@Client.on_message(filters.command("suggestmovie"))
async def suggest_movie(client, message):
    # Fetch a random movie suggestion from the top 250 list
    random_movie = get_random_movie()
    
    if random_movie:
        # Reply with the movie suggestion
        await message.reply_text(f"🎬 Random Movie Suggestion: {random_movie}")
    else:
        # Reply if failed to fetch movie suggestion
        await message.reply_text("Failed to fetch movie suggestion. Please try again later.")

def get_random_movie():
    try:
        # Select a random movie from the top 250 list
        movie = random.choice(top_250_movies)
        return movie['title']
    except Exception as e:
        print(f"Error fetching movie: {e}")
        return None
