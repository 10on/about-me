document.getElementById('year').textContent = new Date().getFullYear();

const STATUS_LABELS = {
    want: 'хочу',
    have: 'есть',
    done: 'готово',
    wip: 'в процессе',
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

            return `
                <div class="item">
                    <div>
                        <div class="item-name">${nameHtml}</div>
                        ${descHtml}
                    </div>
                    ${statusHtml}
                </div>`;
        }).join('');

        container.innerHTML = `<div class="items-list">${rows}</div>`;
    } catch (err) {
        container.innerHTML = '<p class="empty">не удалось загрузить :(</p>';
        console.error(`[${containerId}]`, err);
    }
}

loadSection('data/lego.json', 'lego-list');
loadSection('data/retro.json', 'retro-list');
loadSection('data/diy.json', 'diy-list');
