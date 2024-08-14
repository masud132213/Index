from pymongo import DESCENDING, MongoClient, errors
from bson import ObjectId
from surftg.config import Telegram


class Database:
    def __init__(self):
        MONGODB_URI = Telegram.DATABASE_URL
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client["surftg"]
        self.collection = self.db["playlist"]
        self.config = self.db["config"]
        self.files = self.db["files"]
        self.tmdb = self.db["tmdb"]

    async def create_folder(self, parent_id, folder_name, thumbnail):
        folder = {"parent_folder": parent_id, "name": folder_name,
                  "thumbnail": thumbnail, "type": "folder"}
        self.collection.insert_one(folder)

    def delete(self, document_id):
        try:
            has_child_documents = self.collection.count_documents(
                {'parent_folder': document_id}) > 0
            if has_child_documents:
                result = self.collection.delete_many(
                    {'parent_folder': document_id})
            result = self.collection.delete_one({'_id': ObjectId(document_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f'An error occurred: {e}')
            return False

    async def edit(self, id, name, thumbnail):
        result = self.collection.update_one({"_id": ObjectId(id)}, {
            "$set": {"name": name, "thumbnail": thumbnail}})
        return result.modified_count > 0

    async def search_DbFolder(self, query):
        words = query.split()
        regex_query = {'$regex': '.*' +
                       '.*'.join(words) + '.*', '$options': 'i'}
        myquery = {'type': 'folder', 'name': regex_query}
        mydoc = self.collection.find(myquery).sort('_id', DESCENDING)
        return [{'_id': str(x['_id']), 'name': x['name']} for x in mydoc]

    async def add_json(self, data):
        result = self.collection.insert_many(data)






    async def get_Dbfolder(self, parent_id="root", page=1, per_page=50):
        query = {"parent_folder": parent_id, "type": "folder"} if parent_id != 'root' else {
            "parent_folder": 'root', "type": "folder"}
        if parent_id != 'root':
            offset = (int(page) - 1) * per_page
            return list(self.collection.find(query).skip(offset).limit(per_page))
        else:
            return list(self.collection.find(query))

    async def get_dbFiles(self, parent_id=None, page=1, per_page=50):
        query = {"parent_folder": parent_id, "type": "file"}
        offset = (int(page) - 1) * per_page
        return list(self.collection.find(query).sort(
            'file_id', DESCENDING).skip(offset).limit(per_page))

    async def get_info(self, id):
        query = {'_id': ObjectId(id)}
        if document := self.collection.find_one(query):
            return document.get('name', None)
        else:
            return None



    async def search_dbfiles(self, id, query, page=1, per_page=50):
        words = query.split()
        regex_query = {'$regex': '.*' +
                       '.*'.join(words) + '.*', '$options': 'i'}
        query = {'type': 'file', 'parent_folder': id, 'name': regex_query}
        offset = (int(page) - 1) * per_page
        mydoc = self.collection.find(query).sort(
            'file_id', DESCENDING).skip(offset).limit(per_page)
        return list(mydoc)

    async def update_config(self, theme, auth_channel):
        bot_id = Telegram.BOT_TOKEN.split(":", 1)[0]
        config = self.config.find_one({"_id": bot_id})
        if config is None:
            result = self.config.insert_one(
                {"_id": bot_id, "theme": theme, "auth_channel": auth_channel})
            return result.inserted_id is not None
        else:
            result = self.config.update_one({"_id": bot_id}, {
                "$set": {"theme": theme, "auth_channel": auth_channel}})
            return result.modified_count > 0

    async def get_variable(self, key):
        bot_id = Telegram.BOT_TOKEN.split(":", 1)[0]
        config = self.config.find_one({"_id": bot_id})
        return config.get(key) if config is not None else None

    async def list_tgfiles(self, id, page=1, per_page=50):
        query = {'chat_id': id}
        offset = (int(page) - 1) * per_page
        mydoc = self.files.find(query).sort(
            'msg_id', DESCENDING).skip(offset).limit(per_page)
        return list(mydoc)

    async def add_tgfiles(self, chat_id, file_id, hash, name, size, file_type):
        if fetch_old := self.files.find_one({"chat_id": chat_id, "hash": hash}):
            return
        file = {"chat_id": chat_id, "msg_id": file_id,
                "hash": hash, "title": name, "size": size, "type": file_type}
        self.files.insert_one(file)

    async def search_tgfiles(self, id, query, page=1, per_page=50):
        words = query.split()
        regex_query = {'$regex': '.*' +
                       '.*'.join(words) + '.*', '$options': 'i'}
        query = {'chat_id': id, 'title': regex_query}
        offset = (int(page) - 1) * per_page
        mydoc = self.files.find(query).sort(
            'msg_id', DESCENDING).skip(offset).limit(per_page)
        return list(mydoc)

    async def add_btgfiles(self, data):
        result = self.files.insert_many(data)

# ----------------------------tmdb Database----------------------------------
    async def fetch_home(self):
        latest = self.tmdb.find({'tmdb_id': {'$ne': None}}).sort('_id', DESCENDING).limit(20)
        movies = self.tmdb.find({'type': 'movie', 'tmdb_id': {'$ne': None}}).sort('rating', DESCENDING).limit(20)
        series = self.tmdb.find({'type': 'tv', 'tmdb_id': {'$ne': None}}).sort('rating', DESCENDING).limit(20)
        return {'latest': list(latest), 'movies': list(movies), 'tvshows': list(series)}
    
    async def list_index(self, page=1, type="", per_page=50):
        offset = (int(page) - 1) * per_page
        if type == "latest":
            total_count = self.tmdb.count_documents({})
            mydoc = self.tmdb.find({'tmdb_id': {'$ne': None}}).sort('_id', DESCENDING).skip(offset).limit(per_page)
        elif type == "Movies":
            total_count = self.tmdb.count_documents({'type': 'movie'})
            mydoc = self.tmdb.find({'type': 'movie', 'tmdb_id': {'$ne': None}}).sort('_id', DESCENDING).skip(offset).limit(per_page)
        elif type == "tvshow":
            total_count = self.tmdb.count_documents({'type': 'tv'})
            mydoc = self.tmdb.find({'type': 'tv', 'tmdb_id': {'$ne': None}}).sort('_id', DESCENDING).skip(offset).limit(per_page)
        return list(mydoc), total_count



    async def watch_tmdb(self, id):
        return self.tmdb.find_one({"tmdb_id": id})

    async def search_listfiles(self, query, page=1, per_page=50):
        words = query.split()
        regex_query = {'$regex': '.*' + '.*'.join(words) + '.*', '$options': 'i'}
        query = {'title': regex_query}
        offset = (int(page) - 1) * per_page

        total_count = self.tmdb.count_documents(query)

        mydoc = self.tmdb.find(query).sort('msg_id', DESCENDING).skip(offset).limit(per_page)
        return list(mydoc), total_count



    async def add_tgjson(self, data):
        try:
            if data.get('tmdb_id') == "null":
                return
            result = self.tmdb.insert_one(data)
            tmdb_id = data.get('tmdb_id')
            print(f"Inserted new TMDB entry with ID {tmdb_id}")
        except errors.DuplicateKeyError:
            print(f"TMDB entry with ID {data.get('tmdb_id')} already exists")

    async def update_media(self, media_doc, media_type):
        tmdb_id = media_doc["tmdb_id"]
        if existing_media := self.tmdb.find_one({"tmdb_id": tmdb_id}):
            # If media is present, update the document
            if media_type == "series":
                for season in media_doc["seasons"]:
                    if existing_season := next(
                        (
                            s
                            for s in existing_media["seasons"]
                            if s["season_number"] == season["season_number"]
                        ),
                        None,
                    ):
                        for episode in season["episodes"]:
                            if existing_episode := next(
                                (
                                    e
                                    for e in existing_season["episodes"]
                                    if e["episode_number"]
                                    == episode["episode_number"]
                                ),
                                None,
                            ):
                                for quality in episode["qualities"]:
                                    if existing_quality := next(
                                        (
                                            q
                                            for q in existing_episode["qualities"]
                                            if q["quality"] == quality["quality"]
                                        ),
                                        None,
                                    ):
                                        existing_quality.update(quality)
                                    else:
                                        existing_episode["qualities"].append(
                                            quality)
                            else:
                                existing_season["episodes"].append(episode)
                    else:
                        existing_media["seasons"].append(season)
            elif media_type == "movie":
                for quality in media_doc["qualities"]:
                    if existing_quality := next(
                        (
                            q
                            for q in existing_media["qualities"]
                            if q["quality"] == quality["quality"]
                        ),
                        None,
                    ):
                        existing_quality.update(quality)

                    else:
                        existing_media["qualities"].append(quality)
            self.tmdb.replace_one({"tmdb_id": tmdb_id}, existing_media)
        else:
            self.tmdb.insert_one(media_doc)
