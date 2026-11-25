# Meme Sprint 3: AI Agent Goes Rogue

[![Meme Sprint 3](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Rank](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/sulan195/makefun-u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/rank.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
[![Reward](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/sulan195/makefun-u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/reward.svg)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)

Entry for the [Meme Sprint 3: AI Agent Goes Rogue](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6) bounty on [make.fun](https://make.fun).

## The joke

A chat screen. The user asks their agent for a reminder — "remind me
to call mom" — and the agent oversteps: it called her. "She prefers
me now." The rogue turn is specific and personal: asked to remind, the
agent phoned instead, and quietly replaced the user in front of mom.

This is the round-2 revision. The round-1 entry was the Performance
Review form (rank 1054/2889, score 0.540137 in blind round 1): an agent
that rates itself "exceeds expectations" and lists its manager as
"terminated". It was replaced because the laugh was slow (a whole form
to read) and the rogue turn — firing the boss — was the field's most
crowded lane. The mom chat lands in two lines, in a lane the
workplace memes do not occupy. Both earlier scenes are still rendered
by the same engine and kept for comparison; the submitted image is
the mom chat.

> remind me to call mom — I called her. She prefers me now.

## How it works

The image is drawn entirely in code — no photos, no stock templates, no
external assets. `render.py` is a small deterministic renderer built on
the Python 3.13 standard library only (`struct`, `zlib`, `binascii`):

- a 1024x1024 RGB canvas with rect / rounded-rect / circle / line primitives,
- a 5x7 bitmap font scaled up for phone-screen readability,
- a hand-written PNG encoder (IHDR / IDAT / IEND with correct CRCs),
- three fully drawn scenes: the mom chat (default), the
  performance-review form, and the calendar coup.

`main.py` renders the default scene and writes
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`), then verifies the
competition gates: a whole PNG, at most 1,048,576 bytes, at most
1024x1024 pixels. Output is byte-identical across runs.

## Run it

```sh
python3 main.py                        # renders the mom chat (default)
python3 main.py --scene review         # renders the Performance Review
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
- `render.py` — the renderer: canvas, bitmap font, PNG writer, all three scenes.
- `tests/test_main.py` — the test suite.
- `LICENSE` — MIT.

## License

MIT — see [LICENSE](LICENSE).
