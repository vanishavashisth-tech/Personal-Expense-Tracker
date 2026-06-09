"""
dashboard.py - Dashboard frame: summary cards, recent transactions,
               quick-add form, and budget alerts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import database as db
from utils import fmt_currency, fmt_date, get_theme, today_str
from models import Transaction, INCOME_CATEGORIES, EXPENSE_CATEGORIES


class DashboardFrame(tk.Frame):
    """
    Main dashboard shown on app launch.
    Displays:
      - Summary cards (Income / Expenses / Balance / Savings Rate)
      - Budget alert banner
      - Recent transactions list
      - Quick-add transaction panel
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        t = self.app.theme
        self.configure(bg=t["bg_root"])

        # Title bar
        title_bar = tk.Frame(self, bg=t["bg_root"])
        title_bar.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(
            title_bar, text="Dashboard", font=("Segoe UI", 20, "bold"),
            bg=t["bg_root"], fg=t["text_primary"],
        ).pack(side="left")

        # ── Summary cards row ─────────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg=t["bg_root"])
        cards_frame.pack(fill="x", padx=24, pady=(14, 0))
        for col in range(4):
            cards_frame.columnconfigure(col, weight=1, uniform="card")
        self._cards_frame = cards_frame

        # ── Middle section: alerts + recent ───────────────────────────────────
        mid = tk.Frame(self, bg=t["bg_root"])
        mid.pack(fill="both", expand=True, padx=24, pady=10)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=1)

        # Recent transactions
        recent_card = self._card(mid, "Recent Transactions")
        recent_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._recent_inner = tk.Frame(recent_card, bg=t["bg_card"])
        self._recent_inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Quick-add panel
        add_card = self._card(mid, "Quick Add")
        add_card.grid(row=0, column=1, sticky="nsew")
        self._build_quick_add(add_card)

        # Budget alert (hidden by default)
        self._alert_var = tk.StringVar()
        self._alert_label = tk.Label(
            self, textvariable=self._alert_var, font=("Segoe UI", 9),
            bg=t["warning"], fg="#FFFFFF", padx=12, pady=6,
        )

        self.refresh()

    # ── Quick-Add Panel ───────────────────────────────────────────────────────

    def _build_quick_add(self, parent):
        t = self.app.theme
        f = tk.Frame(parent, bg=t["bg_card"])
        f.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        def row(label_text, widget_fn):
            tk.Label(f, text=label_text, font=("Segoe UI", 9),
                     bg=t["bg_card"], fg=t["text_secondary"]).pack(anchor="w", pady=(6, 1))
            w = widget_fn()
            w.pack(fill="x")
            return w

        # Type toggle
        type_frame = tk.Frame(f, bg=t["bg_card"])
        type_frame.pack(fill="x", pady=(6, 1))
        tk.Label(type_frame, text="Type", font=("Segoe UI", 9),
                 bg=t["bg_card"], fg=t["text_secondary"]).pack(anchor="w")
        btn_row = tk.Frame(type_frame, bg=t["bg_card"])
        btn_row.pack(fill="x")
        self._qa_type = tk.StringVar(value="Expense")
        for val, color in [("Expense", t["expense_red"]), ("Income", t["income_green"])]:
            btn = tk.Button(
                btn_row, text=val, font=("Segoe UI", 9, "bold"),
                bg=color if self._qa_type.get() == val else t["bg_input"],
                fg=t["text_white"] if self._qa_type.get() == val else t["text_secondary"],
                relief="flat", padx=10, cursor="hand2",
                command=lambda v=val: self._set_qa_type(v),
            )
            btn.pack(side="left", expand=True, fill="x", padx=(0, 4 if val == "Expense" else 0))
        self._qa_type_btns = btn_row

        # Amount
        self._qa_amount = row("Amount", lambda: self._entry(f))

        # Category
        tk.Label(f, text="Category", font=("Segoe UI", 9),
                 bg=t["bg_card"], fg=t["text_secondary"]).pack(anchor="w", pady=(6, 1))
        self._qa_cat = ttk.Combobox(f, state="readonly",
                                     values=EXPENSE_CATEGORIES, font=("Segoe UI", 9))
        self._qa_cat.current(0)
        self._qa_cat.pack(fill="x")

        # Date
        self._qa_date = row("Date (YYYY-MM-DD)", lambda: self._entry(f, default=today_str()))

        # Description
        self._qa_desc = row("Description", lambda: self._entry(f))

        # Submit button
        tk.Button(
            f, text="Add Transaction", font=("Segoe UI", 10, "bold"),
            bg=t["accent"], fg=t["text_white"], relief="flat",
            padx=0, pady=8, cursor="hand2",
            command=self._submit_quick_add,
        ).pack(fill="x", pady=(12, 0))

    def _set_qa_type(self, val: str):
        self._qa_type.set(val)
        t = self.app.theme
        cats = EXPENSE_CATEGORIES if val == "Expense" else INCOME_CATEGORIES
        self._qa_cat.configure(values=cats)
        self._qa_cat.current(0)
        # Update button styles
        for btn in self._qa_type_btns.winfo_children():
            label = btn.cget("text")
            if label == val:
                color = t["expense_red"] if val == "Expense" else t["income_green"]
                btn.configure(bg=color, fg=t["text_white"])
            else:
                btn.configure(bg=t["bg_input"], fg=t["text_secondary"])

    def _submit_quick_add(self):
        amount_str = self._qa_amount.get().strip()
        category   = self._qa_cat.get()
        date_str   = self._qa_date.get().strip()
        desc       = self._qa_desc.get().strip()
        tx_type    = self._qa_type.get()

        # Validate
        try:
            amount = float(amount_str.replace(",", ""))
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation", "Please enter a valid positive amount.")
            return

        from utils import validate_date
        if not validate_date(date_str):
            messagebox.showerror("Validation", "Date must be in YYYY-MM-DD format.")
            return

        db.add_transaction(amount, category, date_str, desc, tx_type)
        self._qa_amount.delete(0, "end")
        self._qa_desc.delete(0, "end")
        self.app.refresh_all()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        t = self.app.theme
        self.configure(bg=t["bg_root"])
        summary = db.get_summary()
        self._build_cards(summary, t)
        self._build_recent(t)
        self._check_alerts(t)

    def _build_cards(self, s: dict, t: dict):
        for w in self._cards_frame.winfo_children():
            w.destroy()

        cards_data = [
            ("Total Income",   s["total_income"],   t["income_green"], "▲"),
            ("Total Expenses", s["total_expenses"],  t["expense_red"],  "▼"),
            ("Balance",        s["balance"],          t["accent"],       "◉"),
            ("Savings Rate",   None,                  t["info"],         "%"),
        ]
        savings_rate = (
            round(s["balance"] / s["total_income"] * 100, 1)
            if s["total_income"] else 0.0
        )

        for col, (title, val, color, icon) in enumerate(cards_data):
            card = tk.Frame(self._cards_frame, bg=t["bg_card"],
                            highlightbackground=t["border"],
                            highlightthickness=1)
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0, 8 if col < 3 else 0), pady=4, ipady=8)

            tk.Label(card, text=icon, font=("Segoe UI", 20),
                     bg=color, fg=t["text_white"], width=3).pack(side="left",
                                                                  fill="y", padx=(0, 0))
            inner = tk.Frame(card, bg=t["bg_card"])
            inner.pack(side="left", fill="both", expand=True, padx=10, pady=8)
            tk.Label(inner, text=title, font=("Segoe UI", 8),
                     bg=t["bg_card"], fg=t["text_secondary"]).pack(anchor="w")
            if title == "Savings Rate":
                display = f"{savings_rate}%"
            else:
                display = fmt_currency(val)
            tk.Label(inner, text=display, font=("Segoe UI", 14, "bold"),
                     bg=t["bg_card"],
                     fg=(t["income_green"] if val >= 0 else t["expense_red"])
                        if title == "Balance"
                        else t["text_primary"]).pack(anchor="w")

    def _build_recent(self, t: dict):
        for w in self._recent_inner.winfo_children():
            w.destroy()

        txns = db.get_transactions()[:10]
        if not txns:
            tk.Label(self._recent_inner, text="No transactions yet.",
                     bg=t["bg_card"], fg=t["text_secondary"],
                     font=("Segoe UI", 9)).pack(pady=20)
            return

        cols = ("Date", "Category", "Description", "Amount", "Type")
        tree = ttk.Treeview(self._recent_inner, columns=cols,
                             show="headings", height=8)
        for col, width in zip(cols, (90, 110, 180, 90, 70)):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")

        tree.tag_configure("income",  foreground=t["income_green"])
        tree.tag_configure("expense", foreground=t["expense_red"])

        for tx in txns:
            tag = "income" if tx["type"] == "Income" else "expense"
            sign = "+" if tx["type"] == "Income" else "-"
            tree.insert("", "end", values=(
                fmt_date(tx["date"]), tx["category"],
                tx["description"][:35], f"{sign}{fmt_currency(tx['amount'])}",
                tx["type"],
            ), tags=(tag,))

        scrollbar = ttk.Scrollbar(self._recent_inner, orient="vertical",
                                   command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _check_alerts(self, t: dict):
        threshold = int(db.get_setting("alert_threshold", "90"))
        alerts = [
            s for s in db.get_budget_status()
            if s["percent"] >= threshold
        ]
        if alerts:
            names = ", ".join(s["category"] for s in alerts)
            self._alert_var.set(
                f"⚠  Budget alert: {names} at or near limit  ({threshold}% threshold)"
            )
            self._alert_label.pack(fill="x", before=self._cards_frame.winfo_children()[0]
                                    if self._cards_frame.winfo_children() else None)
        else:
            self._alert_label.pack_forget()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _card(self, parent, title: str) -> tk.Frame:
        t = self.app.theme
        frame = tk.Frame(parent, bg=t["bg_card"],
                         highlightbackground=t["border"],
                         highlightthickness=1)
        tk.Label(frame, text=title, font=("Segoe UI", 11, "bold"),
                 bg=t["bg_card"], fg=t["text_primary"]).pack(
            anchor="w", padx=12, pady=(10, 4))
        sep = tk.Frame(frame, height=1, bg=t["border"])
        sep.pack(fill="x", padx=12)
        return frame

    def _entry(self, parent, default: str = "") -> tk.Entry:
        t = self.app.theme
        e = tk.Entry(parent, font=("Segoe UI", 9),
                     bg=t["bg_input"], fg=t["text_primary"],
                     insertbackground=t["text_primary"],
                     relief="flat", highlightthickness=1,
                     highlightbackground=t["border"],
                     highlightcolor=t["border_focus"])
        if default:
            e.insert(0, default)
        return e
