
async function fetchJSON(url) {
    const response = await fetch(url);
    const data = await response.json();
    return data;
}

function generateSection(items, title, className) {
    const section = document.createElement('div');
    section.className = 'container';

    const header = document.createElement('span');
    header.className = 'movies-container';
    header.style.marginTop = title === 'Latest Updates' ? '100px' : '10px'; // Set margin-top based on title
    header.innerHTML = `${title} <i class="fa-solid fa-chevron-right"></i><a href="/get/${className}" class="view-all">View All</a>`;

    const carousel = document.createElement('div');
    carousel.className = `main-carousel ${className}`;

    items.forEach(item => {
        const cell = document.createElement('div');
        cell.className = 'carousel-cell';
        cell.innerHTML = `
            <div class="card">
                <div class="movie-card">
                    <a href="/tmdb/${item.type}/${item.tmdb_id}">
                        <div class="card-head">
                            <img src="https://image.tmdb.org/t/p/w500${item.poster}"
                                class="card-img" alt="${item.title}">
                            <div class="card-overlay">
                                <div class="play">
                                    <ion-icon name="play-circle-outline" role="img" class="md hydrated"
                                        aria-label="play circle outline"></ion-icon>
                                </div>
                            </div>
                        </div>
                        <h6 class="card-title">${item.title}</h6>
                        <div class="card-info">
                            <span class="year">${item.release_date.substring(0, 4)}</span>
                        </div>
                    </a>
                </div>
            </div>
        `;
        carousel.appendChild(cell);
    });

    section.appendChild(header);
    section.appendChild(carousel);
    document.querySelector('.main-content').appendChild(section);
}

function initFlickity() {
    $('.main-carousel').flickity({
        // options
        cellAlign: 'left',
        contain: true,
        pageDots: false,
        groupCells: 2
    });
}

function waitForImages(callback) {
    const images = document.querySelectorAll('img');
    let loadedCount = 0;

    images.forEach((img) => {
        if (img.complete) {
            loadedCount++;
        } else {
            img.addEventListener('load', () => {
                loadedCount++;
                if (loadedCount === images.length) {
                    callback();
                }
            });
        }
    });

    if (loadedCount === images.length) {
        callback();
    }
}

const apiUrl = `/api/tmdb`;
const loadingScreen = document.getElementById('loading-screen');
loadingScreen.style.display = 'flex';
fetchJSON(apiUrl).then((data) => {
    generateSection(data.latest, 'Latest Updates', 'latest');
    generateSection(data.movies, 'Movies', 'Movies');
    generateSection(data.tvshows, 'Tv-Shows', 'tvshow');
    waitForImages(() => {
        initFlickity();
        loadingScreen.style.display = 'none';
    });
});





const STAR_COLOR = '#fff';
const STAR_SIZE = 3;
const STAR_MIN_SCALE = 0.2;
const OVERFLOW_THRESHOLD = 50;
const STAR_COUNT = (window.innerWidth + window.innerHeight) / 8;

const canvas = document.querySelector('canvas'),
    context = canvas.getContext('2d');

let scale = 1, // device pixel ratio
    width,
    height;

let stars = [];

let pointerX,
    pointerY;

let velocity = { x: 0, y: 0, tx: 0, ty: 0, z: 0.0005 };

let touchInput = false;

generate();
resize();
step();

window.onresize = resize;
canvas.onmousemove = onMouseMove;
canvas.ontouchmove = onTouchMove;
canvas.ontouchend = onMouseLeave;
document.onmouseleave = onMouseLeave;

function generate() {

    for (let i = 0; i < STAR_COUNT; i++) {
        stars.push({
            x: 0,
            y: 0,
            z: STAR_MIN_SCALE + Math.random() * (1 - STAR_MIN_SCALE)
        });
    }

}

function placeStar(star) {

    star.x = Math.random() * width;
    star.y = Math.random() * height;

}

function recycleStar(star) {

    let direction = 'z';

    let vx = Math.abs(velocity.x),
        vy = Math.abs(velocity.y);

    if (vx > 1 || vy > 1) {
        let axis;

        if (vx > vy) {
            axis = Math.random() < vx / (vx + vy) ? 'h' : 'v';
        }
        else {
            axis = Math.random() < vy / (vx + vy) ? 'v' : 'h';
        }

        if (axis === 'h') {
            direction = velocity.x > 0 ? 'l' : 'r';
        }
        else {
            direction = velocity.y > 0 ? 't' : 'b';
        }
    }

    star.z = STAR_MIN_SCALE + Math.random() * (1 - STAR_MIN_SCALE);

    if (direction === 'z') {
        star.z = 0.1;
        star.x = Math.random() * width;
        star.y = Math.random() * height;
    }
    else if (direction === 'l') {
        star.x = -OVERFLOW_THRESHOLD;
        star.y = height * Math.random();
    }
    else if (direction === 'r') {
        star.x = width + OVERFLOW_THRESHOLD;
        star.y = height * Math.random();
    }
    else if (direction === 't') {
        star.x = width * Math.random();
        star.y = -OVERFLOW_THRESHOLD;
    }
    else if (direction === 'b') {
        star.x = width * Math.random();
        star.y = height + OVERFLOW_THRESHOLD;
    }

}

function resize() {

    scale = window.devicePixelRatio || 1;

    width = window.innerWidth * scale;
    height = window.innerHeight * scale;

    canvas.width = width;
    canvas.height = height;

    stars.forEach(placeStar);

}

function step() {

    context.clearRect(0, 0, width, height);

    update();
    render();

    requestAnimationFrame(step);

}

function update() {

    velocity.tx *= 0.96;
    velocity.ty *= 0.96;

    velocity.x += (velocity.tx - velocity.x) * 0.8;
    velocity.y += (velocity.ty - velocity.y) * 0.8;

    stars.forEach((star) => {

        star.x += velocity.x * star.z;
        star.y += velocity.y * star.z;

        star.x += (star.x - width / 2) * velocity.z * star.z;
        star.y += (star.y - height / 2) * velocity.z * star.z;
        star.z += velocity.z;

        // recycle when out of bounds
        if (star.x < -OVERFLOW_THRESHOLD || star.x > width + OVERFLOW_THRESHOLD || star.y < -OVERFLOW_THRESHOLD || star.y > height + OVERFLOW_THRESHOLD) {
            recycleStar(star);
        }

    });

}

function render() {

    stars.forEach((star) => {

        context.beginPath();
        context.lineCap = 'round';
        context.lineWidth = STAR_SIZE * star.z * scale;
        context.globalAlpha = 0.5 + 0.5 * Math.random();
        context.strokeStyle = STAR_COLOR;

        context.beginPath();
        context.moveTo(star.x, star.y);

        var tailX = velocity.x * 2,
            tailY = velocity.y * 2;

        // stroke() wont work on an invisible line
        if (Math.abs(tailX) < 0.1) tailX = 0.5;
        if (Math.abs(tailY) < 0.1) tailY = 0.5;

        context.lineTo(star.x + tailX, star.y + tailY);

        context.stroke();

    });

}

function movePointer(x, y) {

    if (typeof pointerX === 'number' && typeof pointerY === 'number') {

        let ox = x - pointerX,
            oy = y - pointerY;

        velocity.tx = velocity.tx + (ox / 8 * scale) * (touchInput ? 1 : -1);
        velocity.ty = velocity.ty + (oy / 8 * scale) * (touchInput ? 1 : -1);

    }

    pointerX = x;
    pointerY = y;

}