# Nouemane El Gaou — Portfolio

Personal portfolio for **Nouemane El Gaou**, AI Engineering student at ENSIAS, Rabat.

A single-page, dark-themed, animated site inspired by [landonorris.com](https://landonorris.com).
No build step, no dependencies — pure HTML, CSS and vanilla JavaScript.

## Run locally

Just open `index.html` in a browser, or serve the folder:

```bash
python -m http.server 8000
# then visit http://localhost:8000
```

## Structure

```
index.html     # markup & content
styles.css     # design system, layout, responsive, animations
script.js      # preloader, scroll reveals, counters, cursor, menu
assets/
  profile.png  # profile photo
```

## Customize

- **Accent color** — edit the `--accent` / `--accent-2` / `--glow` variables at the top of `styles.css`.
- **Content** — edit the text directly in `index.html`.

## Deploy

The site is fully static and works on any host (GitHub Pages, Netlify, Vercel, Cloudflare Pages).
For GitHub Pages: push to a repo and enable Pages on the `main` branch (root).
