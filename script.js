/* ============================================================
   Nouemane El Gaou — Portfolio interactions
   ============================================================ */
(function () {
  'use strict';

  const $  = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------
     PRELOADER
  --------------------------------------------------------- */
  function preloader() {
    const pre     = $('#preloader');
    const counter = $('#counter');
    const bar     = $('#loadBar');
    if (!pre) return revealHero();

    if (reduceMotion) {
      pre.classList.add('done');
      setTimeout(revealHero, 100);
      return;
    }

    let val = 0;
    const tick = () => {
      val += Math.round(Math.random() * 8) + 3;
      if (val > 100) val = 100;
      counter.textContent = val;
      bar.style.width = val + '%';
      if (val < 100) {
        setTimeout(tick, Math.random() * 130 + 40);
      } else {
        setTimeout(() => {
          pre.classList.add('done');
          revealHero();
        }, 350);
      }
    };
    tick();
  }

  /* ---------------------------------------------------------
     HERO INTRO (staggered lines)
  --------------------------------------------------------- */
  function wrapLines() {
    $$('.hero__title .line, .contact__mail .line').forEach((line) => {
      if (line.querySelector('span,em,i')) return; // already structured
    });
    // wrap raw text nodes so they can be translated
    $$('.hero__title .line, .contact__mail .line').forEach((line) => {
      const html = line.innerHTML.trim();
      line.innerHTML = `<span class="line__inner">${html}</span>`;
    });
  }

  function revealHero() {
    document.body.classList.add('loaded');
    $$('.hero__title .line__inner').forEach((el, i) => {
      setTimeout(() => el.classList.add('reveal-up'), 120 * i + 80);
    });
    $$('.hero [data-reveal]').forEach((el, i) => {
      setTimeout(() => el.classList.add('in'), 350 + 90 * i);
    });
  }

  /* ---------------------------------------------------------
     SCROLL REVEAL (IntersectionObserver)
  --------------------------------------------------------- */
  function scrollReveal() {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          // stagger children inside contact mail
          if (e.target.classList.contains('line')) {
            const inner = e.target.querySelector('.line__inner');
            if (inner) inner.classList.add('reveal-up');
          }
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    $$('[data-reveal]').forEach((el) => {
      if (el.closest('.hero')) return; // hero handled by intro
      io.observe(el);
    });
    $$('.contact__mail .line').forEach((el) => io.observe(el));
  }

  /* ---------------------------------------------------------
     STAT COUNTERS
  --------------------------------------------------------- */
  function counters() {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        const el     = e.target;
        const target = parseInt(el.dataset.count, 10);
        const prefix = el.dataset.prefix || '';
        if (reduceMotion) { el.textContent = prefix + target; io.unobserve(el); return; }
        let cur = 0;
        const step = Math.max(1, Math.round(target / 38));
        const run = () => {
          cur += step;
          if (cur >= target) { cur = target; }
          el.textContent = prefix + cur;
          if (cur < target) requestAnimationFrame(run);
        };
        run();
        io.unobserve(el);
      });
    }, { threshold: 0.5 });
    $$('[data-count]').forEach((el) => io.observe(el));
  }

  /* ---------------------------------------------------------
     HEADER on scroll + scroll progress
  --------------------------------------------------------- */
  function headerScroll() {
    const header   = $('#header');
    const progress = $('#scrollProgress');
    const onScroll = () => {
      const y = window.scrollY;
      header.classList.toggle('scrolled', y > 40);
      const h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------------------------------------------------------
     MOBILE MENU
  --------------------------------------------------------- */
  function mobileMenu() {
    const burger = $('#burger');
    const nav    = $('#nav');
    if (!burger) return;
    const toggle = (force) => {
      const open = force ?? !nav.classList.contains('open');
      nav.classList.toggle('open', open);
      burger.classList.toggle('open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    burger.addEventListener('click', () => toggle());
    $$('#nav a').forEach((a) => a.addEventListener('click', () => toggle(false)));
  }

  /* ---------------------------------------------------------
     HERO PARALLAX
  --------------------------------------------------------- */
  function heroParallax() {
    if (reduceMotion) return;
    const b1 = $('.hero__blob--1');
    const b2 = $('.hero__blob--2');
    const title = $('.hero__title');
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y > window.innerHeight) return;
      if (b1) b1.style.transform = `translateY(${y * 0.18}px)`;
      if (b2) b2.style.transform = `translateY(${-y * 0.12}px)`;
      if (title) title.style.transform = `translateY(${y * 0.07}px)`;
    }, { passive: true });
  }

  /* ---------------------------------------------------------
     CUSTOM CURSOR
  --------------------------------------------------------- */
  function cursor() {
    if (window.matchMedia('(hover: none)').matches) return;
    const ring = $('#cursor');
    const dot  = $('#cursorDot');
    if (!ring) return;

    let mx = innerWidth / 2, my = innerHeight / 2;
    let rx = mx, ry = my;

    window.addEventListener('mousemove', (e) => {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = `translate(${mx}px, ${my}px) translate(-50%,-50%)`;
    });

    const loop = () => {
      rx += (mx - rx) * 0.18;
      ry += (my - ry) * 0.18;
      ring.style.transform = `translate(${rx}px, ${ry}px) translate(-50%,-50%)`;
      requestAnimationFrame(loop);
    };
    loop();

    const hoverEls = '[data-hover], a, button';
    document.addEventListener('mouseover', (e) => {
      if (e.target.closest(hoverEls)) ring.classList.add('hovering');
    });
    document.addEventListener('mouseout', (e) => {
      if (e.target.closest(hoverEls)) ring.classList.remove('hovering');
    });
  }

  /* ---------------------------------------------------------
     CARD TILT + glow tracking
  --------------------------------------------------------- */
  function cardTilt() {
    const cards = $$('[data-tilt]');
    cards.forEach((card) => {
      card.addEventListener('mousemove', (e) => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width;
        const py = (e.clientY - r.top) / r.height;
        card.style.setProperty('--mx', px * 100 + '%');
        card.style.setProperty('--my', py * 100 + '%');
        if (reduceMotion) return;
        const rotX = (py - 0.5) * -6;
        const rotY = (px - 0.5) * 6;
        card.style.transform = `perspective(900px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateY(-4px)`;
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });
  }

  /* ---------------------------------------------------------
     MISC
  --------------------------------------------------------- */
  function misc() {
    const yr = $('#year');
    if (yr) yr.textContent = new Date().getFullYear();
  }

  /* ---------------------------------------------------------
     INIT
  --------------------------------------------------------- */
  function init() {
    wrapLines();
    misc();
    headerScroll();
    mobileMenu();
    scrollReveal();
    counters();
    heroParallax();
    cursor();
    cardTilt();
    preloader();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
