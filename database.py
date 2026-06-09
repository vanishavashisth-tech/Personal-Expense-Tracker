"""
database.py - SQLite database management for Personal Expense Tracker
Handles all database operations: creation, CRUD, backup/restore.
"""

import sqlite3
import os
import shutil
import csv
from datetime import datetime
from typing import Optional


DB_PATH = "expense_tracker.db"


def get_connection() -> sqlite3.Connection:
    """Return a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    """Create all tables if they do not exist and seed sample data."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL    NOT NULL CHECK(amount > 0),
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT,
                type        TEXT    NOT NULL CHECK(type IN ('Income','Expense')),
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT    NOT NULL UNIQUE,
                amount      REAL    NOT NULL CHECK(amount > 0),
                period      TEXT    NOT NULL DEFAULT 'monthly',
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Settings table (key-value store)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Insert default settings if absent
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES
                ('dark_mode', '0'),
                ('currency', 'USD'),
                ('alert_threshold', '90')
        """)

        conn.commit()

        # Seed sample data only on a fresh DB
        cursor.execute("SELECT COUNT(*) FROM transactions")
        if cursor.fetchone()[0] == 0:
            _seed_sample_data(conn)


def _seed_sample_data(conn: sqlite3.Connection):
    """Insert representative sample transactions for demonstration."""
    samples = [
        # Income
        (5000.00, "Salary",      "2025-01-01", "Monthly salary",        "Income"),
        (800.00,  "Freelance",   "2025-01-10", "Web design project",    "Income"),
        (5000.00, "Salary",      "2025-02-01", "Monthly salary",        "Income"),
        (300.00,  "Investment",  "2025-02-14", "Dividend payout",       "Income"),
        (5000.00, "Salary",      "2025-03-01", "Monthly salary",        "Income"),
        (5000.00, "Salary",      "2025-04-01", "Monthly salary",        "Income"),
        (5000.00, "Salary",      "2025-05-01", "Monthly salary",        "Income"),
        (5000.00, "Salary",      "2025-06-01", "Monthly salary",        "Income"),
        # Expenses
        (1200.00, "Housing",     "2025-01-03", "Rent payment",          "Expense"),
        (250.00,  "Food",        "2025-01-07", "Grocery shopping",      "Expense"),
        (80.00,   "Transport",   "2025-01-09", "Monthly bus pass",      "Expense"),
        (120.00,  "Utilities",   "2025-01-15", "Electricity bill",      "Expense"),
        (60.00,   "Healthcare",  "2025-01-18", "Pharmacy",              "Expense"),
        (45.00,   "Entertainment","2025-01-22","Streaming services",    "Expense"),
        (200.00,  "Food",        "2025-01-28", "Restaurant dinner",     "Expense"),
        (1200.00, "Housing",     "2025-02-03", "Rent payment",          "Expense"),
        (270.00,  "Food",        "2025-02-09", "Grocery shopping",      "Expense"),
        (90.00,   "Transport",   "2025-02-12", "Fuel",                  "Expense"),
        (130.00,  "Utilities",   "2025-02-16", "Water & gas",           "Expense"),
        (320.00,  "Shopping",    "2025-02-20", "Clothing",              "Expense"),
        (1200.00, "Housing",     "2025-03-03", "Rent payment",          "Expense"),
        (240.00,  "Food",        "2025-03-06", "Grocery shopping",      "Expense"),
        (75.00,   "Transport",   "2025-03-10", "Monthly bus pass",      "Expense"),
        (150.00,  "Healthcare",  "2025-03-15", "Doctor visit",          "Expense"),
        (500.00,  "Education",   "2025-03-20", "Online course",         "Expense"),
        (1200.00, "Housing",     "2025-04-03", "Rent payment",          "Expense"),
        (260.00,  "Food",        "2025-04-07", "Grocery shopping",      "Expense"),
        (100.00,  "Transport",   "2025-04-10", "Fuel",                  "Expense"),
        (200.00,  "Entertainment","2025-04-18","Concert tickets",       "Expense"),
        (1200.00, "Housing",     "2025-05-03", "Rent payment",          "Expense"),
        (290.00,  "Food",        "2025-05-08", "Grocery shopping",      "Expense"),
        (80.00,   "Transport",   "2025-05-11", "Monthly bus pass",      "Expense"),
        (140.00,  "Utilities",   "2025-05-16", "Electricity bill",      "Expense"),
        (1200.00, "Housing",     "2025-06-03", "Rent payment",          "Expense"),
        (280.00,  "Food",        "2025-06-08", "Grocery shopping",      "Expense"),
    ]
    conn.executemany(
        "INSERT INTO transactions (amount, category, date, description, type) VALUES (?,?,?,?,?)",
        samples,
    )

    # Sample budgets
    budgets = [
        ("Housing", 1300.00),
        ("Food", 400.00),
        ("Transport", 150.00),
        ("Utilities", 200.00),
        ("Healthcare", 200.00),
        ("Entertainment", 150.00),
        ("Shopping", 300.00),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO budgets (category, amount) VALUES (?,?)", budgets
    )
    conn.commit()


# ──────────────────────────── Transactions ────────────────────────────

def add_transaction(amount: float, category: str, date: str,
                    description: str, t_type: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO transactions (amount, category, date, description, type) VALUES (?,?,?,?,?)",
            (amount, category, date, description, t_type),
        )
        conn.commit()
        return cur.lastrowid


def get_transactions(start_date: str = "", end_date: str = "",
                     category: str = "", t_type: str = "",
                     search: str = "") -> list:
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if t_type and t_type != "All":
        query += " AND type = ?"
        params.append(t_type)
    if search:
        query += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY date DESC, id DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def update_transaction(tx_id: int, amount: float, category: str,
                       date: str, description: str, t_type: str):
    with get_connection() as conn:
        conn.execute(
            """UPDATE transactions
               SET amount=?, category=?, date=?, description=?, type=?
               WHERE id=?""",
            (amount, category, date, description, t_type, tx_id),
        )
        conn.commit()


def delete_transaction(tx_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
        conn.commit()


def get_summary() -> dict:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type='Income'  THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END), 0) AS total_expenses
            FROM transactions
        """).fetchone()
    return {
        "total_income":   row["total_income"],
        "total_expenses": row["total_expenses"],
        "balance":        row["total_income"] - row["total_expenses"],
    }


