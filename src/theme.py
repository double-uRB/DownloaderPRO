"""
Design token system and QSS stylesheet generator for Downloader PRO.
Matches the Stitch design: dark-first with glassmorphism, gradient CTAs, and glow effects.
"""

# ─── Color Palettes ───────────────────────────────────────────────────────────

DARK_COLORS = {
    "background":               "#0b1326",
    "sidebar_bg":               "#131b2e",
    "surface_container":        "#171f33",
    "surface_container_low":    "#131b2e",
    "surface_container_high":   "#222a3d",
    "surface_container_highest":"#2d3449",
    "surface_container_lowest": "#060e20",
    "primary":                  "#4cd7f6",
    "primary_container":        "#06b6d4",
    "secondary":                "#d0bcff",
    "secondary_container":      "#571bc1",
    "on_surface":               "#dae2fd",
    "on_surface_variant":       "#bcc9cd",
    "on_primary":               "#003640",
    "on_secondary":             "#3c0091",
    "outline":                  "#869397",
    "outline_variant":          "#3d494c",
    "error":                    "#ffb4ab",
    "error_container":          "#93000a",
    "glass_bg":                 "rgba(45, 52, 73, 102)",   # ~40% opacity
    "glass_border":             "rgba(76, 215, 246, 26)",  # primary 10%
    "glow_shadow":              "rgba(76, 215, 246, 0.15)",
    "hover_overlay":            "rgba(255, 255, 255, 13)",  # white 5%
    "separator":                "rgba(61, 73, 76, 25)",
}

LIGHT_COLORS = {
    "background":               "#f0f4ff",
    "sidebar_bg":               "#e8ecf4",
    "surface_container":        "#ffffff",
    "surface_container_low":    "#f5f7fc",
    "surface_container_high":   "#e8ecf4",
    "surface_container_highest":"#dde2ee",
    "surface_container_lowest": "#ffffff",
    "primary":                  "#06b6d4",
    "primary_container":        "#06b6d4",
    "secondary":                "#7c3aed",
    "secondary_container":      "#571bc1",
    "on_surface":               "#1a1a2e",
    "on_surface_variant":       "#6b7280",
    "on_primary":               "#ffffff",
    "on_secondary":             "#ffffff",
    "outline":                  "#9ca3af",
    "outline_variant":          "#d1d5db",
    "error":                    "#dc2626",
    "error_container":          "#fee2e2",
    "glass_bg":                 "rgba(255, 255, 255, 178)",
    "glass_border":             "rgba(6, 182, 212, 40)",
    "glow_shadow":              "rgba(6, 182, 212, 0.12)",
    "hover_overlay":            "rgba(0, 0, 0, 13)",
    "separator":                "rgba(209, 213, 219, 80)",
}

# ─── Gradient Strings ─────────────────────────────────────────────────────────

def _gradient_cta(c):
    """CSS-style gradient – PySide6 QSS uses qlineargradient syntax."""
    return (
        f"qlineargradient(x1:0, y1:0, x2:1, y2:1, "
        f"stop:0 {c['primary_container']}, stop:1 {c['secondary_container']})"
    )

def _gradient_primary_secondary(c):
    return (
        f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 {c['primary']}, stop:1 {c['secondary']})"
    )

# ─── Stylesheet Generator ────────────────────────────────────────────────────

