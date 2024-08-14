import re
from aiofiles import open as aiopen
from os import path as ospath

from surftg import LOGGER
from surftg.config import Telegram
from surftg.helper.database import Database
from surftg.helper.exceptions import InvalidHash
from surftg.helper.file_size import get_readable_file_size
from surftg.server.file_properties import get_file_ids
from surftg.bot import StreamBot

db = Database()

admin_block = """
                    <style>
                        .admin-only {
                            display: none;
                        }
                    </style>"""

hide_channel = """
                    <style>
                        .hide-channel {
                            display: none;
                        }
                    </style>"""


def generate_pagination(current_page, total_pages, max_pages_to_show=3):
    pagination_html = '<div><ul class="pagination">'

    # Calculate the start and end page indices
    start_page = max(1, current_page - max_pages_to_show // 2)
    end_page = min(total_pages, start_page + max_pages_to_show - 1)

    # Adjust start and end pages if they go out of bounds
    if end_page - start_page < max_pages_to_show:
        start_page = max(1, end_page - max_pages_to_show + 1)

    if current_page > 1:
        pagination_html += '<li class="page-item"><a class="page-link" href="?page=1"><i class="bi bi-chevron-double-left"></i></a></li>'
        pagination_html += f'<li class="page-item"><a class="page-link" href="?page={current_page-1}"><i class="bi bi-chevron-left"></i></a></li>'
    else:
        pagination_html += '<li class="page-item disabled"><a class="page-link" href="#"><i class="bi bi-chevron-left"></i></a></li>'

    # Page numbers
    for page in range(start_page, end_page + 1):
        if page == current_page:
            pagination_html += f'<li class="page-item active"><a class="page-link" href="#">{page}</a></li>'
        else:
            pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page}">{page}</a></li>'

    # Next button
    if current_page < total_pages:
        pagination_html += f'<li class="page-item"><a class="page-link" href="?page={current_page+1}"><i class="bi bi-chevron-right"></i></a></li>'
    else:
        pagination_html += '<li class="page-item disabled"><a class="page-link" href="#"><i class="bi bi-chevron-right"></i></a></li>'

    # Last button
    if current_page < total_pages:
        pagination_html += f'<li class="page-item"><a class="page-link" href="?page={total_pages}"><i class="bi bi-chevron-double-right"></i></a></li>'

    pagination_html += '</ul></div>'
    return pagination_html


