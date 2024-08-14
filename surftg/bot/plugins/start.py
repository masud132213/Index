import re
from surftg import LOGGER
from surftg.config import Telegram
from surftg.helper.database import Database
from surftg.helper.file_size import get_readable_file_size
from surftg.helper.index import get_messages
from surftg.helper.media import is_media
# from surftg.helper.tmdb import get_tmdb_info
from surftg.helper.tmdb import TMDBClient
from surftg.bot import StreamBot
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.enums.parse_mode import ParseMode
from asyncio import sleep
import PTN
from os import path as ospath

import requests
db = Database()

session = requests.Session()
client = TMDBClient(session)


@StreamBot.on_message(filters.command('log') & filters.private)
async def start(bot: Client, message: Message):
    try:
        
        path = ospath.abspath('log.txt')
        return await message.reply_document(
        document=path, quote=True, disable_notification=True
        )
    except Exception as e:
        print(f"An error occurred: {e}")


@StreamBot.on_message(filters.command('start') & filters.private)
async def start(bot: Client, message: Message):
    if "file_" in message.text:
        try:
            usr_cmd = message.text.split("_")[-1]
            data = usr_cmd.split("-")
            message_id, chat_id = data[0], f"-{data[1]}"
            file = await bot.get_messages(int(chat_id), int(message_id))
            media = is_media(file)
            await message.reply_cached_media(file_id=media.file_id, caption=f'**{media.file_name}**')
        except Exception as e:
            print(f"An error occurred: {e}")


