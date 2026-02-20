# BCP Morning Prayer Comparator

This project is a minimal web app that compares the **Morning Prayer office** of the **1662 Book of Common Prayer** and the **1928 Book of Common Prayer** in a side-by-side interface.

## Stack

- **Web server:** Python app server (`app.py`) with routed endpoints
- **UI:** HTML template + static CSS/JavaScript
- **Data source:** local JSON file at `data/morning_prayer.json`
- **User preferences:** browser `localStorage`

## Project layout

- `app.py` — web server and routes
- `templates/index.html` — main page template
- `static/style.css` — UI styles
- `static/app.js` — browser logic (rendering, settings, diff)
- `data/morning_prayer.json` — canonical comparison data

## API routes

- `GET /` — main UI
- `GET /api/morning-prayer` — returns full comparison dataset as JSON

## How the office is structured for comparison

The texts are normalized into these logical units:

1. Opening Rubrics
2. Opening Sentences of Scripture
3. Exhortation
4. General Confession
5. Absolution / Declaration of Absolution
6. Opening Versicles and Lord’s Prayer Rubrics
7. Opening Versicles and Lord’s Prayer Text
8. Invitatory Psalm (Venite)
9. Psalter and Lessons Rubrics
10. Canticles after the Lessons
11. Apostles’ Creed
12. Suffrages and Collects Rubrics
13. Suffrages and Collects Text
14. Additional Prayers and Thanksgivings Rubrics
15. Additional Prayers and Thanksgivings Text
16. Closing Rubric
17. Closing Grace Text

## Run locally

```bash
python3 app.py
```

Open <http://localhost:8000>.

## UI behavior

- The app displays each unit in a dedicated card with **1662** on the left and **1928** on the right.
- A diff toggle enables/disables word-level highlights.
- View settings include:
  - unit search/filter,
  - base font size,
  - compact spacing mode.
- View settings persist in the local browser using `localStorage`.

## Notes on source retrieval

This environment blocked direct HTTPS access to common source hosts during this run. The app preserves the URLs that were attempted and includes normalized public-domain text in the dataset.