def generate_search_pagination(request, current_page, total_pages, max_pages_to_show=3):
    pagination_html = '<div><ul class="pagination">'
    query_params = request

    # Calculate the start and end page indices
    start_page = max(1, current_page - max_pages_to_show // 2)
    end_page = min(total_pages, start_page + max_pages_to_show - 1)

    # Adjust start and end pages if they go out of bounds
    if end_page - start_page < max_pages_to_show:
        start_page = max(1, end_page - max_pages_to_show + 1)

    if current_page > 1:
        pagination_html += f'<li class="page-item"><a class="page-link" href="?q={query_params}&page=1"><i class="bi bi-chevron-double-left"></i></a></li>'
        pagination_html += f'<li class="page-item"><a class="page-link" href="?q={query_params}&page={current_page-1}"><i class="bi bi-chevron-left"></i></a></li>'
    else:
        pagination_html += '<li class="page-item disabled"><a class="page-link" href="#"><i class="bi bi-chevron-left"></i></a></li>'

    # Page numbers
    for page in range(start_page, end_page + 1):
        if page == current_page:
            pagination_html += f'<li class="page-item active"><a class="page-link" href="#">{page}</a></li>'
        else:
            pagination_html += f'<li class="page-item"><a class="page-link" href="?q={query_params}&page={page}">{page}</a></li>'

    # Next button
    if current_page < total_pages:
        pagination_html += f'<li class="page-item"><a class="page-link" href="?q={query_params}&page={current_page+1}"><i class="bi bi-chevron-right"></i></a></li>'
    else:
        pagination_html += '<li class="page-item disabled"><a class="page-link" href="#"><i class="bi bi-chevron-right"></i></a></li>'

    # Last button
    if current_page < total_pages:
        pagination_html += f'<li class="page-item"><a class="page-link" href="?q={query_params}&page={total_pages}"><i class="bi bi-chevron-double-right"></i></a></li>'

    pagination_html += '</ul></div>'
    return pagination_html


async def render_page(id, secure_hash, is_admin=False, html='', playlist='', database='', route='', redirect_url='', msg='', chat_id='', current_page=1, total_pages=1):
    theme = await db.get_variable('theme')
    if theme is None or theme == '':
        theme = Telegram.THEME
    tpath = ospath.join('surftg', 'server', 'template')
    if route == 'login':
        async with aiopen(ospath.join(tpath, 'login.html'), 'r') as f:
            html = (await f.read()).replace("<!-- Error -->", msg or '').replace("<!-- Theme -->", theme.lower()).replace("<!-- RedirectURL -->", redirect_url)
# ---------------------tmdb render route----------------------------------------------------
    elif route == "tmdbhome":
        async with aiopen(ospath.join(tpath, 'tmdbHome.html'), 'r') as f:
            html = (await f.read())
    elif route == "tmdblist":
        async with aiopen(ospath.join(tpath, 'tmdbList.html'), 'r') as f:
            pagination_html = generate_pagination(current_page, total_pages)
            html = (await f.read()).replace("<!-- Print -->", html).replace("<!-- Theme -->", theme.lower()).replace("<--!posttitle-->", msg).replace("<!-- Pagination -->", pagination_html)
    elif route == "tmdblistsearch":
        async with aiopen(ospath.join(tpath, 'tmdbListSearch.html'), 'r') as f:
            pagination_html = generate_search_pagination(msg, current_page, total_pages)  # Generate pagination HTML
            html = (await f.read()).replace("<!-- Print -->", html).replace("<--!posttitle-->", msg).replace("<!-- Pagination -->", pagination_html)
    elif route == "movie":
        async with aiopen(ospath.join(tpath, 'tmdbMovie.html'), 'r') as f:
            html = (await f.read()).replace('<!-- Username -->', StreamBot.me.username)
    elif route == "tv":
        async with aiopen(ospath.join(tpath, 'tmdbSeries.html'), 'r') as f:
            html = (await f.read()).replace('<!-- Username -->', StreamBot.me.username)
# -----------------------------------------------------------------------------------------------
    elif route == 'home':
        async with aiopen(ospath.join(tpath, 'home.html'), 'r') as f:
            html = (await f.read()).replace("<!-- Print -->", html).replace("<!-- Theme -->", theme.lower()).replace("<!-- Playlist -->", playlist)
            if not is_admin:
                html += admin_block
                if Telegram.HIDE_CHANNEL:
                    html += hide_channel
    elif route == 'playlist':
        async with aiopen(ospath.join(tpath, 'playlist.html'), 'r') as f:
            html = (await f.read()).replace("<!-- Theme -->", theme.lower()).replace("<!-- Playlist -->", playlist).replace("<!-- Database -->", database).replace("<!-- Title -->", msg).replace("<!-- Parent_id -->", id)
            if not is_admin:
                html += admin_block
    elif route == 'index':
        async with aiopen(ospath.join(tpath, 'index.html'), 'r') as f:
            html = (await f.read()).replace("<!-- Print -->", html).replace("<!-- Theme -->", theme.lower()).replace("<!-- Title -->", msg).replace("<!-- Chat_id -->", chat_id)
            if not is_admin:
                html += admin_block
    else:
        file_data = await get_file_ids(StreamBot, chat_id=int(chat_id), message_id=int(id))
        if file_data.unique_id[:6] != secure_hash:
            LOGGER.info('Link hash: %s - %s', secure_hash,
                        file_data.unique_id[:6])
            LOGGER.info('Invalid hash for message with - ID %s', id)
            raise InvalidHash
        filename, tag, size = file_data.file_name, file_data.mime_type.split(
            '/')[0].strip(), get_readable_file_size(file_data.file_size)
        if filename is None:
            filename = "Proper Filename is Missing"
        filename = re.sub(r'[,|_\',]', ' ', filename)
        if tag == 'video':
            async with aiopen(ospath.join(tpath, 'video.html')) as r:
                poster = f"/api/thumb/{chat_id}?id={id}"
                html = (await r.read()).replace('<!-- Filename -->', filename).replace("<!-- Theme -->", theme.lower()).replace('<!-- Poster -->', poster).replace('<!-- Size -->', size).replace('<!-- Username -->', StreamBot.me.username)
        else:
            async with aiopen(ospath.join(tpath, 'dl.html')) as r:
                html = (await r.read()).replace('<!-- Filename -->', filename).replace("<!-- Theme -->", theme.lower()).replace('<!-- Size -->', size)
    return html
