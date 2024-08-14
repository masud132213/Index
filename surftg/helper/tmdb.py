import json
from math import ceil
import re
from typing import Optional
from surftg import LOGGER
from surftg.helper.utilis import clean_file_name
from surftg.config import Telegram

# Your API key for TMDB
API_KEY = Telegram.TMDB_API
TMDB_LANGUAGE = Telegram.TMDB_LANGUAGE

def clean_title(title: str) -> str:
    """Remove non-alphanumeric characters and convert to lowercase."""
    return re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().strip()

# Initialize the TMDBClient
class TMDBClient:
    def __init__(self, client):
        self.client = client
        self.api_key = API_KEY
        self.language = TMDB_LANGUAGE

    def get_episode_details(self, tmdb_id: int, episode_number: int, season_number: int = 1) -> dict:
        """Get the details of a specific episode from the API"""
        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}/episode/{episode_number}"
        response = self.client.get(url, params={'api_key': self.api_key, "language": self.language})
        if response.status_code == 200:
            return response.json()
        LOGGER.warn(
            f"Failed to fetch episode details for TMDB ID {tmdb_id}, season {season_number}, episode {episode_number}. Status code: {response.status_code}")
        return {}

    def find_media_id(self, title: str, data_type: str, use_api: bool = True, year: Optional[int] = None, adult: bool = False) -> Optional[int]:
        """Get TMDB ID for a title"""

        title = title.lower().strip()
        original_title = title
        title = clean_file_name(title)

        if not title:
            LOGGER.warn(
                "The parsed title returned an empty string. Skipping...")
            LOGGER.info("Original Title: %s", original_title)
            return None

        if use_api:
            LOGGER.info("Trying search using API for '%s'", title)
            type_name = "tv" if data_type == "series" else "movie"

            def search_tmdb(query_year):
                params = {
                    "query": title,
                    "include_adult": adult,
                    "page": 1,
                    "language": self.language,
                    "api_key": self.api_key,
                }
                if query_year:
                    params["primary_release_year"] = query_year

                resp = self.client.get(
                    f"https://api.themoviedb.org/3/search/{type_name}", params=params)
                return resp

            # Attempt to search with year
            resp = search_tmdb(year)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if not results and year:
                    # Retry without year if no results are found
                    LOGGER.warn(
                        f"No results found for '{title}' with year {year}. Retrying without year.")
                    resp = search_tmdb(None)
                    results = resp.json().get("results", [])

                if results:
                    LOGGER.debug(f"Search results for '{title}': {results}")
                    return results[0]["id"]

                else:
                    LOGGER.warn(
                        f"No results found for '{title}' - The API said '{resp.json().get('errors', 'No error message provided')}' with status code {resp.status_code}"
                    )
            else:
                LOGGER.warn(
                    f"API search failed for '{title}' - The API said '{resp.json().get('errors', 'No error message provided')}' with status code {resp.status_code}"
                )
        return 

    def get_details(self, tmdb_id: int, data_type: str) -> dict:
        """Get the details of a movie/series from the API"""
        type_name = "tv" if data_type == "series" else "movie"
        url = f"https://api.themoviedb.org/3/{type_name}/{tmdb_id}"
        if type_name == "tv":
            params = {
                "include_image_language": self.language,
                "append_to_response": "credits,images,external_ids,videos,reviews,content_ratings",
                "api_key": self.api_key,
                "language": self.language
            }
        else:
            params = {
                "include_image_language": self.language,
                "append_to_response": "credits,images,external_ids,videos,reviews",
                "api_key": self.api_key,
                "language": self.language
            }
        response = self.client.get(url, params=params).json()

        if type_name == "tv":
            self._extracted_from_get_details_13(response, url)
        # print(response)
        return response

    # Rename this here and in `get_details`
    def _extracted_from_get_details_13(self, response, url):
        seasons = response.get("seasons", [])
        length = len(seasons)
        append_seasons = []
        n_of_appends = ceil(length / 20)
        for x in range(n_of_appends):
            append_season = ",".join(
                f"season/{n}" for n in range(x * 20, min((x + 1) * 20, length)))
            append_seasons.append(append_season)

        for append_season in append_seasons:
            tmp_response = self.client.get(
                url, params={"append_to_response": append_season, "api_key": self.api_key}).json()
            season_keys = [k for k in tmp_response.keys() if "season/" in k]
            for key in season_keys:
                response[key] = tmp_response[key]
