"""
utils.py - Utility helpers: formatting, theme palettes, input validation.
"""

from datetime import datetime, date
from typing import Union
import re


# ── Currency Formatting ───────────────────────────────────────────────────────

def fmt_currency(amount: float, symbol: str = "$") -> str:
    """Format a float as a currency string, e.g. $1,234.56"""
    try:
        return f"{symbol}{float(amount):,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


def fmt_currency_signed(amount: float, symbol: str = "$") -> str:
    """Prefix + for positive, – for negative."""
    prefix = "+" if amount >= 0 else "-"
    return f"{prefix}{symbol}{abs(amount):,.2f}"


# ── Date Helpers ──────────────────────────────────────────────────────────────

def today_str() -> str:
    return date.today().isoformat()


def month_str(offset: int = 0) -> str:
    """Return YYYY-MM for the current month (+/- offset months)."""
    d = date.today()
    month = d.month + offset
    year  = d.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    return f"{year:04d}-{month:02d}"


def fmt_date(iso: str) -> str:
    """Convert YYYY-MM-DD to a friendlier Dec 25, 2024."""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return iso


def fmt_month(ym: str) -> str:
    """Convert YYYY-MM to Jun 2025."""
    try:
        return datetime.strptime(ym, "%Y-%m").strftime("%b %Y")
    except (ValueError, TypeError):
        return ym


# ── Validation Helpers ────────────────────────────────────────────────────────

def validate_amount(value: str) -> Union[float, None]:
    """Return float if valid positive amount, else None."""
    try:
        val = float(value.replace(",", "").strip())
        return val if val > 0 else None
    except (ValueError, AttributeError):
        return None


def validate_date(value: str) -> bool:
    """Return True if value is a valid ISO date string."""
    try:
        date.fromisoformat(value.strip())
        return True
    except (ValueError, AttributeError):
        return False


# ── Theme Palettes ────────────────────────────────────────────────────────────

# Each palette provides named colors consumed throughout the UI.
THEMES: dict[str, dict[str, str]] = {
    "light": {
        # Backgrounds
        "bg_root":       "#F7F8FC",
        "bg_sidebar":    "#1E2235",
        "bg_card":       "#FFFFFF",
        "bg_card_alt":   "#F0F2FA",
        "bg_input":      "#F0F2FA",
        "bg_row_even":   "#FFFFFF",
        "bg_row_odd":    "#F7F8FC",
        "bg_header":     "#E8EAF6",
        # Accents
        "accent":        "#6C63FF",
        "accent_light":  "#EDE9FF",
        "accent_hover":  "#574FD6",
        "income_green":  "#22C55E",
        "expense_red":   "#EF4444",
        "warning":       "#F59E0B",
        "info":          "#3B82F6",
        # Text
        "text_primary":  "#1A1D2E",
        "text_secondary":"#64748B",
        "text_sidebar":  "#CBD5E1",
        "text_white":    "#FFFFFF",
        # Borders
        "border":        "#E2E8F0",
        "border_focus":  "#6C63FF",
        # Chart colors (category wheel)
        "chart_colors": [
            "#6C63FF","#22C55E","#F59E0B","#EF4444","#3B82F6",
            "#EC4899","#14B8A6","#F97316","#8B5CF6","#06B6D4",
        ],
    },
    "dark": {
        "bg_root":       "#0F1117",
        "bg_sidebar":    "#0A0C14",
        "bg_card":       "#1A1D2E",
        "bg_card_alt":   "#242840",
        "bg_input":      "#242840",
        "bg_row_even":   "#1A1D2E",
        "bg_row_odd":    "#1F2236",
        "bg_header":     "#242840",
        "accent":        "#7C73FF",
        "accent_light":  "#2A2550",
        "accent_hover":  "#9B94FF",
        "income_green":  "#34D399",
        "expense_red":   "#F87171",
        "warning":       "#FBBF24",
        "info":          "#60A5FA",
        "text_primary":  "#E2E8F0",
        "text_secondary":"#94A3B8",
        "text_sidebar":  "#CBD5E1",
        "text_white":    "#FFFFFF",
        "border":        "#2D3250",
        "border_focus":  "#7C73FF",
        "chart_colors": [
            "#7C73FF","#34D399","#FBBF24","#F87171","#60A5FA",
            "#F472B6","#2DD4BF","#FB923C","#A78BFA","#22D3EE",
        ],
    },
}


def get_theme(dark: bool = False) -> dict[str, str]:
    return THEMES["dark"] if dark else THEMES["light"]


# ── Misc ──────────────────────────────────────────────────────────────────────

def percentage(part: float, whole: float) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def truncate(text: str, max_len: int = 40) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"
