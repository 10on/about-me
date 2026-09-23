(function () {
    var scriptUrl = document.currentScript.src;
    var snapshotUrl = new URL('data/reactions.json', scriptUrl);
    var reactions = {};
    var isEnglish = document.documentElement.lang === 'en';

    function addCounters() {
        document.querySelectorAll('.note-comments-link, .article-read-link').forEach(function (link) {
            var match = new URL(link.getAttribute('href'), location.href).pathname.match(/\/(notes|articles)\/([a-z0-9-]+)\.html$/);
            if (!match) return;
            var term = (match[1] === 'notes' ? 'note:' : 'article:') + match[2];
            var info = reactions[term];
            var count = info && Number.isInteger(info.count) ? info.count : 0;
            var badge = link.parentElement.querySelector('.reaction-link');
            if (!badge) {
                badge = document.createElement('a');
                badge.className = 'reaction-link';
                link.before(badge);
            }
            var target = info && /^https:\/\/github\.com\/10on\/about-me\/discussions\/\d+$/.test(info.url)
                ? info.url : link.href.replace(/#.*$/, '') + '#comments';
            if (badge.getAttribute('href') !== target) badge.href = target;
            var label = (isEnglish ? 'Reactions: ' : 'Реакции: ') + count + (isEnglish ? '. Add yours' : '. Оставить свою');
            if (badge.getAttribute('aria-label') !== label) badge.setAttribute('aria-label', label);
            var display = '♡ ' + count;
            if (badge.textContent !== display) badge.textContent = display;
        });
    }

    addCounters();
    new MutationObserver(addCounters).observe(document.body, { childList: true, subtree: true });
    fetch(snapshotUrl).then(function (response) {
        if (!response.ok) throw new Error('Reaction snapshot unavailable');
        return response.json();
    }).then(function (data) {
        if (data && typeof data === 'object') reactions = data;
        addCounters();
    }).catch(function () {});
})();