def get_category_totals(t_type: str = "Expense") -> list:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT category, SUM(amount) AS total
            FROM transactions WHERE type=?
            GROUP BY category ORDER BY total DESC
        """, (t_type,)).fetchall()
    return [dict(r) for r in rows]


def get_monthly_totals() -> list:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT strftime('%Y-%m', date) AS month,
                   SUM(CASE WHEN type='Income'  THEN amount ELSE 0 END) AS income,
                   SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) AS expenses
            FROM transactions
            GROUP BY month ORDER BY month
        """).fetchall()
    return [dict(r) for r in rows]


def get_all_categories() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM transactions ORDER BY category"
        ).fetchall()
    return [r["category"] for r in rows]


# ──────────────────────────── Budgets ────────────────────────────

def set_budget(category: str, amount: float):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO budgets (category, amount, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(category) DO UPDATE SET amount=excluded.amount,
                                                updated_at=excluded.updated_at
        """, (category, amount))
        conn.commit()


def get_budgets() -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()
    return [dict(r) for r in rows]


def get_budget_status(month: Optional[str] = None) -> list:
    """Return each budget with actual spending for the given month (YYYY-MM)."""
    month = month or datetime.now().strftime("%Y-%m")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT b.category, b.amount AS budget,
                   COALESCE(SUM(t.amount), 0) AS spent
            FROM budgets b
            LEFT JOIN transactions t
                   ON t.category = b.category
                  AND t.type = 'Expense'
                  AND strftime('%Y-%m', t.date) = ?
            GROUP BY b.category
        """, (month,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["percent"] = round(d["spent"] / d["budget"] * 100, 1) if d["budget"] else 0
        d["over_budget"] = d["spent"] > d["budget"]
        result.append(d)
    return result


# ──────────────────────────── Settings ────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


# ──────────────────────────── Backup / Restore ────────────────────────────

def backup_db(dest_path: str) -> bool:
    try:
        shutil.copy2(DB_PATH, dest_path)
        return True
    except Exception:
        return False


def restore_db(src_path: str) -> bool:
    try:
        shutil.copy2(src_path, DB_PATH)
        return True
    except Exception:
        return False


# ──────────────────────────── CSV Export ────────────────────────────

def export_to_csv(filepath: str, transactions: list) -> bool:
    try:
        if not transactions:
            return False
        fieldnames = ["id", "date", "type", "category", "amount", "description"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(transactions)
        return True
    except Exception:
        return False
