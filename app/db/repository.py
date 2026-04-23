import sqlite3
import sys
import os
from pathlib import Path

class ScanHistory:
    def __init__(self, db_path: str = "scans.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    status TEXT,
                    service TEXT,
                    banner TEXT,
                    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _get_db_path() -> Path:
        """Возвращает путь к БД: в %APPDATA% для персистентности"""
        if hasattr(sys, '_MEIPASS'):
            # Режим EXE: сохраняем в AppData, а не во временную папку
            appdata = Path(os.getenv('APPDATA', Path.home() / '.config')) / 'NetScanner'
            appdata.mkdir(parents=True, exist_ok=True)
            return appdata / "scans.db"
        else:
            # Режим разработки: локально в проекте
            return Path(__file__).parent.parent.parent / "scans.db"
        
    def save_results(self, host: str, results: list):
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO scans (host, port, status, service, banner) VALUES (?, ?, ?, ?, ?)",
                [(host, r['Port'], r['Status'], r['Service'], r['Banner']) for r in results]
            )
    
    def get_history(self, host: str = None, limit: int = 100):
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM scans"
            params = []
            if host:
                query += " WHERE host = ?"
                params.append(host)
            query += " ORDER BY scanned_at DESC LIMIT ?"
            params.append(limit)
            return conn.execute(query, params).fetchall()