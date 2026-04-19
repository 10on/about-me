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

async function loadSection(file, containerId) {
    const container = document.getElementById(containerId);
    try {
        const res = await fetch(file);
        if (!res.ok) throw new Error(res.statusText);
        const items = await res.json();

        if (!items.length) {
            container.innerHTML = '<p class="empty">скоро будет...</p>';
            return;
        }

        const rows = items.map(item => {
            const nameHtml = item.url
                ? `<a href="${item.url}" target="_blank" rel="noopener">${item.name}</a>`
                : item.name;

            const descHtml = item.desc
                ? `<div class="item-desc">${item.desc}</div>`
                : '';

            const statusHtml = item.status
                ? `<span class="item-status status-${item.status}">${STATUS_LABELS[item.status] ?? item.status}</span>`
                : '';

            const num = item.desc ? item.desc.match(/^(\S+)/)?.[1] : null;
            const imgUrl = num ? `https://img.bricklink.com/ItemImage/SN/0/${num}-1.png` : null;
            const picHtml = imgUrl
                ? `<button class="item-pic" onclick="openModal('${imgUrl}','${item.name.replace(/'/g,"\\'")}')">тык</button>`
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

loadSection('data/lego.json', 'lego-list');
loadSection('data/retro.json', 'retro-list');
loadSection('data/diy.json', 'diy-list');
