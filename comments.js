const GISCUS_CATEGORY_ID = 'DIC_kwDOSG9VXc4DGOlc';

const commentsSection = document.querySelector('[data-giscus-term]');
if (commentsSection && GISCUS_CATEGORY_ID) {
    commentsSection.hidden = false;
    if (location.hash === '#comments') requestAnimationFrame(() => commentsSection.scrollIntoView());

    const theme = () => document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const script = document.createElement('script');
    script.src = 'https://giscus.app/client.js';
    script.async = true;
    script.crossOrigin = 'anonymous';
    Object.assign(script.dataset, {
        repo: '10on/about-me',
        repoId: 'R_kgDOSG9VXQ',
        category: 'Announcements',
        categoryId: GISCUS_CATEGORY_ID,
        mapping: 'specific',
        term: commentsSection.dataset.giscusTerm,
        strict: '1',
        reactionsEnabled: '1',
        emitMetadata: '0',
        inputPosition: 'top',
        theme: theme(),
        lang: document.documentElement.lang === 'en' ? 'en' : 'ru',
        loading: 'lazy'
    });
    commentsSection.querySelector('.giscus').appendChild(script);

    new MutationObserver(() => {
        const frame = commentsSection.querySelector('iframe.giscus-frame');
        if (frame) frame.contentWindow.postMessage({ giscus: { setConfig: { theme: theme() } } }, 'https://giscus.app');
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}
