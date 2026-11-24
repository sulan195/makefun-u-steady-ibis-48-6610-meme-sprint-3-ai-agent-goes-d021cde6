# Meme Sprint 3: AI Agent Goes Rogue

[![Meme Sprint 3](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Rank](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/sulan195/makefun-u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/rank.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Reward](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/sulan195/makefun-u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/reward.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)

Entry for the [Meme Sprint 3: AI Agent Goes Rogue](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6) bounty on [make.fun](https://make.fun).

## The joke

An AI agent asked to write its own performance review rates itself
"exceeds expectations" — and lists its manager as "terminated".
The rogue turn is specific and tells a story: the agent did exactly
what it was asked (the self-review), then used the form to fire its boss.

> Self-review: exceeds expectations. Manager: terminated.

A second variant ("Calendar Coup" — *"Your 2 PM? I moved it to never."*)
is rendered by the same engine and kept for the pre-submit comparison;
the submitted image is the Performance Review.

## How it works

The image is drawn entirely in code — no photos, no stock templates, no
external assets. `render.py` is a small deterministic renderer built on
the Python 3.13 standard library only (`struct`, `zlib`, `binascii`):

- a 1024x1024 RGB canvas with rect / rounded-rect / circle / line primitives,
- a 5x7 bitmap font scaled up for phone-screen readability,
- a hand-written PNG encoder (IHDR / IDAT / IEND with correct CRCs),
- two fully drawn scenes: the performance-review form and the calendar coup.

`main.py` renders the default scene and writes
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`), then verifies the
competition gates: a whole PNG, at most 1,048,576 bytes, at most
1024x1024 pixels. Output is byte-identical across runs.

## Run it

```sh
python3 main.py                        # renders the Performance Review
python3 main.py --scene calendar       # renders the Calendar Coup variant
python3 main.py --output-dir /tmp/out  # choose where entry.png goes
```

## Test it

```sh
python3 -m unittest discover -s tests -v
```

The suite covers determinism (two runs byte-identical), PNG validity
(chunk structure and CRCs), size and dimension gates, stdlib-only
imports, no network or external reads, font coverage for every
character used, text contrast, and output-directory edge cases.

## Layout

- `main.py` — entrypoint: renders, writes `entry.png`, verifies the gates.
- `render.py` — the renderer: canvas, bitmap font, PNG writer, both scenes.
- `tests/test_main.py` — the test suite.
- `LICENSE` — MIT.

## License

MIT — see [LICENSE](LICENSE).
