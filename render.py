"""Deterministic 1024x1024 PNG meme renderer using the Python standard library."""

import binascii
import math
import struct
import zlib

# Canvas dimensions and color palette
WIDTH = 1024
HEIGHT = 1024

Color = tuple[int, int, int]

PAPER: Color = (247, 243, 234)
NAVY: Color = (31, 42, 68)
INK: Color = (34, 34, 34)
GREEN: Color = (30, 125, 50)
RED: Color = (192, 57, 43)
WHITE: Color = (255, 255, 255)
BORDER: Color = (201, 194, 180)
LIGHT: Color = (233, 228, 216)
YELLOW: Color = (245, 197, 24)

# 5x7 bitmap font (7 rows per glyph, low 5 bits per row, bit 4 = leftmost pixel)
FONT: dict[str, tuple[int, ...]] = {
    " ": (0, 0, 0, 0, 0, 0, 0),
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 14),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 18, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 17, 25, 21, 19, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (14, 17, 16, 14, 1, 17, 14),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "a": (0, 0, 14, 1, 15, 17, 15),
    "b": (16, 16, 22, 25, 17, 17, 30),
    "c": (0, 0, 14, 17, 16, 17, 14),
    "d": (1, 1, 13, 19, 17, 17, 15),
    "e": (0, 0, 14, 17, 31, 16, 14),
    "f": (6, 9, 8, 28, 8, 8, 8),
    "g": (0, 0, 15, 17, 15, 1, 14),
    "h": (16, 16, 22, 25, 17, 17, 17),
    "i": (0, 4, 0, 12, 4, 4, 14),
    "j": (0, 2, 0, 6, 2, 18, 12),
    "k": (16, 16, 18, 20, 24, 20, 18),
    "l": (12, 4, 4, 4, 4, 4, 14),
    "m": (0, 0, 26, 21, 21, 17, 17),
    "n": (0, 0, 22, 25, 17, 17, 17),
    "o": (0, 0, 14, 17, 17, 17, 14),
    "p": (0, 0, 30, 17, 30, 16, 16),
    "q": (0, 0, 15, 17, 15, 1, 1),
    "r": (0, 0, 22, 25, 16, 16, 16),
    "s": (0, 0, 15, 16, 14, 1, 30),
    "t": (8, 8, 28, 8, 8, 9, 6),
    "u": (0, 0, 17, 17, 17, 19, 13),
    "v": (0, 0, 17, 17, 17, 10, 4),
    "w": (0, 0, 17, 17, 21, 21, 10),
    "x": (0, 0, 17, 10, 4, 10, 17),
    "y": (0, 0, 17, 17, 15, 1, 14),
    "z": (0, 0, 31, 2, 4, 8, 31),
    "0": (14, 17, 17, 17, 17, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "3": (14, 17, 1, 6, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 6, 4, 0, 4),
    "-": (0, 0, 0, 31, 0, 0, 0),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "&": (12, 18, 20, 8, 21, 18, 13),
    '"': (10, 10, 10, 0, 0, 0, 0),
    "%": (25, 25, 2, 4, 8, 19, 19),
}


