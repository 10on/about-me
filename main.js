document.getElementById('year').textContent = new Date().getFullYear();

const themeBtn = document.getElementById('theme-toggle');
function syncThemeLabel() {
    themeBtn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀︎' : '☾';
}
syncThemeLabel();
themeBtn.addEventListener('click', function () {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? '' : 'dark';
    if (next) document.documentElement.setAttribute('data-theme', next); else document.documentElement.removeAttribute('data-theme');
    syncThemeLabel();
    try { localStorage.setItem('denchik-theme', next); } catch (e) {}
});

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
