"""
reports.py - Reports & Analytics frame.
Renders:
  - Pie chart: category-wise expense distribution
  - Bar chart: monthly income vs expenses
  - Line chart: monthly spending trend
  - Category breakdown table
  - Budget status bars
All charts use Matplotlib embedded in Tkinter via FigureCanvasTkAgg.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import database as db
from utils import fmt_currency, fmt_month, get_theme, month_str


# Shared style helper applied to every Figure
def _apply_fig_style(fig: Figure, ax, t: dict):
    fig.patch.set_facecolor(t["bg_card"])
    ax.set_facecolor(t["bg_card"])
    ax.tick_params(colors=t["text_secondary"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(t["border"])


class ReportsFrame(tk.Frame):
    """
    Full reports page with tab navigation for different chart types.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._canvases: list[FigureCanvasTkAgg] = []
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        t = self.app.theme
        self.configure(bg=t["bg_root"])

        # Header
        hdr = tk.Frame(self, bg=t["bg_root"])
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(hdr, text="Reports & Analytics", font=("Segoe UI", 20, "bold"),
                 bg=t["bg_root"], fg=t["text_primary"]).pack(side="left")

        # Month selector
        tk.Label(hdr, text="Month:", font=("Segoe UI", 9),
                 bg=t["bg_root"], fg=t["text_secondary"]).pack(side="right", padx=(0, 4))
        self._month_var = tk.StringVar(value=month_str())
        months = [month_str(i) for i in range(-11, 1)]
        month_cb = ttk.Combobox(hdr, textvariable=self._month_var,
                                 values=months, state="readonly", width=10)
        month_cb.pack(side="right")
        month_cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        # Tab notebook
        style = ttk.Style()
        style.configure("Reports.TNotebook", background=t["bg_root"],
                         borderwidth=0)
        style.configure("Reports.TNotebook.Tab", background=t["bg_card_alt"],
                         foreground=t["text_secondary"], padding=[12, 6])
        style.map("Reports.TNotebook.Tab",
                  background=[("selected", t["accent"])],
                  foreground=[("selected", t["text_white"])])

        self._nb = ttk.Notebook(self, style="Reports.TNotebook")
        self._nb.pack(fill="both", expand=True, padx=24, pady=12)

        # Tab frames
        self._tab_overview  = tk.Frame(self._nb, bg=t["bg_root"])
        self._tab_monthly   = tk.Frame(self._nb, bg=t["bg_root"])
        self._tab_budget    = tk.Frame(self._nb, bg=t["bg_root"])
        self._nb.add(self._tab_overview, text="  Overview  ")
        self._nb.add(self._tab_monthly,  text="  Monthly Trend  ")
        self._nb.add(self._tab_budget,   text="  Budget Status  ")

        self.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        t = self.app.theme
        self.configure(bg=t["bg_root"])
        # Destroy old canvases to prevent memory leaks
        for c in self._canvases:
            try:
                c.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvases.clear()
        plt.close("all")

        self._build_overview(t)
        self._build_monthly(t)
        self._build_budget(t)

    # ── Overview Tab ──────────────────────────────────────────────────────────

    def _build_overview(self, t: dict):
        for w in self._tab_overview.winfo_children():
            w.destroy()

        cat_totals = db.get_category_totals("Expense")
        row_frame = tk.Frame(self._tab_overview, bg=t["bg_root"])
        row_frame.pack(fill="both", expand=True)
        row_frame.columnconfigure(0, weight=1)
        row_frame.columnconfigure(1, weight=1)
        row_frame.rowconfigure(0, weight=1)

        # Pie chart
        pie_card = self._card(row_frame, "Expense Distribution")
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)
        self._draw_pie(pie_card, cat_totals, t)

        # Category table
        tbl_card = self._card(row_frame, "Category Breakdown")
        tbl_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)
        self._draw_category_table(tbl_card, cat_totals, t)

    def _draw_pie(self, parent, cat_totals: list, t: dict):
        if not cat_totals:
            tk.Label(parent, text="No expense data.", bg=t["bg_card"],
                     fg=t["text_secondary"], font=("Segoe UI", 10)).pack(pady=40)
            return

        labels = [c["category"] for c in cat_totals]
        sizes  = [c["total"]    for c in cat_totals]
        colors = (t["chart_colors"] * ((len(labels) // len(t["chart_colors"])) + 1))[:len(labels)]

        fig = Figure(figsize=(5, 3.8), dpi=96, tight_layout=True)
        ax  = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct="%1.0f%%",
            colors=colors, startangle=140,
            wedgeprops={"linewidth": 1.5, "edgecolor": t["bg_card"]},
        )
        for a in autotexts:
            a.set_fontsize(7)
            a.set_color(t["text_white"])
        fig.patch.set_facecolor(t["bg_card"])

        # Legend
        legend = ax.legend(
            wedges, [f"{l} ({fmt_currency(s)})" for l, s in zip(labels, sizes)],
            loc="lower center", bbox_to_anchor=(0.5, -0.22),
            ncol=2, fontsize=7, frameon=False,
            labelcolor=t["text_secondary"],
        )
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        self._canvases.append(canvas)

    def _draw_category_table(self, parent, cat_totals: list, t: dict):
        f = tk.Frame(parent, bg=t["bg_card"])
        f.pack(fill="both", expand=True, padx=8, pady=8)

        headers = ("Category", "Total Spent", "% of Expenses")
        widths   = (130, 110, 110)
        for col, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(f, text=h, font=("Segoe UI", 8, "bold"), width=w//8,
                     bg=t["bg_header"], fg=t["text_primary"],
                     anchor="w", pady=5).grid(row=0, column=col, sticky="nsew",
                                               padx=(0, 1))

        grand = sum(c["total"] for c in cat_totals) or 1
        for i, c in enumerate(cat_totals):
            bg = t["bg_row_even"] if i % 2 == 0 else t["bg_row_odd"]
            pct = round(c["total"] / grand * 100, 1)
            for col, val in enumerate([c["category"], fmt_currency(c["total"]), f"{pct}%"]):
                tk.Label(f, text=val, font=("Segoe UI", 8), bg=bg,
                         fg=t["text_primary"], anchor="w", pady=4).grid(
                    row=i+1, column=col, sticky="nsew", padx=(0, 1))

    # ── Monthly Tab ───────────────────────────────────────────────────────────

    def _build_monthly(self, t: dict):
        for w in self._tab_monthly.winfo_children():
            w.destroy()

        monthly = db.get_monthly_totals()
        if not monthly:
            tk.Label(self._tab_monthly, text="No data to display.",
                     bg=t["bg_root"], fg=t["text_secondary"],
                     font=("Segoe UI", 10)).pack(pady=60)
            return

        months   = [fmt_month(r["month"])   for r in monthly]
        incomes  = [r["income"]   for r in monthly]
        expenses = [r["expenses"] for r in monthly]

        col_frame = tk.Frame(self._tab_monthly, bg=t["bg_root"])
        col_frame.pack(fill="both", expand=True)
        col_frame.columnconfigure(0, weight=1)
        col_frame.columnconfigure(1, weight=1)
        col_frame.rowconfigure(0, weight=1)

        # Bar chart
        bar_card = self._card(col_frame, "Income vs Expenses by Month")
        bar_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)
        self._draw_bar(bar_card, months, incomes, expenses, t)

        # Line chart
        line_card = self._card(col_frame, "Monthly Spending Trend")
        line_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)
        self._draw_line(line_card, months, incomes, expenses, t)

    def _draw_bar(self, parent, months, incomes, expenses, t):
        fig = Figure(figsize=(5, 3.5), dpi=96, tight_layout=True)
        ax  = fig.add_subplot(111)
        _apply_fig_style(fig, ax, t)

        x     = range(len(months))
        width = 0.35
        ax.bar([i - width/2 for i in x], incomes,  width, color=t["income_green"],
               label="Income",  alpha=0.85)
        ax.bar([i + width/2 for i in x], expenses, width, color=t["expense_red"],
               label="Expenses", alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels(months, rotation=40, ha="right", fontsize=7,
                            color=t["text_secondary"])
        ax.legend(fontsize=7, labelcolor=t["text_secondary"],
                  framealpha=0, loc="upper left")
        ax.yaxis.set_tick_params(labelcolor=t["text_secondary"])

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        self._canvases.append(canvas)

    def _draw_line(self, parent, months, incomes, expenses, t):
        fig = Figure(figsize=(5, 3.5), dpi=96, tight_layout=True)
        ax  = fig.add_subplot(111)
        _apply_fig_style(fig, ax, t)

        x = list(range(len(months)))
        ax.plot(x, incomes,  "o-", color=t["income_green"],  linewidth=2,
                markersize=5, label="Income")
        ax.plot(x, expenses, "o-", color=t["expense_red"],   linewidth=2,
                markersize=5, label="Expenses")
        ax.fill_between(x, expenses, incomes, alpha=0.08,
                         color=t["accent"])
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=40, ha="right", fontsize=7,
                            color=t["text_secondary"])
        ax.legend(fontsize=7, labelcolor=t["text_secondary"],
                  framealpha=0, loc="upper left")
        ax.yaxis.set_tick_params(labelcolor=t["text_secondary"])

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        self._canvases.append(canvas)

    # ── Budget Tab ────────────────────────────────────────────────────────────

    def _build_budget(self, t: dict):
        for w in self._tab_budget.winfo_children():
            w.destroy()

        month  = self._month_var.get()
        status = db.get_budget_status(month)

        card = self._card(self._tab_budget, f"Budget Status — {fmt_month(month)}")
        card.pack(fill="both", expand=True, padx=4, pady=4)

        canvas_frame = tk.Frame(card, bg=t["bg_card"])
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=8)

        if not status:
            tk.Label(canvas_frame, text="No budgets set. Add budgets in Settings.",
                     bg=t["bg_card"], fg=t["text_secondary"],
                     font=("Segoe UI", 10)).pack(pady=40)
            return

        for s in status:
            row = tk.Frame(canvas_frame, bg=t["bg_card"])
            row.pack(fill="x", pady=4)
            label_color = t["expense_red"] if s["over_budget"] else t["text_primary"]
            tk.Label(row, text=s["category"], width=16, anchor="w",
                     font=("Segoe UI", 9), bg=t["bg_card"],
                     fg=label_color).pack(side="left")
            # Progress bar container
            bar_bg = tk.Frame(row, bg=t["border"], height=14)
            bar_bg.pack(side="left", fill="x", expand=True, padx=4)
            bar_bg.pack_propagate(False)
            pct     = min(s["percent"], 100)
            fill_c  = t["expense_red"] if s["over_budget"] else (
                t["warning"] if pct >= 80 else t["income_green"]
            )
            bar_fill = tk.Frame(bar_bg, bg=fill_c, height=14)
            bar_fill.place(x=0, y=0, relwidth=pct/100, relheight=1)
            # Numbers
            tk.Label(row, text=f"{fmt_currency(s['spent'])} / {fmt_currency(s['budget'])}",
                     font=("Segoe UI", 8), bg=t["bg_card"],
                     fg=t["text_secondary"], width=22, anchor="e").pack(side="left")
            tk.Label(row, text=f"{s['percent']}%",
                     font=("Segoe UI", 8, "bold"), bg=t["bg_card"],
                     fg=label_color, width=6, anchor="e").pack(side="left")

    # ── Helper ────────────────────────────────────────────────────────────────

    def _card(self, parent, title: str) -> tk.Frame:
        t = self.app.theme
        frame = tk.Frame(parent, bg=t["bg_card"],
                         highlightbackground=t["border"], highlightthickness=1)
        tk.Label(frame, text=title, font=("Segoe UI", 11, "bold"),
                 bg=t["bg_card"], fg=t["text_primary"]).pack(
            anchor="w", padx=12, pady=(10, 4))
        tk.Frame(frame, height=1, bg=t["border"]).pack(fill="x", padx=12)
        return frame
