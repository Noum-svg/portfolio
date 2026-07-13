/* ============================================================
   Nouemane El Gaou — Dashboard interactions
   ============================================================ */
(function () {
  'use strict';
  const $  = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- reveal on scroll ---------- */
  function reveal() {
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    $$('[data-reveal]').forEach((el) => io.observe(el));
  }

  /* ---------- stat counters ---------- */
  function counters() {
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => {
        if (!e.isIntersecting) return;
        const el = e.target, target = parseInt(el.dataset.count, 10), prefix = el.dataset.prefix || '';
        if (reduce) { el.textContent = prefix + target; io.unobserve(el); return; }
        let cur = 0; const step = Math.max(1, Math.round(target / 32));
        const run = () => { cur += step; if (cur >= target) cur = target; el.textContent = prefix + cur; if (cur < target) requestAnimationFrame(run); };
        run(); io.unobserve(el);
      });
    }, { threshold: 0.6 });
    $$('[data-count]').forEach((el) => io.observe(el));
  }

  /* ---------- scrollspy (active sidebar link) ---------- */
  function scrollspy() {
    const links = $$('.nav__link');
    const map = {}; links.forEach((l) => map[l.dataset.section] = l);
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => {
        if (e.isIntersecting) {
          links.forEach((l) => l.classList.remove('is-active'));
          const active = map[e.target.id];
          if (active) active.classList.add('is-active');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
    $$('.panel').forEach((p) => io.observe(p));
  }

  /* ---------- scroll progress ---------- */
  function progress() {
    const bar = $('#scrollProgress');
    const on = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + '%';
    };
    window.addEventListener('scroll', on, { passive: true }); on();
  }

  /* ---------- mobile sidebar ---------- */
  function menu() {
    const burger = $('#burger'), sidebar = $('#sidebar'), overlay = $('#overlay');
    if (!burger) return;
    const set = (open) => {
      sidebar.classList.toggle('open', open);
      overlay.classList.toggle('show', open);
      burger.classList.toggle('open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    burger.addEventListener('click', () => set(!sidebar.classList.contains('open')));
    overlay.addEventListener('click', () => set(false));
    $$('.nav__link, .btn-cv').forEach((a) => a.addEventListener('click', () => set(false)));
  }

  /* ---------- terminal typing ---------- */
  function typing() {
    const el = $('#typed');
    if (!el) return;
    const cmds = ['ls projects/', 'git status', 'python train.py --model llm', './deploy.sh'];
    if (reduce) { el.textContent = cmds[0]; return; }
    let ci = 0, chi = 0, del = false;
    const tick = () => {
      const word = cmds[ci];
      el.textContent = word.slice(0, chi);
      if (!del) {
        chi++;
        if (chi > word.length) { del = true; return setTimeout(tick, 1600); }
      } else {
        chi--;
        if (chi === 0) { del = false; ci = (ci + 1) % cmds.length; }
      }
      setTimeout(tick, del ? 45 : 95);
    };
    setTimeout(tick, 900);
  }

  /* ---------- KaTeX math ---------- */
  const MATH_OPTS = {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$', right: '$', display: false }
    ],
    throwOnError: false
  };
  function renderMath(el) {
    if (window.renderMathInElement && el) {
      try { window.renderMathInElement(el, MATH_OPTS); } catch (e) {}
    }
  }
  function mathInit() {
    if (!window.renderMathInElement) { setTimeout(mathInit, 120); return; }
    $$('.project__math').forEach(renderMath);
  }

  /* ---------- repo / code viewer (GitHub-style) ---------- */
  function codeViewer() {
    const modal = $('#codeModal');
    if (!modal) return;
    const filesEl = $('#cmFiles'), viewEl = $('#cmView'), titleEl = $('#cmTitle'),
          descEl = $('#cmDesc'), langEl = $('#cmLang'), nameEl = $('#cmFilename'), copyBtn = $('#cmCopy');
    let manifest = null, current = null;

    const setActive = (name) =>
      $$('.codemodal__file').forEach((b) => b.classList.toggle('active', b.dataset.file === name));

    const showCode = (slug, file) => {
      setActive(file.name);
      nameEl.textContent = 'code/' + slug + '/' + file.name;
      viewEl.innerHTML = '';
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.className = 'hljs language-' + (file.lang || 'plaintext');
      code.textContent = 'Loading…';
      pre.appendChild(code); viewEl.appendChild(pre);
      fetch('code/' + slug + '/' + encodeURIComponent(file.name))
        .then((r) => r.text())
        .then((t) => { current = t; code.textContent = t; if (window.hljs) { try { window.hljs.highlightElement(code); } catch (e) {} } viewEl.scrollTop = 0; })
        .catch(() => { code.textContent = '// could not load file'; });
    };

    const showReadme = (slug, readme) => {
      setActive(readme);
      nameEl.textContent = readme;
      viewEl.innerHTML = '<div class="markdown-body">Loading…</div>';
      fetch('code/' + slug + '/' + encodeURIComponent(readme))
        .then((r) => r.text())
        .then((md) => {
          current = md;
          let html = md;
          if (window.marked) {
            // Protect $$…$$ and $…$ from markdown parsing (e.g. * in V^*), restore after.
            const math = [];
            const stash = (m) => { math.push(m); return '@@MATH' + (math.length - 1) + '@@'; };
            const tokenized = md
              .replace(/\$\$([\s\S]+?)\$\$/g, stash)
              .replace(/\$([^$\n]+?)\$/g, stash);
            html = window.marked.parse(tokenized)
              .replace(/@@MATH(\d+)@@/g, (_, i) => math[+i]);
          }
          viewEl.innerHTML = '<div class="markdown-body">' + html + '</div>';
          renderMath(viewEl.firstChild);
          viewEl.scrollTop = 0;
        })
        .catch(() => { viewEl.innerHTML = '<div class="markdown-body">// could not load README</div>'; });
    };

    const open = (slug) => {
      const proj = manifest[slug];
      if (!proj) return;
      titleEl.textContent = 'nouemane / ' + proj.name;
      descEl.textContent = proj.desc || '';
      langEl.textContent = proj.lang || '';
      filesEl.innerHTML = '';

      if (proj.readme) {
        const b = document.createElement('button');
        b.className = 'codemodal__file is-readme'; b.textContent = proj.readme; b.dataset.file = proj.readme;
        b.addEventListener('click', () => showReadme(slug, proj.readme));
        filesEl.appendChild(b);
      }
      proj.files.forEach((f) => {
        const b = document.createElement('button');
        b.className = 'codemodal__file'; b.textContent = f.name; b.dataset.file = f.name;
        b.addEventListener('click', () => showCode(slug, f));
        filesEl.appendChild(b);
      });

      modal.classList.add('open'); modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      if (proj.readme) showReadme(slug, proj.readme);
      else showCode(slug, proj.files[0]);
    };

    const close = () => {
      modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    };

    fetch('code/manifest.json').then((r) => r.json())
      .then((m) => {
        manifest = m;
        $$('.project__code').forEach((btn) => {
          const slug = btn.dataset.code;
          btn.addEventListener('click', () => { if (manifest && manifest[slug]) open(slug); });
        });
      })
      .catch(() => {});

    modal.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && modal.classList.contains('open')) close(); });
    copyBtn.addEventListener('click', () => {
      if (current == null) return;
      navigator.clipboard.writeText(current).then(() => {
        copyBtn.textContent = 'Copied ✓';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
      });
    });
  }

  /* ---------- misc ---------- */
  function misc() { const y = $('#year'); if (y) y.textContent = new Date().getFullYear(); }

  function init() { misc(); reveal(); counters(); scrollspy(); progress(); menu(); typing(); mathInit(); codeViewer(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
