"""
models.py - Data models / value objects for Personal Expense Tracker.
Pure Python dataclasses; no database imports here.
"""

from dataclasses import dataclass, field
from datetime import date as Date
from typing import Optional


# ── Valid categories ──────────────────────────────────────────────────────────

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Investment", "Rental", "Gift", "Bonus", "Other Income"
]

EXPENSE_CATEGORIES = [
    "Housing", "Food", "Transport", "Utilities", "Healthcare",
    "Entertainment", "Shopping", "Education", "Insurance", "Personal Care",
    "Savings", "Debt", "Other Expense"
]

ALL_CATEGORIES = sorted(set(INCOME_CATEGORIES + EXPENSE_CATEGORIES))


# ── Transaction ───────────────────────────────────────────────────────────────

@dataclass
class Transaction:
    amount:      float
    category:    str
    date:        str           # ISO format: YYYY-MM-DD
    description: str
    type:        str           # "Income" | "Expense"
    id:          Optional[int] = None
    created_at:  Optional[str] = None

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """Return a list of human-readable error strings (empty = valid)."""
        errors: list[str] = []
        try:
            val = float(self.amount)
            if val <= 0:
                errors.append("Amount must be greater than zero.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")

        if not self.category or self.category.strip() == "":
            errors.append("Category is required.")

        try:
            Date.fromisoformat(self.date)
        except (TypeError, ValueError):
            errors.append("Date must be in YYYY-MM-DD format.")

        if self.type not in ("Income", "Expense"):
            errors.append("Type must be Income or Expense.")

        return errors

    # ── Convenience ───────────────────────────────────────────────────────────

    @property
    def signed_amount(self) -> float:
        return self.amount if self.type == "Income" else -self.amount

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "amount":      self.amount,
            "category":    self.category,
            "date":        self.date,
            "description": self.description,
            "type":        self.type,
            "created_at":  self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            id=d.get("id"),
            amount=d.get("amount", 0),
            category=d.get("category", ""),
            date=d.get("date", ""),
            description=d.get("description", ""),
            type=d.get("type", ""),
            created_at=d.get("created_at"),
        )


# ── Budget ────────────────────────────────────────────────────────────────────

@dataclass
class Budget:
    category: str
    amount:   float
    period:   str = "monthly"
    id:       Optional[int] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        try:
            val = float(self.amount)
            if val <= 0:
                errors.append("Budget amount must be greater than zero.")
        except (TypeError, ValueError):
            errors.append("Budget amount must be a valid number.")
        if not self.category:
            errors.append("Category is required.")
        return errors


# ── Summary (thin DTO) ────────────────────────────────────────────────────────

@dataclass
class Summary:
    total_income:   float = 0.0
    total_expenses: float = 0.0

    @property
    def balance(self) -> float:
        return self.total_income - self.total_expenses

    @property
    def savings_rate(self) -> float:
        if self.total_income == 0:
            return 0.0
        return round(self.balance / self.total_income * 100, 1)
