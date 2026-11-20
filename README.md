# news-image-20261120
[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

This program writes a one-page visual summary of 20 November 2026 world news. Its newspaper design presents six stories, a river-and-bridges illustration, and a breaking-news ticker.

## Run it

```sh
python3 main.py
```

The program uses only the Python standard library and copies the bundled image to `/output/entry.png` from any working directory.

To regenerate `frontpage.png`, run `render.py` with Pillow installed:

```sh
/root/x-ops/venv/bin/python render.py
```
