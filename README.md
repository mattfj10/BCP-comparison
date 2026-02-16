# BCP Morning Prayer Comparator

This project compares the **Morning Prayer office** of the **1662 Book of Common Prayer** and the **1928 Book of Common Prayer** in a side-by-side web interface.

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

The canonical comparison data is stored in `data/morning_prayer.json`, now populated with full text in each comparison unit rather than abbreviated excerpts.

## Run locally

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>.

## UI behavior

- Main comparison page is at `/`.
- The app displays each unit in a dedicated card with **1662** on the left and **1928** on the right.
- A diff toggle enables/disables word-level highlights.
- A built-in data-URI favicon avoids noisy `/favicon.ico` 404 errors in simple static servers.

## Notes on source retrieval

This environment blocked direct HTTPS access to common source hosts during this run. The app preserves the URLs that were attempted and includes normalized public-domain text in the dataset.
