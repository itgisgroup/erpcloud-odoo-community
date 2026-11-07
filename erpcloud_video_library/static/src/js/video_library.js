/** @odoo-module **/

// Standalone website behavior. It does not depend on Odoo's legacy publicWidget.
const make = (tag, className, value) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value != null) node.textContent = String(value);
    return node;
};

function videoCard(video) {
    if (!/^[A-Za-z0-9_-]{11}$/.test(video.video_id || '')) return null;
    const column = make('div', 'col-lg-4 col-md-6 mb-4 video_card_col');
    const card = make('div', `video_card${video.is_featured ? ' featured' : ''}`);
    const thumb = make('div', 'video_thumbnail');
    const fallback = make('div', 'video_thumbnail_fallback');
    fallback.appendChild(make('span', 'video_thumbnail_label', 'VIDEO LIBRARY'));
    fallback.appendChild(make('strong', 'video_thumbnail_title', video.name || 'Watch video'));
    thumb.appendChild(fallback);
    const image = make('img');
    image.src = `https://img.youtube.com/vi/${video.video_id}/hqdefault.jpg`;
    image.alt = video.name || '';
    image.loading = 'lazy';
    image.addEventListener('load', () => { image.style.display = 'block'; });
    image.addEventListener('error', () => { image.style.display = 'none'; });
    thumb.appendChild(image);
    const overlay = make('div', 'video_overlay');
    const play = make('div', 'play_button');
    play.appendChild(make('i', 'fa fa-play'));
    overlay.appendChild(play);
    thumb.appendChild(overlay);
    if (video.duration) thumb.appendChild(make('span', 'video_duration', video.duration));
    if (video.is_featured) thumb.appendChild(make('span', 'video_featured_badge', 'Featured'));
    const body = make('div', 'video_card_body');
    body.appendChild(make('span', 'video_category', video.category_name || ''));
    body.appendChild(make('h5', 'video_card_title', video.name || ''));
    body.appendChild(make('p', 'video_card_desc', video.description || ''));
    const link = make('a', 'btn_watch_video', 'Watch video');
    link.href = `https://www.youtube.com/watch?v=${video.video_id}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    body.appendChild(link);
    card.append(thumb, body);
    column.appendChild(card);
    return column;
}

async function loadVideos(section, category = 'all') {
    const grid = section.querySelector('.video_cards_grid');
    const filters = section.querySelector('.video_filter_buttons');
    if (!grid || !filters) return;
    grid.replaceChildren(make('div', 'col-12 text-center py-5', 'Loading videos…'));
    try {
        const limit = Math.max(1, Math.min(Number(section.dataset.vLimit) || 6, 24));
        const response = await fetch('/video_library/get_videos', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({jsonrpc: '2.0', params: {category_id: category, limit}}),
        });
        const payload = await response.json();
        if (!response.ok || payload.error) throw new Error('Video request failed');
        const data = payload.result || {};
        const cards = (data.videos || []).map(videoCard).filter(Boolean);
        grid.replaceChildren(...(cards.length ? cards : [make('div', 'col-12 text-center py-5', 'No published videos yet.')]));
        filters.replaceChildren();
        for (const item of [{id: 'all', name: 'All'}, ...(data.categories || [])]) {
            const button = make('button', `video_filter_btn${String(item.id) === String(category) ? ' active' : ''}`, item.name);
            button.type = 'button';
            button.dataset.category = item.id;
            button.addEventListener('click', () => loadVideos(section, item.id));
            filters.appendChild(button);
        }
    } catch (_error) {
        grid.replaceChildren(make('div', 'col-12 text-center py-5', 'Videos are temporarily unavailable. Please try again.'));
    }
}

function mount() {
    document.querySelectorAll('.s_video_library:not([data-ec-mounted])').forEach(section => {
        section.dataset.ecMounted = '1';
        loadVideos(section);
    });
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
else mount();
new MutationObserver(mount).observe(document.documentElement, {childList: true, subtree: true});
