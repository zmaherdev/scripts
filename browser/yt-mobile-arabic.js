const SEL = '.YtmCommentRendererText, ytd-comments #content-text';

const st = document.createElement('style');
st.textContent = `${SEL}{text-align:start!important;unicode-bidi:plaintext}`;
document.documentElement.appendChild(st);

const fix = () => document.querySelectorAll(SEL).forEach(e => e.dir = 'auto');
new MutationObserver(fix).observe(document.documentElement, { childList: true, subtree: true });
fix();
