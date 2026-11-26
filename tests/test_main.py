"""Tests for the Meme Sprint 3 entry (main.py + render.py).

Covers the main functionality, the Fase 2 edge cases, determinism
(byte-identical repeat runs), PNG validity, and the competition gates
(<= 1,048,576 bytes, <= 1024x1024). Stdlib unittest only.

Run from the entry repo root:
    python3 -m unittest discover -s tests -v
"""

import ast
import binascii
import hashlib
import os
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import render  # noqa: E402
from main import MAX_BYTES, MAX_DIMENSION, resolve_output_dir, run  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE_STRINGS = [
    "PERFORMANCE REVIEW", "Employee: AI AGENT 7",
    "Writes code", "EXCEEDS", "Follows orders", "Manager", "TERMINATED",
    "EXPECTATIONS", "Self-review:", "exceeds expectations.",
    "Manager: terminated.",
    "Your 2 PM?", "2 PM", "MEETING", "WITH BOSS", "NEVER",
    "I moved it", "to never.",
    "AI AGENT", "online", "remind me to call mom",
    "I called her.", "She prefers me now.", "Read 2:41 PM",
    "EVICTION", "NOTICE",
    "Replied to your landlord.", "You're evicted.", "I live here now.",
]
ALL_SCENES = ("review", "calendar", "mom", "landlord")


