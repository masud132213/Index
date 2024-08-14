async function fetchJSON(url) {
    const response = await fetch(url);
    const data = await response.json();
    return data;
}

function convertMinutesToReadableFormat(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
}

// Function to create series card
function createMovieCard(data) {
    const { poster, title, rating, runtime, release_date, genres, description, backdrop } = data;

    // Update the poster image
    const posterElement = document.querySelector(".movie-poster");
    if (posterElement) {
        const posterUrl = `https://image.tmdb.org/t/p/w500/${poster}`;
        posterElement.src = posterUrl;
    }

    // Update the title
    const titleElement = document.querySelector(".movie-title");
    if (titleElement) {
        titleElement.textContent = title;
        document.title = `Movie - ${title}`;
    }
    // Format and update the rating (to one decimal place)
    const formattedRating = parseFloat(rating).toFixed(1);
    const ratingElement = document.querySelector(".rating");
    if (ratingElement) {
        ratingElement.innerHTML = `<i class="bi bi-star-fill" style="color: #ffd700;"></i> ${formattedRating}`;
    }

    const runtimeElement = document.querySelector(".runtime");
    if (runtimeElement) {
        const readableRuntime = convertMinutesToReadableFormat(runtime);
        runtimeElement.innerHTML = `<i class="bi bi-clock-fill"></i> ${readableRuntime}`;
    }


    // Extract and update the year (only the year part from YYYY-MM-DD format)
    const formattedYear = release_date.split('-')[0];
    const yearElement = document.querySelector(".year");
    if (yearElement) {
        yearElement.innerHTML = `<i class="bi bi-calendar-range-fill"></i> ${formattedYear}`;
    }

    // Join and update the genres (array of strings)
    const formattedGenres = genres.join(', ');
    const genreElement = document.querySelector(".genre");
    if (genreElement) {
        genreElement.textContent = formattedGenres;
    }
    // Update the description
    const descriptionElement = document.querySelector(".movie-description");
    if (descriptionElement) {
        descriptionElement.textContent = description;
    }

    const watchButton = document.querySelector(".watch-button");
    const backdropUrl = `https://image.tmdb.org/t/p/w1280${backdrop}`;

    if (watchButton) {
        watchButton.onclick = function () {
            const qualities = data.qualities.map(q => ({
                quality: q.quality,
                size: q.size,
                type: q.type,
                hash: q.hash,
                cid: q.cid,
                msg_id: q.msg_id
            }));
            showEpisodeDetails(title, `${backdropUrl}`, qualities);
        }
    }


    document.body.style.background = `linear-gradient(rgba(0, 0, 0, 0.588), rgba(0, 0, 0, 0.774)), url('${backdropUrl}')`;
    document.body.style.backgroundSize = "cover";
    document.body.style.backgroundAttachment = "fixed";
    document.body.style.backgroundRepeat = "no-repeat";

}

