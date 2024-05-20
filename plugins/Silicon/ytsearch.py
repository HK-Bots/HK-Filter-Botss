from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtube_search import YoutubeSearch


@Client.on_message(filters.command(["ytsearch"]))
async def ytsearch(_, message: Message):
    try:
        await message.delete()
    except:
        pass
    try:
        if len(message.command) < 2:
            return await message.reply_text("» ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ sᴇᴀʀᴄʜ ʙᴀʙʏ !")
        query = message.text.split(None, 1)[1]
        m = await message.reply_text("🔎")
        results = YoutubeSearch(query, max_results=4).to_dict()
        i = 0
        text = ""
        while i < 4:
            text += f"✨ ᴛɪᴛʟᴇ : {results[i]['title']}\n"
            text += f"⏱ ᴅᴜʀᴀᴛɪᴏɴ : `{results[i]['duration']}`\n"
            text += f"👀 ᴠɪᴇᴡs : `{results[i]['views']}`\n"
            text += f"📣 ᴄʜᴀɴɴᴇʟ : {results[i]['channel']}\n"
            text += f"🔗 ʟɪɴᴋ : https://youtube.com{results[i]['url_suffix']}\n\n"
            i += 1
        key = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "• ᴜᴘᴅᴀᴛᴇs •", url="https://t.me/main_movie_hub",
                    ),
                ]
            ]
        )
        await m.edit_text(
            text=text,
            reply_markup=key,
            disable_web_page_preview=True,
        )
    except Exception as e:
        await message.reply_text(str(e))