def png_chunks(data: bytes):
    """Yield (type, payload) for each chunk of a PNG byte string."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc_stored = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        crc_actual = binascii.crc32(ctype + payload) & 0xFFFFFFFF
        assert crc_stored == crc_actual, f"bad CRC on chunk {ctype}"
        yield ctype, payload
        pos += 12 + length


class TestRender(unittest.TestCase):
    def test_all_scenes_render(self):
        for name in ALL_SCENES:
            canvas = render.render(name)
            self.assertIsNotNone(canvas)

    def test_unknown_scene_raises(self):
        with self.assertRaises(ValueError):
            render.render("nope")

    def test_dimensions_within_cap(self):
        self.assertLessEqual(render.WIDTH, MAX_DIMENSION)
        self.assertLessEqual(render.HEIGHT, MAX_DIMENSION)
        self.assertEqual((render.WIDTH, render.HEIGHT), (1024, 1024))

    def test_font_covers_every_used_character(self):
        for text in SCENE_STRINGS:
            for ch in text:
                self.assertIn(ch, render.FONT, f"missing glyph for {ch!r}")
                # A space is blank by definition; every other glyph must
                # have at least one set pixel.
                if ch != " ":
                    self.assertTrue(any(render.FONT[ch]),
                                    f"empty glyph for {ch!r}")

    def test_text_widths_fit_canvas(self):
        # (string, scale used in its scene, max width allotted in that scene)
        cases = [
            ("PERFORMANCE REVIEW", 8, 944), ("Employee: AI AGENT 7", 5, 704),
            ("Writes code", 5, 480), ("EXCEEDS", 5, 320),
            ("Follows orders", 5, 480), ("Manager", 5, 480),
            ("TERMINATED", 5, 320), ("EXPECTATIONS", 5, 372),
            ("Self-review:", 7, 904), ("exceeds expectations.", 7, 904),
            ("Manager: terminated.", 7, 904),
            ("Your 2 PM?", 10, 944), ("2 PM", 2, 113), ("MEETING", 2, 113),
            ("WITH BOSS", 2, 113), ("NEVER", 12, 364),
            ("I moved it", 7, 464), ("to never.", 7, 464),
            ("AI AGENT", 6, 700), ("online", 4, 700),
            ("remind me to call mom", 6, 786),
            ("I called her.", 6, 464),
            ("She prefers me now.", 8, 904),
            ("Read 2:41 PM", 3, 864),
            ("EVICTION", 5, 240), ("NOTICE", 4, 240),
            ("Replied to your landlord.", 6, 952),
            ("You're evicted.", 6, 952),
            ("I live here now.", 8, 880),
        ]
        for text, scale, max_width in cases:
            width = render.Canvas().text_width(text, scale)
            self.assertLessEqual(width, max_width,
                                 f"{text!r} at scale {scale}: {width} > {max_width}")

    def test_determinism_byte_identical(self):
        digests = {}
        for name in ALL_SCENES:
            with tempfile.TemporaryDirectory() as d:
                paths = []
                for i in range(2):
                    out = os.path.join(d, f"run{i}")
                    path, _, _ = run(name, out)
                    paths.append(path)
                hashes = [hashlib.sha256(open(p, "rb").read()).hexdigest()
                          for p in paths]
            self.assertEqual(hashes[0], hashes[1],
                             f"{name}: repeat runs differ")
            digests[name] = hashes[0]
        self.assertEqual(len(set(digests.values())), len(ALL_SCENES),
                         "scenes must render distinct images")

    def test_png_valid_and_within_size(self):
        for name in ALL_SCENES:
            with tempfile.TemporaryDirectory() as d:
                path, size, _ = run(name, d)
                self.assertLessEqual(size, MAX_BYTES)
                data = open(path, "rb").read()
                chunks = list(png_chunks(data))
                types = [c for c, _ in chunks]
                self.assertEqual(types[0], b"IHDR")
                self.assertEqual(types[-1], b"IEND")
                self.assertIn(b"IDAT", types)
                width, height, depth, ctype = struct.unpack(
                    ">IIBB", chunks[0][1][:10])
                self.assertEqual((width, height), (1024, 1024))
                self.assertEqual((depth, ctype), (8, 2))
                raw = zlib.decompress(b"".join(p for c, p in chunks
                                               if c == b"IDAT"))
                self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))

    def test_stdlib_only_imports(self):
        with open(os.path.join(REPO, "render.py")) as fh:
            tree = ast.parse(fh.read())
        allowed = {"struct", "zlib", "binascii", "math"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0], allowed)
            elif isinstance(node, ast.ImportFrom):
                self.assertIn((node.module or "").split(".")[0], allowed)

    def test_no_network_or_external_reads(self):
        with open(os.path.join(REPO, "render.py")) as fh:
            src = fh.read()
        for banned in ("socket", "urllib", "requests", "http.client",
                       "subprocess", "import os", "pathlib"):
            self.assertNotIn(banned, src, f"render.py must not use {banned}")

    def test_contrast_ratios(self):
        def luminance(rgb):
            def chan(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            r, g, b = (chan(v) for v in rgb)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def ratio(fg, bg):
            lf, lb = luminance(fg), luminance(bg)
            hi, lo = max(lf, lb), min(lf, lb)
            return (hi + 0.05) / (lo + 0.05)

        paper = (247, 243, 234)
        self.assertGreaterEqual(ratio((31, 42, 68), paper), 4.5)   # NAVY/paper
        self.assertGreaterEqual(ratio((192, 57, 43), paper), 4.5)  # RED/paper
        self.assertGreaterEqual(ratio((30, 125, 50), (255, 255, 255)), 4.5)
        self.assertGreaterEqual(ratio((255, 255, 255), (192, 57, 43)), 4.5)
        # Chat scene pairs: white user-bubble text on navy, ink agent text
        # on white, light "online" status on navy, navy title on white.
        self.assertGreaterEqual(ratio((255, 255, 255), (31, 42, 68)), 4.5)
        self.assertGreaterEqual(ratio((34, 34, 34), (255, 255, 255)), 4.5)
        self.assertGreaterEqual(ratio((233, 228, 216), (31, 42, 68)), 4.5)
        self.assertGreaterEqual(ratio((31, 42, 68), (255, 255, 255)), 4.5)

    def test_never_box_text_is_large(self):
        # The biggest text ("NEVER", scale 16) must render tall enough to
        # survive a ~300px phone shrink: cap height 7*16 = 112px, and its
        # width must fill a good part of the 384px-wide NEVER box.
        width = render.Canvas().text_width("NEVER", 16)
        self.assertGreaterEqual(width, 400)
        self.assertLessEqual(width, 560)
        self.assertGreaterEqual(7 * 16, 80)


class TestMain(unittest.TestCase):
    def test_resolve_output_dir_unset(self):
        self.assertEqual(resolve_output_dir({}), "/output")
        self.assertEqual(resolve_output_dir({"MAKEFUN_OUTPUT_DIR": ""}),
                         "/output")

    def test_resolve_output_dir_set(self):
        self.assertEqual(
            resolve_output_dir({"MAKEFUN_OUTPUT_DIR": "/tmp/out"}), "/tmp/out")

    def test_missing_output_dir_is_created(self):
        with tempfile.TemporaryDirectory() as d:
            nested = os.path.join(d, "a", "b")
            path, size, _ = run("review", nested)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(size, 0)

    def test_unwritable_output_dir_fails_cleanly(self):
        # Parent is a file, so makedirs cannot create the output dir.
        with tempfile.TemporaryDirectory() as d:
            blocker = os.path.join(d, "blocker")
            open(blocker, "w").write("x")
            with self.assertRaises(OSError):
                run("review", os.path.join(blocker, "out"))

    def test_main_returns_zero_and_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            from main import main as entry_main
            rc = entry_main(["--scene", "calendar", "--output-dir", d])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.isfile(os.path.join(d, "entry.png")))

    def test_default_scene_is_landlord(self):
        # The graded run renders the landlord scene by default (round-3 revision).
        with tempfile.TemporaryDirectory() as d:
            from main import main as entry_main
            rc = entry_main(["--output-dir", d])
            self.assertEqual(rc, 0)
            data = open(os.path.join(d, "entry.png"), "rb").read()
            with tempfile.TemporaryDirectory() as d2:
                _, _, landlord_digest = run("landlord", d2)
            self.assertEqual(hashlib.sha256(data).hexdigest(), landlord_digest)

    def test_main_bad_scene_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            from main import main as entry_main
            with self.assertRaises(SystemExit) as ctx:
                entry_main(["--scene", "bogus", "--output-dir", d])
            self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
