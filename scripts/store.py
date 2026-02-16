"""
SQLite storage for LLM Cost Monitor
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class UsageStore:
    def __init__(self, storage_path: str = "~/.llm-cost-monitor"):
        self.storage_path = os.path.expanduser(storage_path)
        os.makedirs(self.storage_path, exist_ok=True)
        self.db_path = os.path.join(self.storage_path, "usage.db")
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Usage records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                provider TEXT NOT NULL,
                api_key_hash TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cache_read_tokens INTEGER DEFAULT 0,
                cache_creation_tokens INTEGER DEFAULT 0,
                cost REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, provider, api_key_hash, model)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_date_provider
            ON usage_records(date, provider)
        """)

        conn.commit()
        conn.close()

    def add_usage(
        self,
        date: str,
        provider: str,
        api_key: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cost: float = 0.0
    ):
        """Add or update usage record"""
        key_hash = self._hash_key(api_key)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try to insert, update if exists
        cursor.execute("""
            INSERT INTO usage_records
            (date, provider, api_key_hash, model, input_tokens, output_tokens,
             cache_read_tokens, cache_creation_tokens, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, provider, api_key_hash, model)
            DO UPDATE SET
                input_tokens = usage_records.input_tokens + excluded.input_tokens,
                output_tokens = usage_records.output_tokens + excluded.output_tokens,
                cache_read_tokens = usage_records.cache_read_tokens + excluded.cache_read_tokens,
                cache_creation_tokens = usage_records.cache_creation_tokens + excluded.cache_creation_tokens,
                cost = usage_records.cost + excluded.cost
        """, (date, provider, key_hash, model, input_tokens, output_tokens,
              cache_read_tokens, cache_creation_tokens, cost))

        conn.commit()
        conn.close()

    def get_usage(
        self,
        start_date: str,
        end_date: str,
        provider: Optional[str] = None
    ) -> List[Dict]:
        """Get usage records for date range"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT date, provider, model,
                   SUM(input_tokens) as input_tokens,
                   SUM(output_tokens) as output_tokens,
                   SUM(cache_read_tokens) as cache_read_tokens,
                   SUM(cache_creation_tokens) as cache_creation_tokens,
                   SUM(cost) as cost
            FROM usage_records
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        query += " GROUP BY date, provider, model ORDER BY date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_total_cost(
        self,
        start_date: str,
        end_date: str,
        provider: Optional[str] = None
    ) -> float:
        """Get total cost for date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT SUM(cost) FROM usage_records WHERE date >= ? AND date <= ?"
        params = [start_date, end_date]

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        cursor.execute(query, params)
        result = cursor.fetchone()[0]
        conn.close()

        return result or 0.0

    def get_cost_by_model(
        self,
        start_date: str,
        end_date: str,
        provider: Optional[str] = None
    ) -> Dict[str, float]:
        """Get cost breakdown by model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT model, SUM(cost) as cost
            FROM usage_records
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        query += " GROUP BY model ORDER BY cost DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in rows}

    def get_cost_by_provider(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, float]:
        """Get cost breakdown by provider"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT provider, SUM(cost) as cost
            FROM usage_records
            WHERE date >= ? AND date <= ?
            GROUP BY provider
        """

        cursor.execute(query, [start_date, end_date])
        rows = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in rows}

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash API key for storage"""
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def get_store() -> UsageStore:
    """Get default usage store instance"""
    return UsageStore()


if __name__ == "__main__":
    # Test
    store = UsageStore("~/.llm-cost-monitor-test")
    print(f"Database initialized at: {store.db_path}")
