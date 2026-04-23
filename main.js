document.getElementById('year').textContent = new Date().getFullYear();

const STATUS_LABELS = {
    want: 'хочу',
    have: 'есть',
    done: 'готово',
    wip: 'в процессе',
    v5: 'очень хочу',
    v4: 'хочу',
    v3: 'неплохо',
    v2: 'сойдёт',
    v1: 'ну может',
};

async function loadSection(file, containerId, opts = {}) {
    const { showPic = false, sortBy = null, localImages = false } = opts;
    const container = document.getElementById(containerId);
    if (!container) return;
    try {
        const res = await fetch(file);
        if (!res.ok) throw new Error(res.statusText);
        let items = await res.json();

        if (sortBy === 'year') {
            items = [...items].sort((a, b) => {
                const yr = s => parseInt(s?.desc?.match(/(\d{4})\s*$/)?.[1] ?? '0');
                return yr(a) - yr(b);
            });
        }

        if (!items.length) {
            container.innerHTML = '<p class="empty">скоро будет...</p>';
            return;
        }

        const rows = items.map(item => {
            const num = item.desc?.match(/^(\S+)/)?.[1] ?? null;

            const nameHtml = item.url
                ? `<a href="${item.url}" target="_blank" rel="noopener">${item.name}</a>`
                : item.name;

            const descHtml = item.desc
                ? `<div class="item-desc">${item.desc}</div>`
                : '';

            const statusHtml = item.status
                ? `<span class="item-status status-${item.status}">${STATUS_LABELS[item.status] ?? item.status}</span>`
                : '';

            if (localImages && num) {
                const imgSrc = `img/lego/${num}.jpg`;
                const safeName = item.name.replace(/'/g, "\\'");
                const blUrl  = item.url ?? '#';
                const rbUrl  = `https://rebrickable.com/sets/${num}-1/`;
                const ebayUrl = `https://www.ebay.com/sch/i.html?_nkw=lego+${encodeURIComponent(num)}`;

                return `
                    <div class="item item-with-img">
                        <img class="item-thumb" src="${imgSrc}" alt="${item.name}" loading="lazy"
                             onclick="openModal('${imgSrc}','${safeName}')">
                        <div class="item-body">
                            <div class="item-name">${nameHtml}</div>
                            ${descHtml}
                        </div>
                        <div class="item-right">
                            <div class="item-links">
                                <a class="item-link" href="${blUrl}" target="_blank" rel="noopener">BL</a>
                                <a class="item-link" href="${rbUrl}" target="_blank" rel="noopener">RB</a>
                                <a class="item-link" href="${ebayUrl}" target="_blank" rel="noopener">eBay</a>
                            </div>
                            ${statusHtml}
                        </div>
                    </div>`;
            }

            const picHtml = showPic && num
                ? `<button class="item-pic" onclick="openModal('https://img.bricklink.com/ItemImage/SN/0/${num}-1.png','${item.name.replace(/'/g,"\\'")}')">тык</button>`
                : '';

            return `
                <div class="item">
                    <div>
                        <div class="item-name">${nameHtml}</div>
                        ${descHtml}
                    </div>
                    <div class="item-right">${picHtml}${statusHtml}</div>
                </div>`;
        }).join('');

        container.innerHTML = `<div class="items-list">${rows}</div>`;
    } catch (err) {
        container.innerHTML = '<p class="empty">не удалось загрузить :(</p>';
        console.error(`[${containerId}]`, err);
    }
}

function openModal(src, alt) {
    const m = document.getElementById('img-modal');
    const img = document.getElementById('img-modal-img');
    img.src = src;
    img.alt = alt;
    m.classList.add('open');
}

document.getElementById('img-modal').addEventListener('click', function(e) {
    if (e.target === this || e.target.classList.contains('modal-backdrop')) {
        this.classList.remove('open');
    }
});

loadSection('data/retro.json', 'retro-list');
loadSection('data/diy.json', 'diy-list');
loadSection('data/games.json', 'games-list');
