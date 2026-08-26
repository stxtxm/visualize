"""
Generate high-quality, readable social-media footer icons for the Visualize GUI.

Design goals:
- Larger, crisp icons (supersampled then downscaled for smooth edges).
- Each icon is a rounded "chip" with a brand-tinted background and a high-contrast
  glyph, so it is always legible against the dark footer (#0a0a12).
- LinkedIn: brand-blue chip with a white "in" monogram + logo square.
- Website: neon-cyan chip with a white globe glyph.
- Hover variants add a brighter fill + outer glow ring.

Output: assets/linkedin.png, linkedin_hover.png, website.png, website_hover.png
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SIZE = 64  # output size in px (displayed smaller, supersampled for quality)

FONT_PATHS = [
    "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Bold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/var/lib/flatpak/runtime/org.fedoraproject.Platform/x86_64/f44/92e592c9e361816e0737b10ed4a2a844d10692952ded73bee921ea64be06a0dc/files/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
]


def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def vertical_gradient(size, top, bottom):
    """Return an RGBA image with a vertical linear gradient."""
    w, h = size, size
    img = Image.new("RGBA", (w, h))
    top_r, top_g, top_b = top
    bot_r, bot_g, bot_b = bottom
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        for x in range(w):
            img.putpixel((x, y), (r, g, b, 255))
    return img


def rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def make_chip(size, color_top, color_bottom, glyph_draw, hover=False):
    """Compose a chip icon: rounded gradient background + glyph + optional glow."""
    # Supersample for crisp edges
    S = size * 4
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    radius = int(S * 0.24)
    bg = vertical_gradient(S, color_top, color_bottom)
    mask = rounded_mask(S, radius)
    base.paste(bg, (0, 0), mask)

    # Subtle inner highlight (top sheen)
    sheen = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rounded_rectangle([0, 0, S - 1, int(S * 0.5)], radius=radius, fill=(255, 255, 255, 28))
    sheen = sheen.filter(ImageFilter.GaussianBlur(S * 0.02))
    base = Image.alpha_composite(base, sheen)

    # Glyph drawn centered
    glyph = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glyph_draw(ImageDraw.Draw(glyph), S, hover)

    if hover:
        # Outer glow ring
        glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        glow_color = glyph_draw.glow_color if hasattr(glyph_draw, "glow_color") else color_top
        gd.rounded_rectangle(
            [int(S * 0.03), int(S * 0.03), int(S * 0.97) - 1, int(S * 0.97) - 1],
            radius=radius, outline=glow_color + (255,), width=int(S * 0.025),
        )
        glow = glow.filter(ImageFilter.GaussianBlur(S * 0.03))
        base = Image.alpha_composite(glow, base)

    base = Image.alpha_composite(base, glyph)

    # Downscale to final size
    final = base.resize((size, size), Image.LANCZOS)
    return final


# ── LinkedIn glyph ──────────────────────────────────────────────────────────
def draw_linkedin(draw, S, hover):
    white = (255, 255, 255, 255)
    # "in" monogram, bold, centered
    font = load_font(int(S * 0.52))
    text = "in"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (S - tw) / 2 - bbox[0]
    y = (S - th) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=white)

    # Small logo square above the "i" to evoke the LinkedIn mark
    sq = int(S * 0.085)
    draw.rectangle([int(S * 0.3), int(S * 0.18), int(S * 0.3) + sq, int(S * 0.18) + sq],
                   fill=white)


# ── Website / globe glyph ──────────────────────────────────────────────────
def draw_website(draw, S, hover):
    light = (235, 250, 255, 255)
    cx, cy = S / 2, S / 2
    r = S * 0.30
    lw = max(1, int(S * 0.028))

    # Outer globe circle (arcs)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=light, width=lw)

    # Meridians (vertical ellipses)
    for factor in (0.45, 0.8):
        rr = r * factor
        draw.ellipse([cx - rr, cy - r, cx + rr, cy + r], outline=light, width=lw)

    # Latitudes (horizontal lines)
    for fy in (0.42, 0.62):
        yy = cy - r + 2 * r * fy
        half = math.sqrt(max(0.0, r * r - (yy - cy) ** 2))
        draw.line([cx - half, yy, cx + half, yy], fill=light, width=lw)


draw_linkedin.glow_color = (0, 200, 255)
draw_website.glow_color = (0, 229, 255)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # LinkedIn — brand blue gradient
    linkedin_normal = make_chip(
        SIZE,
        color_top=(10, 130, 220),
        color_bottom=(8, 80, 165),
        glyph_draw=draw_linkedin,
        hover=False,
    )
    linkedin_hover = make_chip(
        SIZE,
        color_top=(20, 160, 255),
        color_bottom=(10, 110, 200),
        glyph_draw=draw_linkedin,
        hover=True,
    )

    # Website — neon cyan gradient
    website_normal = make_chip(
        SIZE,
        color_top=(0, 200, 220),
        color_bottom=(0, 140, 180),
        glyph_draw=draw_website,
        hover=False,
    )
    website_hover = make_chip(
        SIZE,
        color_top=(60, 240, 255),
        color_bottom=(0, 190, 220),
        glyph_draw=draw_website,
        hover=True,
    )

    linkedin_normal.save(os.path.join(ASSETS_DIR, "linkedin.png"))
    linkedin_hover.save(os.path.join(ASSETS_DIR, "linkedin_hover.png"))
    website_normal.save(os.path.join(ASSETS_DIR, "website.png"))
    website_hover.save(os.path.join(ASSETS_DIR, "website_hover.png"))
    print("Icons generated successfully.")


if __name__ == "__main__":
    main()
