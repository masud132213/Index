from os.path import splitext
import re

import requests
from surftg.config import Telegram
from surftg.helper.database import Database
from surftg.bot import StreamBot, UserBot
from surftg.helper.file_size import get_readable_file_size
from surftg.helper.cache import get_cache, save_cache
from asyncio import gather
from datetime import datetime
import PTN
from surftg.helper.tmdb import TMDBClient
db = Database()
session = requests.Session()
client = TMDBClient(session)

async def fetch_message(chat_id, message_id):
    try:
        message = await StreamBot.get_messages(chat_id, message_id)
        return message
    except Exception as e:
        return None


async def get_messages(chat_id, first_message_id, last_message_id, batch_size=50):
    current_message_id = first_message_id
    while current_message_id <= last_message_id:
        batch_message_ids = list(range(current_message_id, min(
            current_message_id + batch_size, last_message_id + 1)))
        tasks = [fetch_message(chat_id, message_id)
                 for message_id in batch_message_ids]
        batch_messages = await gather(*tasks)
        for message in batch_messages:
            if message:
                if file := message.video or message.document:
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
                    cid = str(chat_id).replace("-100", "")
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
        current_message_id += batch_size



async def get_files(chat_id, page=1):
    # if Telegram.SESSION_STRING == '':
    #     return await db.list_tgfiles(id=chat_id, page=page)
    # if cache := get_cache(chat_id, int(page)):
    #     return cache
    posts = []
    print(chat_id)
    async for post in UserBot.get_chat_history(chat_id=int(chat_id), limit=50, offset=(int(page) - 1) * 50):
        file = post.video or post.document
        if not file:
            continue
        title = file.file_name or post.caption or file.file_id
        title, _ = splitext(title)
        title = re.sub(r'[.,|_\',]', ' ', title)
        posts.append({"msg_id": post.id, "title": title,
                      "hash": file.file_unique_id[:6], "size": get_readable_file_size(file.file_size), "type": file.mime_type})
    # save_cache(chat_id, {"posts": posts}, page)
    return posts


async def get_list(page=1, type=""):
    return await db.list_index(page=page)


async def posts_file(posts, chat_id):
    phtml = """
            <div class="col">

                    <div class="card text-white bg-primary mb-3">
                        <input type="checkbox" class="admin-only form-check-input position-absolute top-0 end-0 m-2"
                            onchange="checkSendButton()" id="selectCheckbox"
                            data-id="{id}|{hash}|{title}|{size}|{type}|{img}">
                        <img src="https://cdn.jsdelivr.net/gh/weebzone/weebzone/data/Surf-TG/src/loading.gif" class="lzy_img card-img-top rounded-top"
                            data-src="{img}" alt="{title}">
                        <a href="/watch/{chat_id}?id={id}&hash={hash}">
                        <div class="card-body p-1">
                            <h6 class="card-title">{title}</h6>
                            <span class="badge bg-warning">{type}</span>
                            <span class="badge bg-info">{size}</span>
                        </div>
                        </a>
                    </div>

            </div>
"""
    return ''.join(phtml.format(chat_id=str(chat_id).replace("-100", ""), id=post["msg_id"], img=f"/api/thumb/{chat_id}?id={post['msg_id']}", title=post["title"], hash=post["hash"], size=post['size'], type=post['type']) for post in posts)


async def posts_tmdb(posts):
    phtml = """
            <div class="movie-card">
            <a href="/tmdb/{type}/{id}">
                <div class="card-head">
                    <img src="https://cdn.jsdelivr.net/gh/weebzone/weebzone/data/Surf-TG/src/loading.gif" class="card-img lzy_img" data-src="{img}" alt="{title}">
                    <div class="card-overlay">
                        <div class="play">
                            <ion-icon name="play-circle-outline" role="img" class="md hydrated"
                                aria-label="play circle outline" style="color: #f11932d2;"></ion-icon>
                        </div>
                    </div>
                </div>
                <div class="mt-1">
                    <h6 class="card-title">{title}</h6>
                    <div class="card-info">
                        <span class="year">{year}</span>
                    </div>
                </div>
            </a>
            </div>
"""

    return ''.join(phtml.format(
    id=post["tmdb_id"],
    img=f"https://image.tmdb.org/t/p/w500{post['poster']}",
    title=post["title"],
    year=(datetime.strptime(post["release_date"], "%Y-%m-%d").year 
          if len(post["release_date"]) == 10 
          else "Unknown"),
    type=post["type"]
) for post in posts)
