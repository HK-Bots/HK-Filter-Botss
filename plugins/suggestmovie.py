from pyrogram import Client, filters
import random
from imdb import IMDb

# Create an instance of the IMDb class
ia = IMDb()

@Client.on_message(filters.command("suggestmovie"))
async def suggest_movie(client, message):
    # Fetch a random movie suggestion from IMDb
    random_movie = get_random_movie()
    
    if random_movie:
        # Reply with the movie suggestion
        await message.reply_text(f"🎬 Random Movie Suggestion: {random_movie}")
    else:
        # Reply if failed to fetch movie suggestion
        await message.reply_text("Failed to fetch movie suggestion. Please try again later.")

def get_random_movie():
    try:
        # Get a random movie
        movie_id = random.randint(1, 1000000)  # Adjust the range as needed
        movie = ia.get_movie(movie_id)
        return movie['title']
    except Exception as e:
        print(f"Error fetching movie: {e}")
        return None

# Run the client
