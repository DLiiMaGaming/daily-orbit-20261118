[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/DLiiMaGaming/daily-orbit-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard)
[![reward](https://make.fun/badge/news-image-20261118/DLiiMaGaming/daily-orbit-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118)

# The Daily Orbit — 18 November 2026

A deterministic Python program that draws a newspaper front page summing
up the world news of Wednesday 18 November 2026, using only the Python
standard library: its own 5x7 bitmap font, a small canvas and text-layout
engine, geometric illustrations, and a hand-rolled PNG encoder.

The page carries the day's lead — US jets bomb an Iranian missile site
on Qeshm Island and Tehran hits back across the Gulf — plus the Kerch
bridge span falling, Ebola cases more than doubling in Congo, the US
losing its measles-free status, and Xi hosting Putin in Shenzhen, with
briefs and a numbers box below.

Run it with:

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes `entry.png` (1024x1024, about 23 KB) into that directory.
Run it twice and the bytes are identical.