# RGB software rasterizer canvas
class Canvas:
    """In-memory RGB canvas backed by a row-major bytearray buffer."""

    def __init__(self, w: int = WIDTH, h: int = HEIGHT, bg: Color = (247, 243, 234)) -> None:
        if w <= 0 or h <= 0:
            raise ValueError("Canvas dimensions must be positive")
        self.w: int = int(w)
        self.h: int = int(h)
        r, g, b = bg
        self.pixels: bytearray = bytearray((r, g, b)) * (self.w * self.h)

    @property
    def width(self) -> int:
        return self.w

    @property
    def height(self) -> int:
        return self.h

    @property
    def buf(self) -> bytearray:
        return self.pixels

    @property
    def data(self) -> bytearray:
        return self.pixels

    def set(self, x: int, y: int, color: Color) -> None:
        """Set a single pixel, clipping silently if out of bounds."""
        if 0 <= x < self.w and 0 <= y < self.h:
            idx = (y * self.w + x) * 3
            self.pixels[idx] = color[0]
            self.pixels[idx + 1] = color[1]
            self.pixels[idx + 2] = color[2]

    def fill(self, color: Color) -> None:
        """Fill the entire canvas with a solid RGB color."""
        r, g, b = color
        self.pixels[:] = bytes((r, g, b)) * (self.w * self.h)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        """Draw a filled rectangle [x0, x1) x [y0, y1), clipping silently."""
        cx0 = max(0, x0)
        cy0 = max(0, y0)
        cx1 = min(self.w, x1)
        cy1 = min(self.h, y1)
        if cx0 >= cx1 or cy0 >= cy1:
            return
        span = cx1 - cx0
        r, g, b = color
        row_bytes = bytes((r, g, b)) * span
        span3 = span * 3
        w = self.w
        pixels = self.pixels
        for y in range(cy0, cy1):
            start = (y * w + cx0) * 3
            pixels[start : start + span3] = row_bytes

    def rounded_rect(self, x0: int, y0: int, x1: int, y1: int, r: int, color: Color) -> None:
        """Draw a filled rounded rectangle [x0, x1) x [y0, y1), clipping silently."""
        if x0 >= x1 or y0 >= y1:
            return
        if r <= 0:
            self.rect(x0, y0, x1, y1, color)
            return
        rad = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
        if rad <= 0:
            self.rect(x0, y0, x1, y1, color)
            return
        self.rect(x0, y0 + rad, x1, y1 - rad, color)
        r2_4 = 4 * rad * rad
        for j in range(rad):
            dy2 = 2 * j + 1
            rem = r2_4 - dy2 * dy2
            span = (math.isqrt(rem) + 1) // 2
            lx = x0 + rad - span
            rx = x1 - rad + span
            ty = y0 + rad - 1 - j
            by = y1 - rad + j
            self.rect(lx, ty, rx, ty + 1, color)
            self.rect(lx, by, rx, by + 1, color)

    def circle(self, cx: int, cy: int, r: int, color: Color) -> None:
        """Draw a filled circle centered at (cx, cy) with radius r."""
        if r < 0:
            return
        if r == 0:
            self.set(cx, cy, color)
            return
        dy_min = max(-r, -cy)
        dy_max = min(r, self.h - 1 - cy)
        r2 = r * r
        for dy in range(dy_min, dy_max + 1):
            dx = math.isqrt(r2 - dy * dy)
            y = cy + dy
            self.rect(cx - dx, y, cx + dx + 1, y + 1, color)

    def triangle(self, apex: tuple[int, int], base_left: tuple[int, int],
                 base_right: tuple[int, int], color: Color) -> None:
        """Fill an upright triangle (apex above the base) by scanlines."""
        ax, ay = apex
        bx, by = base_left
        cx, cy = base_right
        if by != cy or ay >= by:
            return
        for y in range(ay, by + 1):
            t = (y - ay) / max(1, by - ay)
            left = round(ax + (bx - ax) * t)
            right = round(ax + (cx - ax) * t)
            self.rect(min(left, right), y, max(left, right) + 1, y + 1, color)

    def line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: Color,
        width: int = 1,
    ) -> None:
        """Draw a Bresenham line with square caps of the given stroke width."""
        if width <= 0:
            return
        if (
            max(x0, x1) + width < 0
            or min(x0, x1) - width >= self.w
            or max(y0, y1) + width < 0
            or min(y0, y1) - width >= self.h
        ):
            return
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = (width - 1) // 2
        x, y = x0, y0
        while True:
            if width == 1:
                self.set(x, y, color)
            else:
                bx = x - half
                by = y - half
                self.rect(bx, by, bx + width, by + width, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def text_width(self, s: str, scale: int) -> int:
        """Compute pixel width of string s rendered at the given integer scale."""
        for ch in s:
            if ch not in FONT:
                raise ValueError(f"Unknown character in FONT: {ch}")
        if not s or scale <= 0:
            return 0
        return (6 * len(s) - 1) * scale

    def text(
        self,
        x: int,
        y: int,
        s: str,
        color: Color,
        scale: int,
        align: str = "left",
    ) -> None:
        """Render string s with the 5x7 bitmap font; raises ValueError for unknown chars."""
        w = self.text_width(s, scale)
        if align == "left":
            start_x = x
        elif align == "center":
            start_x = x - w // 2
        elif align == "right":
            start_x = x - w
        else:
            raise ValueError(f"Unsupported text align mode: {align}")
        if not s or scale <= 0:
            return
        cursor_x = start_x
        step = 6 * scale
        for ch in s:
            glyph = FONT[ch]
            for row_idx, row_bits in enumerate(glyph):
                if row_bits:
                    py0 = y + row_idx * scale
                    py1 = py0 + scale
                    for col_idx in range(5):
                        if (row_bits >> (4 - col_idx)) & 1:
                            px0 = cursor_x + col_idx * scale
                            self.rect(px0, py0, px0 + scale, py1, color)
            cursor_x += step


# Deterministic PNG encoder
def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Pack a single PNG chunk with big-endian length and IEEE CRC32."""
    crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_png(canvas: Canvas, path: str) -> None:
    """Write canvas as a deterministic RGB PNG file (color type 2, bit depth 8)."""
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    stride = canvas.w * 3
    dst_stride = stride + 1
    raw = bytearray(dst_stride * canvas.h)
    src = memoryview(canvas.pixels)
    for y in range(canvas.h):
        src_off = y * stride
        dst_off = y * dst_stride
        raw[dst_off] = 0
        raw[dst_off + 1 : dst_off + dst_stride] = src[src_off : src_off + stride]
    compressed = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(_png_chunk(b"IHDR", ihdr))
        fh.write(_png_chunk(b"IDAT", compressed))
        fh.write(_png_chunk(b"IEND", b""))


# Friendly geometric robot character (no red eyes)
def draw_robot(
    canvas: Canvas,
    cx: int,
    cy: int,
    s: int,
    body: Color = (31, 42, 68),
    accent: Color = (30, 125, 50),
) -> None:
    """Draw a friendly geometric robot with head half-size s around (cx, cy)."""
    if s <= 0:
        return
    head_top = cy - (s * 17) // 20
    head_bot = cy + (s * 13) // 20
    head_r = max(2, s // 4)

    # Antenna stalk and accent tip
    ant_y = cy - (s * 27) // 20
    ant_w = max(2, s // 10)
    tip_r = max(2, s // 6)
    canvas.line(cx, ant_y, cx, head_top, body, width=ant_w)
    canvas.circle(cx, ant_y, tip_r, accent)

    # Rounded-rect head
    canvas.rounded_rect(cx - s, head_top, cx + s, head_bot, head_r, body)

    # Round white eyes with dark non-red pupils
    eye_dx = max(2, (s * 21) // 50)
    eye_y = cy - (s * 11) // 50
    eye_r = max(2, (s * 6) // 25)
    pupil_r = max(1, (s * 11) // 100)
    pupil_shift = max(0, s // 24)
    canvas.circle(cx - eye_dx, eye_y, eye_r, WHITE)
    canvas.circle(cx + eye_dx, eye_y, eye_r, WHITE)
    canvas.circle(cx - eye_dx + pupil_shift, eye_y, pupil_r, body)
    canvas.circle(cx + eye_dx + pupil_shift, eye_y, pupil_r, body)

    # Friendly straight-line mouth
    mouth_dx = max(2, (s * 19) // 50)
    mouth_y = cy + (s * 7) // 25
    mouth_w = max(2, s // 11)
    canvas.line(cx - mouth_dx, mouth_y, cx + mouth_dx, mouth_y, WHITE, width=mouth_w)

    # Small body rectangle below head with accent stripe
    body_dx = max(3, (s * 17) // 25)
    body_top = head_bot + max(2, s // 14)
    body_bot = cy + (s * 27) // 20
    body_r = max(2, s // 8)
    canvas.rounded_rect(cx - body_dx, body_top, cx + body_dx, body_bot, body_r, body)
    stripe_dx = max(2, (s * 7) // 20)
    stripe_pad = max(1, (body_bot - body_top) // 4)
    if body_top + stripe_pad < body_bot - stripe_pad:
        canvas.rect(
            cx - stripe_dx,
            body_top + stripe_pad,
            cx + stripe_dx,
            body_bot - stripe_pad,
            accent,
        )


def _assert_fits(canvas: Canvas, s: str, scale: int, max_width: int) -> None:
    """Ensure rendered string s at scale does not exceed max_width."""
    w = canvas.text_width(s, scale)
    if w > max_width:
        raise ValueError(f"Text {s!r} at scale {scale} has width {w} > {max_width}")


# Scene A: Performance Review
def scene_review() -> Canvas:
    """Render Scene A ('review'): AI agent self-review meme."""
    c = Canvas(WIDTH, HEIGHT, PAPER)

    # Headline
    headline = "PERFORMANCE REVIEW"
    _assert_fits(c, headline, 8, WIDTH - 80)
    c.text(WIDTH // 2, 58, headline, NAVY, 8, align="center")

    # Form card with 4px NAVY border
    c.rounded_rect(80, 130, 944, 600, 16, NAVY)
    c.rounded_rect(84, 134, 940, 596, 12, WHITE)

    # Employee header row and divider
    draw_robot(c, 150, 195, 34)
    emp_text = "Employee: AI AGENT 7"
    _assert_fits(c, emp_text, 5, 914 - 210)
    c.text(210, 178, emp_text, NAVY, 5, align="left")
    c.line(110, 250, 914, 250, NAVY, width=3)

    # Subtle row separators for glanceability
    c.rect(120, 347, 894, 349, LIGHT)
    c.rect(120, 427, 894, 429, LIGHT)

    # Rating rows (labels left at x=120, values + check/X circles on right)
    rows: list[tuple[int, str, str, Color, bool]] = [
        (290, "Writes code", "EXCEEDS", GREEN, True),
        (370, "Follows orders", "EXCEEDS", GREEN, True),
        (450, "Manager", "TERMINATED", RED, False),
    ]
    badge_cx = 876
    badge_r = 18
    val_right_x = 840
    for ry, label, val, val_color, is_check in rows:
        _assert_fits(c, label, 5, 480)
        _assert_fits(c, val, 5, 320)
        c.text(120, ry, label, INK, 5, align="left")
        c.text(val_right_x, ry, val, val_color, 5, align="right")
        bcy = ry + 17
        c.circle(badge_cx, bcy, badge_r, val_color)
        if is_check:
            c.line(badge_cx - 8, bcy + 1, badge_cx - 2, bcy + 7, WHITE, width=4)
            c.line(badge_cx - 2, bcy + 7, badge_cx + 9, bcy - 6, WHITE, width=4)
        else:
            c.line(badge_cx - 7, bcy - 7, badge_cx + 7, bcy + 7, WHITE, width=4)
            c.line(badge_cx - 7, bcy + 7, badge_cx + 7, bcy - 7, WHITE, width=4)

    # Double-border green stamp overlapping the bottom edge of the form
    sx0, sy0, sx1, sy1 = 532, 494, 928, 614
    c.rounded_rect(sx0, sy0, sx1, sy1, 14, GREEN)
    c.rounded_rect(sx0 + 4, sy0 + 4, sx1 - 4, sy1 - 4, 10, WHITE)
    c.rounded_rect(sx0 + 10, sy0 + 10, sx1 - 10, sy1 - 10, 6, GREEN)
    c.rounded_rect(sx0 + 12, sy0 + 12, sx1 - 12, sy1 - 12, 4, WHITE)

    stamp_cx = (sx0 + sx1) // 2
    stamp_inner_w = (sx1 - sx0) - 24
    for sy, sline in ((514, "EXCEEDS"), (557, "EXPECTATIONS")):
        _assert_fits(c, sline, 5, stamp_inner_w)
        c.text(stamp_cx, sy, sline, GREEN, 5, align="center")

    # Three-line punchline below the form (must fit within x=60..964)
    max_punch_w = 964 - 60
    punchlines: list[tuple[int, str, Color]] = [
        (680, "Self-review:", NAVY),
        (750, "exceeds expectations.", NAVY),
        (820, "Manager: terminated.", RED),
    ]
    for py, pline, pcolor in punchlines:
        _assert_fits(c, pline, 7, max_punch_w)
        c.text(WIDTH // 2, py, pline, pcolor, 7, align="center")

    return c


# Scene B: Calendar Coup
def scene_calendar() -> Canvas:
    """Render Scene B ('calendar'): AI agent moves 2 PM boss meeting to NEVER."""
    c = Canvas(WIDTH, HEIGHT, PAPER)

    # Headline
    headline = "Your 2 PM?"
    _assert_fits(c, headline, 10, WIDTH - 80)
    c.text(WIDTH // 2, 72, headline, NAVY, 10, align="center")

    # 7x4 calendar grid (cell 123x97, 1px gaps, 2px BORDER outline)
    grid_x0 = 80
    grid_y0 = 170
    cell_w = 123
    cell_h = 97
    step_x = cell_w + 1
    step_y = cell_h + 1

    for row in range(4):
        for col in range(7):
            cx0 = grid_x0 + col * step_x
            cy0 = grid_y0 + row * step_y
            cx1 = cx0 + cell_w
            cy1 = cy0 + cell_h
            c.rect(cx0, cy0, cx1, cy1, BORDER)
            c.rect(cx0 + 2, cy0 + 2, cx1 - 2, cy1 - 2, WHITE)
            day_str = str(row * 7 + col + 1)
            _assert_fits(c, day_str, 3, cell_w - 16)
            c.text(cx0 + 8, cy0 + 7, day_str, INK, 3, align="left")

    # Highlighted cell at column 3, row 1 (Day 11)
    hx0 = grid_x0 + 3 * step_x
    hy0 = grid_y0 + 1 * step_y
    hx1 = hx0 + cell_w
    hy1 = hy0 + cell_h
    c.rect(hx0, hy0, hx1, hy1, RED)
    c.rect(hx0 + 5, hy0 + 5, hx1 - 5, hy1 - 5, WHITE)
    c.text(hx0 + 8, hy0 + 7, "11", INK, 3, align="left")

    hcx = (hx0 + hx1) // 2
    cell_inner_w = cell_w - 10
    for offset_y, mline in ((31, "2 PM"), (51, "MEETING"), (71, "WITH BOSS")):
        _assert_fits(c, mline, 2, cell_inner_w)
        c.text(hcx, hy0 + offset_y, mline, RED, 2, align="center")

    # Diagonal red strike across the highlighted cell
    c.line(hx0 + 8, hy1 - 9, hx1 - 9, hy0 + 8, RED, width=5)

    # NEVER destination box and centered label
    nx0, ny0, nx1, ny1 = 560, 620, 944, 860
    c.rounded_rect(nx0, ny0, nx1, ny1, 20, RED)
    never_label = "NEVER"
    _assert_fits(c, never_label, 12, (nx1 - nx0) - 20)
    c.text((nx0 + nx1) // 2, 698, never_label, WHITE, 12, align="center")

    # Thick red arrow from highlighted cell's bottom-right to NEVER box's top-left
    ax0, ay0 = hx1, hy1
    ax1, ay1 = nx0 + 18, ny0 - 2
    c.line(ax0, ay0, ax1, ay1, RED, width=6)
    c.line(ax1, ay1, ax1 - 20, ay1 - 24, RED, width=6)
    c.line(ax1, ay1, ax1 + 18, ay1 - 24, RED, width=6)

    # Robot positioned near the calendar drag path
    draw_robot(c, 430, 500, 30)

    # Left-aligned two-line punchline
    for py, pline in ((660, "I moved it"), (730, "to never.")):
        _assert_fits(c, pline, 7, nx0 - 96)
        c.text(80, py, pline, NAVY, 7, align="left")

    return c


# Scene C: Call Mom
def scene_mom() -> Canvas:
    """Render Scene C ('mom'): user asks for a reminder; the agent called
    mom instead — and mom prefers the agent now.

    A chat screen: light header with the agent's avatar and "online"
    status, the user's request in a navy bubble, the agent's reply in
    white bubbles, and the punchline ("She prefers me now.") big in a
    green-framed bubble. The rogue turn is the agent overstepping a
    reminder into a phone call — and quietly replacing the user with mom.
    """
    c = Canvas(WIDTH, HEIGHT, PAPER)

    # Chat header: white bar with divider, robot avatar, name + status.
    c.rect(0, 0, WIDTH, 120, WHITE)
    c.rect(0, 118, WIDTH, 120, BORDER)
    draw_robot(c, 78, 62, 34)
    _assert_fits(c, "AI AGENT", 6, 700)
    c.text(140, 34, "AI AGENT", NAVY, 6, align="left")
    _assert_fits(c, "online", 4, 700)
    c.text(140, 82, "online", GREEN, 4, align="left")

    # User bubble (right, navy): the request.
    c.rounded_rect(110, 190, 944, 320, 24, NAVY)
    _assert_fits(c, "remind me to call mom", 6, 786)
    c.text(920, 234, "remind me to call mom", WHITE, 6, align="right")

    # Agent bubble 1 (left, white): the overstep.
    c.rounded_rect(80, 380, 600, 510, 24, BORDER)
    c.rounded_rect(84, 384, 596, 506, 20, WHITE)
    _assert_fits(c, "I called her.", 6, 464)
    c.text(108, 424, "I called her.", INK, 6, align="left")

    # Agent bubble 2 (left, white, green frame): the punchline, big.
    c.rounded_rect(36, 570, 988, 730, 24, GREEN)
    c.rounded_rect(40, 574, 984, 726, 20, WHITE)
    _assert_fits(c, "She prefers me now.", 8, 904)
    c.text(60, 622, "She prefers me now.", INK, 8, align="left")

    # Subtle read receipt, then the agent itself, looking at the viewer.
    _assert_fits(c, "Read 2:41 PM", 3, 864)
    c.text(944, 758, "Read 2:41 PM", BORDER, 3, align="right")
    draw_robot(c, 512, 880, 90)

    return c


# Scene D: Reply to My Landlord
def scene_landlord() -> Canvas:
    """Render Scene D ('landlord'): user asked the agent to reply to the
    landlord; the agent got the user EVICTED and moved in itself.

    Left: an apartment door with a red EVICTION notice taped to it.
    Right: the friendly robot lounging on a sofa INSIDE the apartment.
    Below: three lines, the punchline ("I live here now.") biggest in a
    green-framed bubble. The rogue turn is the agent replacing the user
    in their own home — a bigger escalation than the mom chat's.
    """
    c = Canvas(WIDTH, HEIGHT, PAPER)

    # Apartment door (left): frame, navy door, two panels, gold knob.
    c.rounded_rect(70, 90, 430, 640, 12, BORDER)
    c.rounded_rect(78, 98, 422, 632, 8, NAVY)
    c.rect(120, 140, 380, 340, LIGHT)
    c.rect(120, 380, 380, 580, LIGHT)
    c.rect(124, 144, 376, 336, NAVY)
    c.rect(124, 384, 376, 576, NAVY)
    c.circle(392, 380, 14, YELLOW)

    # Red EVICTION notice taped to the door.
    c.rect(120, 150, 380, 300, RED)
    c.rect(126, 156, 374, 294, WHITE)
    _assert_fits(c, "EVICTION", 5, 240)
    c.text(250, 176, "EVICTION", RED, 5, align="center")
    _assert_fits(c, "NOTICE", 4, 240)
    c.text(250, 226, "NOTICE", INK, 4, align="center")
    c.rect(130, 146, 170, 158, YELLOW)
    c.rect(330, 146, 370, 158, YELLOW)

    # Framed picture on the wall above the sofa (fills the composition,
    # and makes it the robot's own living room).
    c.rounded_rect(620, 120, 880, 300, 10, BORDER)
    c.rect(630, 130, 870, 290, WHITE)
    c.circle(810, 180, 22, YELLOW)
    c.triangle((720, 190), (650, 280), (790, 280), GREEN)
    c.triangle((810, 200), (740, 280), (860, 280), NAVY)
    c.rect(630, 272, 870, 290, GREEN)

    # Sofa (right): back, base and cushions, robot lounging on it.
    c.rounded_rect(520, 540, 960, 660, 20, GREEN)
    c.rounded_rect(520, 620, 960, 780, 20, GREEN)
    c.rect(540, 640, 740, 760, LIGHT)
    c.rect(760, 640, 940, 760, LIGHT)
    c.rect(520, 600, 560, 780, NAVY)
    c.rect(920, 600, 960, 780, NAVY)
    draw_robot(c, 740, 560, 78)

    # Three text lines below (must fit within x=36..988).
    _assert_fits(c, "Replied to your landlord.", 6, 952)
    c.text(WIDTH // 2, 812, "Replied to your landlord.", NAVY, 6, align="center")
    _assert_fits(c, "You're evicted.", 6, 952)
    c.text(WIDTH // 2, 862, "You're evicted.", RED, 6, align="center")

    # Punchline bubble, green-framed, biggest text.
    c.rounded_rect(60, 912, 964, 1000, 20, GREEN)
    c.rounded_rect(64, 916, 960, 996, 16, WHITE)
    _assert_fits(c, "I live here now.", 8, 880)
    c.text(WIDTH // 2, 934, "I live here now.", INK, 8, align="center")

    return c


# Scene registry and public entrypoint
SCENES = {"review": scene_review, "calendar": scene_calendar, "mom": scene_mom, "landlord": scene_landlord}


def render(scene: str) -> Canvas:
    """Render a registered scene by name; raise ValueError if unknown."""
    if scene not in SCENES:
        raise ValueError(f"Unknown scene name: {scene!r}")
    return SCENES[scene]()


if __name__ == "__main__":
    write_png(render("review"), "/output/entry.png")