@StreamBot.on_message(filters.command('tmdb'))
async def tmdb(bot: Client, message: Message):
    channel_id = message.chat.id
    AUTH_CHANNEL = await db.get_variable('auth_channel')
    if AUTH_CHANNEL is None or AUTH_CHANNEL.strip() == '':
        AUTH_CHANNEL = Telegram.AUTH_CHANNEL
    else:
        AUTH_CHANNEL = [channel.strip() for channel in AUTH_CHANNEL.split(",")]
    if str(channel_id) in AUTH_CHANNEL:
        try:
            last_id = message.id
            start_message = (
                "🔄 Please perform this action only once at the beginning of Surf-Tg usage.\n\n"
                "📋 File listing is currently in progress.\n\n"
                "🚫 Please refrain from sending any additional files or indexing other channels until this process completes.\n\n"
                "⏳ Please be patient and wait a few moments."
            )

            wait_msg = await message.reply(text=start_message)
            files = await get_messages(message.chat.id, 1, last_id)
            # await db.add_btgfiles(files)
            await wait_msg.delete()
            done_message = (
                "✅ All your files have been successfully stored in the database. You're all set!\n\n"
                "📁 You don't need to index again unless you make changes to the database."
            )

            await bot.send_message(chat_id=message.chat.id, text=done_message)
        except FloodWait as e:
            LOGGER.info(f"Sleeping for {str(e.value)}s")
            await sleep(e.value)
            await message.reply(text=f"Got Floodwait of {str(e.value)}s",
                                disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply(text="Channel is not in AUTH_CHANNEL")


@StreamBot.on_message(
    filters.channel
    & (
        filters.document
        | filters.video
    )
)
async def file_receive_handler(bot: Client, message: Message):
    channel_id = message.chat.id
    AUTH_CHANNEL = await db.get_variable('auth_channel')
    if AUTH_CHANNEL is None or AUTH_CHANNEL.strip() == '':
        AUTH_CHANNEL = Telegram.AUTH_CHANNEL
    else:
        AUTH_CHANNEL = [channel.strip() for channel in AUTH_CHANNEL.split(",")]
    if str(channel_id) in AUTH_CHANNEL:
        try:
            file = message.video or message.document
            title = file.file_name or message.caption or file.file_id
            print("Original Title:", title)
            title = title.replace("_", " ").replace(".", " ")
            # Remove patterns like @Anime_RTX
            pattern = r'\s*[\[\(\{]?\s*@\w+\s*[\]\)\}]?\s*[-~]?\s*'

            title = re.sub(pattern, '', title).strip()

            # Replace the first period with a space if there are multiple periods
            filename = re.sub(r'\.(?=[^.]*\.)', ' ', title)
            print("After fixing periods:", filename.strip())
            filename = filename.replace('.', ' ')
            filename = re.sub(r'toonflex', ' ', filename, flags=re.IGNORECASE)
            # Get file details
            size = get_readable_file_size(file.file_size)
            file_type = file.mime_type
            msg_id = message.id
            file_hash = file.file_unique_id[:6]
            cid = str(channel_id).replace("-100", "")
            data = PTN.parse(title)
            # Safely extract 'title', 'season', and 'episode' from data dictionary
            title = data.get('title')
            season = data.get('season')
            episode = data.get('episode')
            year = data.get('year')
            resolution = data.get('resolution')
            quality_info = {
                "quality": resolution or (message.video.height if message.video else "other"),
                "size": size,
                "type": file_type,
                "hash": file_hash,
                "cid": int(cid),
                "msg_id": msg_id
            }

            if season and episode:
                media_id = client.find_media_id(
                    title=title, data_type="series", year=year)
                final = client.get_episode_details(
                    tmdb_id=media_id, episode_number=episode, season_number=season)
                series_details = client.get_details(
                    tmdb_id=media_id, data_type="series")
                if final and isinstance(final, dict) and series_details:
                    genres = [genre['name']
                              for genre in series_details.get('genres', [])]
                    india_rating = None
                    for result in series_details['content_ratings']['results']:
                        if result['iso_3166_1'] == 'IN':
                            india_rating = result['rating']
                    series_doc = {
                        "tmdb_id": series_details.get("id"),
                        "title": series_details.get("name"),
                        "rating": series_details.get("vote_average"),
                        "description": series_details.get("overview"),
                        "release_date": series_details.get("first_air_date"),
                        "poster": series_details.get("poster_path"),
                        "backdrop": series_details.get("backdrop_path"),
                        "rate": india_rating,
                        "type": "tv",
                        "genres": genres,
                        "seasons": [{
                            "season_number": season,
                            "episodes": [{
                                "series": series_details.get("name"),
                                "season_number": season,
                                "episode_number": episode,
                                "date": final.get("air_date"),
                                "duration": final.get("runtime"),
                                "title": final.get("name"),
                                "description": final.get("overview"),
                                "poster": final.get("still_path"),
                                "rating": final.get("vote_average"),
                                "qualities": [quality_info]
                            }]
                        }]
                    }
                    await db.update_media(series_doc, "series")
                else:
                    await db.add_tgjson(series_doc)
            else:
                media_id = client.find_media_id(
                    title=title, data_type="movie", year=year)
                final = client.get_details(tmdb_id=media_id, data_type="movie")
                if final and isinstance(final, dict):
                    genres = [genre['name']
                              for genre in final.get('genres', [])]
                    movie_doc = {
                        "tmdb_id": final.get("id"),
                        "title": final.get("title"),
                        "rating": final.get("vote_average"),
                        "description": final.get("overview"),
                        "runtime": final.get("runtime"),
                        "release_date": final.get("release_date"),
                        "poster": final.get("poster_path"),
                        "backdrop": final.get("backdrop_path"),
                        "genres": genres,
                        "type": "movie",
                        "qualities": [quality_info]
                    }
                    await db.update_media(movie_doc, "movie")
                else:
                    await db.add_tgjson(movie_doc)

        except FloodWait as e:
            print(f"Sleeping for {str(e.value)}s")
            await sleep(e.value)
            await message.reply(text=f"Got Floodwait of {str(e.value)}s",
                                disable_web_page_preview=True, parse_mode='markdown')
    else:
        await message.reply(text="Channel is not in AUTH_CHANNEL")
