from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap
import requests
from io import BytesIO

FONT_DIR = Path(__file__).parent

FONT_QUOTE = FONT_DIR / "mplus-1c-regular.ttf"
FONT_NAME = FONT_DIR / "Inter-Italic.ttf"
FONT_HANDLE = FONT_DIR / "Inter-Light.ttf"

CANVAS_W = 1200
CANVAS_H = 630

AVATAR_W = CANVAS_H

PADDING_X = 48
TEXT_AREA_X = AVATAR_W + PADDING_X
TEXT_AREA_W = CANVAS_W - TEXT_AREA_X - PADDING_X


def fetch_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGBA")


def make_fade_mask(width: int, height: int, fade_px: int = 260) -> Image.Image:
    mask = Image.new("L", (width, height), 255)
    for x in range(width - fade_px, width):
        t = (width - x) / fade_px
        alpha = int(255 * (t ** 2))
        for y in range(height):
            mask.putpixel((x, y), alpha)
    return mask


def draw_centered_multiline(draw, text, font, box, fill):
    x, y, w, h = box
    lines = textwrap.wrap(text, width=28)
    line_h = font.getbbox("Ag")[3] + 10
    total_h = len(lines) * line_h
    start_y = y + (h - total_h) // 2

    for line in lines:
        tw = draw.textlength(line, font=font)
        draw.text(
            (x + (w - tw) // 2, start_y),
            line,
            font=font,
            fill=fill
        )
        start_y += line_h

    return start_y


def render_quote(
    *,
    quote: str,
    display_name: str,
    username: str,
    avatar_url: str,
    colorful: bool = False
) -> Image.Image:
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))

    avatar = fetch_image(avatar_url)
    avatar = avatar.resize((AVATAR_W, AVATAR_W))

    if not colorful:
        avatar = avatar.convert("L").convert("RGBA")

    mask = make_fade_mask(AVATAR_W, AVATAR_W)
    img.paste(avatar, (0, 0), mask)

    draw = ImageDraw.Draw(img)

    quote_font = ImageFont.truetype(str(FONT_QUOTE), 44)
    name_font = ImageFont.truetype(str(FONT_NAME), 26)
    handle_font = ImageFont.truetype(str(FONT_HANDLE), 20)

    quote_bottom_y = draw_centered_multiline(
        draw,
        quote,
        quote_font,
        (
            TEXT_AREA_X,
            0,
            TEXT_AREA_W,
            CANVAS_H - 80
        ),
        (255, 255, 255)
    )

    name_y = quote_bottom_y + 14
    NAME_TO_HANDLE_GAP = 34

    draw.text(
        (TEXT_AREA_X + TEXT_AREA_W // 2, name_y),
        f"- {display_name}",
        font=name_font,
        fill=(200, 200, 200),
        anchor="ma"
    )

    draw.text(
        (TEXT_AREA_X + TEXT_AREA_W // 2, name_y + NAME_TO_HANDLE_GAP),
        f"@{username}",
        font=handle_font,
        fill=(150, 150, 150),
        anchor="ma"
    )

    return img
