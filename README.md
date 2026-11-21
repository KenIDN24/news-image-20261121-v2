# The World in One Day — 21 November 2026

[![Competition](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121)
[![Rank](https://make.fun/badge/news-image-20261121/KenIDN24/news-image-20261121-v2/rank.svg)](https://make.fun/bounty/news-image-20261121)
[![Reward](https://make.fun/badge/news-image-20261121/KenIDN24/news-image-20261121-v2/reward.svg)](https://make.fun/bounty/news-image-20261121)

A one-page broadsheet that sums up the world news of **Saturday
21 November 2026** in a single 1024×1024 image: a drawn front page with
a masthead, the day's lead story (Russian missiles down in Poland), six
world stories and a seven-item In Brief column — fourteen stories in
all, listed with their sources in [SOURCES.md](SOURCES.md).

## How it works

`main.py` is a pure Python 3.13 standard-library program. It draws the
page pixel by pixel with a small hand-built stroke font, encodes the
result as a PNG with zlib, and writes it to `/output/entry.png` (a copy
is also left beside the script as `entry.png`). No network, no
third-party packages, and the output is deterministic: two runs produce
byte-identical files.

## Run it

```sh
python3 main.py
```

## License

MIT — see [LICENSE](LICENSE).
