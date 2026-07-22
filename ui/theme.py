"""
Theme system for the psychedelic visualizer.
Provides multiple colour schemes that can be switched at runtime.
"""


class Theme:
    """A colour theme containing all UI colours."""

    __slots__ = (
        'name', 'bg_dark', 'bg_panel', 'bg_card', 'fg_light', 'fg_muted',
        'neon_primary', 'neon_secondary', 'neon_accent', 'neon_warn',
        'status_bg', 'border', 'footer_bg', 'footer_fg', 'progress_track',
        'input_bg', 'button_bg', 'button_hover', 'preview_bg',
        'danger_bg', 'danger_fg',
    )

    def __init__(self, name, bg_dark, bg_panel, bg_card, fg_light, fg_muted,
                 neon_primary, neon_secondary, neon_accent, neon_warn,
                 status_bg, border, footer_bg, footer_fg, progress_track,
                 input_bg=None, button_bg=None, button_hover=None,
                 preview_bg=None, danger_bg=None, danger_fg=None):
        self.name = name
        self.bg_dark = bg_dark
        self.bg_panel = bg_panel
        self.bg_card = bg_card
        self.fg_light = fg_light
        self.fg_muted = fg_muted
        self.neon_primary = neon_primary
        self.neon_secondary = neon_secondary
        self.neon_accent = neon_accent
        self.neon_warn = neon_warn
        self.status_bg = status_bg
        self.border = border
        self.footer_bg = footer_bg
        self.footer_fg = footer_fg
        self.progress_track = progress_track
        self.input_bg = input_bg or bg_card
        self.button_bg = button_bg or bg_card
        self.button_hover = button_hover or border
        self.preview_bg = preview_bg or bg_dark
        self.danger_bg = danger_bg or bg_panel
        self.danger_fg = danger_fg or "#ff5b6e"

    def as_dict(self):
        return {s: getattr(self, s) for s in self.__slots__}


# ── Built-in themes ──────────────────────────────────────────────────

CYBERPUNK = Theme(
    name="Cyberpunk",
    bg_dark="#09090d", bg_panel="#12121d", bg_card="#1b1b2a",
    fg_light="#e2e2ee", fg_muted="#85859e",
    neon_primary="#00e5ff", neon_secondary="#ff007f", neon_accent="#39ff14",
    neon_warn="#ffaa00",
    status_bg="#0d0d18", border="#1c1c30",
    footer_bg="#0a0a12", footer_fg="#6a6a8a",
    progress_track="#14233b",
    input_bg="#0f1624", button_bg="#1b263b", button_hover="#263853",
    preview_bg="#05070d", danger_bg="#29151f", danger_fg="#ff5b6e",
)

SYNTHWAVE = Theme(
    name="Synthwave",
    bg_dark="#0d041a", bg_panel="#1a0a2e", bg_card="#2a1050",
    fg_light="#f0e6ff", fg_muted="#a080c0",
    neon_primary="#ff00cc", neon_secondary="#00ffff", neon_accent="#ffcc00",
    neon_warn="#ff6600",
    status_bg="#0f0520", border="#3a1a6a",
    footer_bg="#0d041a", footer_fg="#8050a0",
    progress_track="#2a1050",
    input_bg="#200d3a", button_bg="#32165b", button_hover="#48217d",
    preview_bg="#080311", danger_bg="#3a122d", danger_fg="#ff74bd",
)

MATRIX = Theme(
    name="Matrix",
    bg_dark="#000a00", bg_panel="#001a00", bg_card="#002a00",
    fg_light="#ccffcc", fg_muted="#408040",
    neon_primary="#00ff41", neon_secondary="#00cc33", neon_accent="#80ff80",
    neon_warn="#ffaa00",
    status_bg="#000d00", border="#004400",
    footer_bg="#000a00", footer_fg="#306030",
    progress_track="#002a00",
    input_bg="#001500", button_bg="#003000", button_hover="#004d00",
    preview_bg="#000500", danger_bg="#1d1200", danger_fg="#ffaa00",
)

TOKYO_NIGHT = Theme(
    name="Tokyo Night",
    bg_dark="#0f111a", bg_panel="#1a1b2e", bg_card="#24283b",
    fg_light="#c0caf5", fg_muted="#565f89",
    neon_primary="#7aa2f7", neon_secondary="#bb9af7", neon_accent="#9ece6a",
    neon_warn="#e0af68",
    status_bg="#131520", border="#2f354a",
    footer_bg="#0f111a", footer_fg="#464b66",
    progress_track="#24283b",
    input_bg="#161a29", button_bg="#202640", button_hover="#303958",
    preview_bg="#0b0d14", danger_bg="#2b1d2f", danger_fg="#f7768e",
)

THEMES = {
    "cyberpunk": CYBERPUNK,
    "synthwave": SYNTHWAVE,
    "matrix": MATRIX,
    "tokyo_night": TOKYO_NIGHT,
}

THEME_NAMES = list(THEMES.keys())


def get_theme(name="cyberpunk"):
    """Get a theme by name. Falls back to cyberpunk."""
    return THEMES.get(name, CYBERPUNK)