function showEpisodeDetails(title, poster, qualities) {
    if (!Array.isArray(qualities)) {
        console.error("Qualities is not an array:", qualities);
        qualities = [];
    }

    const modalTitle = document.getElementById("episodeModalLabel");
    modalTitle.textContent = title;
    const modalBody = document.getElementById("episodeModalBody");

    modalBody.innerHTML = `
        <div class="container text-center">
            <video controls crossorigin playsinline id="videoPlayer">
            </video>
            
            <div class="btn-group mt-2" role="group" aria-label="Button group with nested dropdown">
                <button type="button" class="btn btn-outline-secondary">Download</button>
                <div class="btn-group" role="group">
                    <button id="btnGroupDrop3" type="button"
                        class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown"
                        aria-haspopup="true" aria-expanded="false"></button>
                    <div class="dropdown-menu download" aria-labelledby="btnGroupDrop3">
                    </div>
                </div>
            </div>
            <div class="btn-group  mt-2" role="group" aria-label="Button group with nested dropdown">
                <button type="button" class="btn btn-outline-secondary">Get File</button>
                <div class="btn-group" role="group">
                    <button id="btnGroupDrop3" type="button"
                        class="btn  btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown"
                        aria-haspopup="true" aria-expanded="false"></button>
                    <div class="dropdown-menu telegram" aria-labelledby="btnGroupDrop3">
                    </div>
                </div>
            </div>

            <div class="btn-group  mt-2" role="group" aria-label="Button group with nested dropdown">
                <button type="button" class="btn btn-outline-secondary">MX Player</button>
                <div class="btn-group" role="group">
                    <button id="btnGroupDrop3" type="button"
                        class="btn btn-outline-secondary  dropdown-toggle" data-bs-toggle="dropdown"
                        aria-haspopup="true" aria-expanded="false"></button>
                    <div class="dropdown-menu mxplayer" aria-labelledby="btnGroupDrop3">
                    </div>
                </div>
            </div>
        </div>
    `;
    const modal = new bootstrap.Modal(document.getElementById('episodeModal'));
    modal.show();

    const player = new Plyr('#videoPlayer', { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'settings', 'pip', 'airplay', 'fullscreen', 'quality'] });
    const sources = qualities.map(quality => ({
        src: `/${quality.cid}/${quality.quality}.mkv?id=${quality.msg_id}&hash=${quality.hash}`,
        type: 'video/mp4',
        size: parseInt(quality.quality.replace('p', ''), 10)
    }));
    player.source = {
        type: 'video',
        title: title,
        sources: sources,
        poster: poster,
    };

    // Pause the video when the modal is being closed
    $('#episodeModal').on('hidden.bs.modal', function () {
        player.pause();
    });

    // Pause/play the video when tapping anywhere on it
    $('#videoPlayer').on('click', function () {
        if (player.playing) {
            player.pause();
        } else {
            player.play();
        }
    });

    const json = `{${qualities.map(quality => `"${quality.quality} - ${quality.size}": "/${quality.cid}/${quality.quality}.mkv?id=${quality.msg_id}&hash=${quality.hash}"`).join(',')}}`;

    const videoSources = JSON.parse(json);
    const videolink = window.location.href;
    const url = new URL(videolink);
    const domainUrl = url.origin;
    const dropdownMenu1 = document.querySelector('.mxplayer');
    dropdownMenu1.innerHTML = '';
    for (const [quality, source] of Object.entries(videoSources)) {
        const link = document.createElement('a');
        link.setAttribute('class', 'dropdown-item');
        link.setAttribute('href', `intent:${domainUrl}${source}#Intent;package=com.mxtech.videoplayer.ad;end`);
        link.textContent = `${quality}`;
        dropdownMenu1.appendChild(link);
    }

    const dropdownMenu2 = document.querySelector('.download');
    dropdownMenu2.innerHTML = '';
    for (const [quality, source] of Object.entries(videoSources)) {
        const link = document.createElement('a');
        link.setAttribute('class', 'dropdown-item');
        link.setAttribute('href', `${domainUrl}${source}`);
        link.textContent = `${quality}`;
        dropdownMenu2.appendChild(link);
    }

    const dropdownMenu3 = document.querySelector('.telegram');
    dropdownMenu3.innerHTML = '';
    const regex = /(\d+)\/\w+\.(mkv|mp4)\?id=(\d+)&/;

    for (const [quality, source] of Object.entries(videoSources)) {
        const match = source.match(regex);
        if (match) {
            const chatId = "-100" + match[1];
            const messageId = match[3];
            const link = document.createElement('a');
            link.setAttribute('class', 'dropdown-item');
            link.setAttribute('href', `https://t.me/<!-- Username -->?start=file_${messageId}${chatId}`);
            link.textContent = `${quality}`;
            dropdownMenu3.appendChild(link);
        }
    }

}

// Function to extract TMDB ID from the URL
function getTmdbIdFromUrl(url) {
    const urlParts = url.split('/');
    return urlParts[urlParts.length - 1];
}

// Example URL
const url = window.location.href;

// Extract TMDB ID
const tmdbId = getTmdbIdFromUrl(url);

// Construct API URL
const apiUrl = `/api/tmdb/${tmdbId}`;
const loadingScreen = document.getElementById('loading-screen');
loadingScreen.style.display = 'flex';
fetchJSON(apiUrl).then((data) => {
    createMovieCard(data);
    loadingScreen.style.display = 'none';
});