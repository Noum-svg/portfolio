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

  /* ---------- code viewer ---------- */
  function codeViewer() {
    const modal = $('#codeModal');
    if (!modal) return;
    const filesEl = $('#cmFiles'), codeEl = $('#cmCode'), titleEl = $('#cmTitle'),
          nameEl = $('#cmFilename'), copyBtn = $('#cmCopy');
    let manifest = null, current = null;

    const highlight = (text, lang) => {
      codeEl.textContent = text;
      codeEl.className = 'hljs language-' + (lang || 'plaintext');
      if (window.hljs) { try { window.hljs.highlightElement(codeEl); } catch (e) {} }
    };

    const loadFile = (slug, file) => {
      $$('.codemodal__file').forEach((b) => b.classList.toggle('active', b.dataset.file === file.name));
      nameEl.textContent = 'code/' + slug + '/' + file.name;
      codeEl.textContent = 'Loading…';
      fetch('code/' + slug + '/' + encodeURIComponent(file.name))
        .then((r) => r.text())
        .then((t) => { current = t; highlight(t, file.lang); codeEl.parentElement.scrollTop = 0; })
        .catch(() => { codeEl.textContent = '// could not load file'; });
    };

    const open = (slug) => {
      const proj = manifest[slug];
      if (!proj) return;
      titleEl.textContent = proj.name.toLowerCase().replace(/[^a-z0-9]+/g, '-') + ' — source';
      filesEl.innerHTML = '';
      proj.files.forEach((f) => {
        const b = document.createElement('button');
        b.className = 'codemodal__file'; b.textContent = f.name; b.dataset.file = f.name;
        b.addEventListener('click', () => loadFile(slug, f));
        filesEl.appendChild(b);
      });
      modal.classList.add('open'); modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      loadFile(slug, proj.files[0]);
    };

    const close = () => {
      modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    };

    const wire = () => {
      $$('.project__code').forEach((btn) => {
        const slug = btn.dataset.code;
        btn.addEventListener('click', () => { if (manifest) open(slug); });
      });
    };

    fetch('code/manifest.json').then((r) => r.json())
      .then((m) => { manifest = m; wire(); })
      .catch(() => {});

    modal.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
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

  function init() { misc(); reveal(); counters(); scrollspy(); progress(); menu(); typing(); codeViewer(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
