[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/DLiiMaGaming/daily-orbit-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard)
[![reward](https://make.fun/badge/news-image-20261118/DLiiMaGaming/daily-orbit-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118)

# The Daily Orbit — 18 November 2026

One Python file, standard library only, that paints the front page of
a newspaper for Wednesday 18 November 2026 and saves it as a PNG.
Letters are drawn from a 5x7 bitmap font stored as row bitmasks, the
page is assembled on a small canvas class, and the PNG bytes are packed
by hand with zlib — no packages, no network, no clock.

What the page shows: the Gulf lead (US jets hit an Iranian missile
site on Qeshm Island; Tehran answers across the Gulf), the Kerch
bridge span coming down, Ebola passing 11,000 cases in Congo, the US
losing measles-free status, and Xi hosting Putin in Shenzhen — plus
briefs and a day-in-numbers box.

Run it with:

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `entry.png` (1024x1024) into `out/`. Running it twice
produces byte-identical files.