def generate_stylesheet(theme: str = "dark") -> str:
    """Return the full QSS stylesheet for the given theme."""
    c = DARK_COLORS if theme == "dark" else LIGHT_COLORS
    cta = _gradient_cta(c)
    grad = _gradient_primary_secondary(c)

    return f"""
    /* ── Global ───────────────────────────────────── */
    * {{
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    }}
    QMainWindow {{
        background-color: {c['background']};
        color: {c['on_surface']};
    }}

    /* ── Sidebar ──────────────────────────────────── */
    #sidebar {{
        background-color: {c['sidebar_bg']};
        border-right: 1px solid {c['separator']};
    }}
    #sidebar QLabel#app_title {{
        color: {c['primary']};
        font-size: 18px;
        font-weight: 900;
    }}
    #sidebar QLabel#app_subtitle {{
        color: {c['on_surface_variant']};
        font-size: 9px;
    }}

    /* Nav items */
    #nav_item {{
        color: {c['on_surface_variant']};
        background: transparent;
        border: none;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: left;
        font-size: 12px;
        font-weight: 600;
    }}
    #nav_item:hover {{
        background-color: {c['surface_container']};
        color: {c['on_surface']};
    }}
    #nav_item[active="true"] {{
        background-color: {c['surface_container']};
        color: {c['primary']};
        border-left: 3px solid {c['primary']};
        font-weight: 700;
    }}

    /* New Task / New Download CTA button */
    #cta_button {{
        background: {cta};
        color: {c['on_primary']};
        border: none;
        border-radius: 12px;
        padding: 14px;
        font-size: 13px;
        font-weight: 800;
    }}
    #cta_button:hover {{
        background: {cta};
        opacity: 0.9;
    }}
    #cta_button:pressed {{
        padding-top: 15px;
        padding-bottom: 13px;
    }}

    /* ── Top Header Bar ───────────────────────────── */
    #top_header {{
        background-color: {c['sidebar_bg']};
        border-bottom: 1px solid {c['separator']};
    }}
    #page_title {{
        color: {c['on_surface']};
        font-size: 17px;
        font-weight: 700;
    }}
    #page_subtitle {{
        color: {c['on_surface_variant']};
        font-size: 9px;
        font-weight: 500;
    }}

    /* ── Glass Panel (card container) ─────────────── */
    #glass_panel {{
        background-color: {c['surface_container_high']};
        border: 1px solid {c['glass_border']};
        border-radius: 14px;
        padding: 20px;
    }}

    /* ── Surface Cards ────────────────────────────── */
    #surface_card {{
        background-color: {c['surface_container']};
        border: 1px solid {c['separator']};
        border-radius: 12px;
        padding: 16px;
    }}
    #surface_card_low {{
        background-color: {c['surface_container_low']};
        border: 1px solid {c['separator']};
        border-radius: 14px;
        padding: 20px;
    }}

    /* ── Inputs ────────────────────────────────────── */
    QLineEdit {{
        background-color: {c['surface_container_lowest']};
        border: 1px solid {c['outline_variant']};
        border-radius: 10px;
        color: {c['on_surface']};
        padding: 10px 16px;
        font-size: 13px;
        selection-background-color: {c['primary_container']};
    }}
    QLineEdit:focus {{
        border: 2px solid {c['primary']};
    }}
    QLineEdit::placeholder {{
        color: {c['outline']};
    }}

    /* ── Buttons ───────────────────────────────────── */
    QPushButton {{
        background-color: {c['surface_container_high']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {c['surface_container_highest']};
    }}
    QPushButton:pressed {{
        background-color: {c['surface_container']};
    }}

    /* Primary action button (gradient) */
    #primary_button {{
        background: {cta};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 28px;
        font-size: 14px;
        font-weight: 700;
    }}
    #primary_button:hover {{
        background: {cta};
    }}
    #primary_button:pressed {{
        padding-top: 13px;
        padding-bottom: 11px;
    }}

    /* Download mega-button */
    #download_button {{
        background: {grad};
        color: {c['on_primary']};
        border: none;
        border-radius: 14px;
        padding: 16px;
        font-size: 16px;
        font-weight: 800;
    }}
    #download_button:hover {{
        background: {grad};
    }}
    #download_button:pressed {{
        padding-top: 17px;
        padding-bottom: 15px;
    }}

    /* Inline paste button */
    #paste_button {{
        background-color: transparent;
        color: {c['primary']};
        border: 1px solid {c['primary']};
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 11px;
        font-weight: 700;
    }}
    #paste_button:hover {{
        background-color: {c['glass_border']};
    }}

    /* ── Quality Cards ─────────────────────────────── */
    #quality_card {{
        background-color: {c['surface_container']};
        border: 1px solid {c['outline_variant']};
        border-radius: 10px;
        padding: 12px;
    }}
    #quality_card:hover {{
        border-color: {c['primary']};
    }}
    #quality_card[selected="true"] {{
        background-color: {c['surface_container_high']};
        border: 2px solid {c['primary']};
    }}

    /* ── Progress Bar ──────────────────────────────── */
    QProgressBar {{
        background-color: {c['surface_container_lowest']};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
        font-size: 0px;
    }}
    QProgressBar::chunk {{
        background: {grad};
        border-radius: 4px;
    }}

    /* ── Labels ────────────────────────────────────── */
    QLabel {{
        color: {c['on_surface']};
        background: transparent;
        border: none;
    }}
    QLabel#section_title {{
        font-size: 15px;
        font-weight: 700;
        color: {c['on_surface']};
    }}
    QLabel#section_subtitle {{
        font-size: 11px;
        color: {c['on_surface_variant']};
    }}
    QLabel#stat_value {{
        font-size: 20px;
        font-weight: 800;
        color: {c['on_surface']};
    }}
    QLabel#stat_label {{
        font-size: 9px;
        font-weight: 600;
        color: {c['on_surface_variant']};
        text-transform: uppercase;
    }}
    QLabel#badge_primary {{
        background-color: {c['primary']};
        color: {c['on_primary']};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: 700;
    }}
    QLabel#badge_hdr {{
        background-color: {c['error_container']};
        color: {c['error']};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: 700;
    }}
    QLabel#speed_label {{
        color: {c['primary']};
        font-size: 13px;
        font-weight: 700;
    }}

    /* ── Checkbox / Toggle ─────────────────────────── */
    QCheckBox {{
        color: {c['on_surface']};
        spacing: 8px;
        font-size: 13px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {c['outline']};
        background-color: {c['surface_container_lowest']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['primary']};
        border-color: {c['primary']};
    }}

    /* ── ComboBox ──────────────────────────────────── */
    QComboBox {{
        background-color: {c['surface_container_lowest']};
        border: 1px solid {c['outline_variant']};
        border-radius: 10px;
        color: {c['on_surface']};
        padding: 8px 14px;
        font-size: 13px;
    }}
    QComboBox:focus {{
        border-color: {c['primary']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['surface_container_high']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        selection-background-color: {c['primary_container']};
    }}

    /* ── Slider ────────────────────────────────────── */
    QSlider::groove:horizontal {{
        border: none;
        height: 6px;
        background: {c['surface_container_lowest']};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {c['primary']};
        border: none;
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c['primary']};
        border-radius: 3px;
    }}

    /* ── Scroll Area ───────────────────────────────── */
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['surface_container_highest']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    /* ── Tab-like filter buttons ───────────────────── */
    #filter_button {{
        background: transparent;
        color: {c['on_surface_variant']};
        border: none;
        border-bottom: 2px solid transparent;
        padding: 8px 4px;
        font-size: 13px;
        font-weight: 500;
    }}
    #filter_button:hover {{
        color: {c['on_surface']};
    }}
    #filter_button[active="true"] {{
        color: {c['primary']};
        border-bottom: 2px solid {c['primary']};
        font-weight: 700;
    }}

    /* ── Status Bar ────────────────────────────────── */
    QStatusBar {{
        background-color: {c['sidebar_bg']};
        color: {c['on_surface_variant']};
        border-top: 1px solid {c['separator']};
        font-size: 11px;
        padding: 4px 16px;
    }}

    /* ── Frame separator ──────────────────────────── */
    #separator_line {{
        background-color: {c['outline_variant']};
        max-height: 1px;
        min-height: 1px;
    }}

    /* ── Theme toggle ─────────────────────────────── */
    #theme_toggle_bg {{
        background-color: {c['surface_container_highest']};
        border: 1px solid {c['outline_variant']};
        border-radius: 14px;
    }}
    #theme_toggle_knob {{
        background-color: {c['primary']};
        border-radius: 12px;
    }}
    """
