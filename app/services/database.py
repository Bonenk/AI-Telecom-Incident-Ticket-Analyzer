import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import AppConfig


class TicketDatabase:
    def __init__(self, db_path: str | Path | None = None):
        cfg = AppConfig()
        self.db_path = Path(db_path) if db_path else cfg.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ticket_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    subject TEXT,
                    description TEXT,
                    category TEXT,
                    confidence REAL,
                    severity TEXT,
                    severity_score INTEGER,
                    classification_reasoning TEXT,
                    severity_reasoning TEXT,
                    resolution TEXT,
                    resolution_eta TEXT,
                    resolution_sources TEXT,
                    human_decision TEXT,
                    human_feedback TEXT,
                    human_edited_resolution TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS synthetic_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    category TEXT,
                    severity TEXT,
                    status TEXT,
                    subject TEXT,
                    description TEXT,
                    customer_name TEXT,
                    customer_account TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    created_at TEXT,
                    resolved_at TEXT,
                    resolution TEXT,
                    priority_score INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    outage_id TEXT NOT NULL,
                    area TEXT,
                    device TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration_hours REAL,
                    affected_customers INTEGER,
                    root_cause TEXT,
                    status TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pdf_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    file_size INTEGER DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'manual',
                    uploaded_at TEXT DEFAULT (datetime('now'))
                )
            """)

    def save_analysis(self, state: dict, human_decision: dict | None = None, ticket: dict | None = None) -> int:
        t = ticket or state.get("ticket", {})
        hd = human_decision or {}

        data = {
            "ticket_id": t.get("ticket_id", "CUSTOM"),
            "subject": t.get("subject", ""),
            "description": t.get("description", ""),
            "category": state.get("category", ""),
            "confidence": state.get("classification_confidence", 0.0),
            "severity": state.get("severity", ""),
            "severity_score": state.get("severity_score", 0),
            "classification_reasoning": state.get("classification_reasoning", ""),
            "severity_reasoning": state.get("severity_reasoning", ""),
            "resolution": hd.get("edited_resolution") or state.get("resolution", ""),
            "resolution_eta": state.get("resolution_eta", ""),
            "resolution_sources": json.dumps(state.get("resolution_sources", [])),
            "human_decision": hd.get("decision"),
            "human_feedback": hd.get("feedback"),
            "human_edited_resolution": hd.get("edited_resolution"),
            "created_at": datetime.now().isoformat(),
        }

        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                """INSERT INTO ticket_analyses
                   (ticket_id, subject, description, category, confidence, severity,
                    severity_score, classification_reasoning, severity_reasoning,
                    resolution, resolution_eta, resolution_sources,
                    human_decision, human_feedback, human_edited_resolution, created_at)
                   VALUES (:ticket_id, :subject, :description, :category, :confidence, :severity,
                           :severity_score, :classification_reasoning, :severity_reasoning,
                           :resolution, :resolution_eta, :resolution_sources,
                           :human_decision, :human_feedback, :human_edited_resolution, :created_at)""",
                data,
            )
            return cur.lastrowid

    def list_analyses(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM ticket_analyses ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(r) | {"resolution_sources": json.loads(r["resolution_sources"]) if r["resolution_sources"] else []} for r in rows]

    def get_analysis(self, analysis_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM ticket_analyses WHERE id = ?", (analysis_id,)
            ).fetchone()
            if row:
                d = dict(row)
                d["resolution_sources"] = json.loads(d["resolution_sources"]) if d.get("resolution_sources") else []
                return d
            return None

    def delete_open_analyses(self, ticket_id: str) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                "DELETE FROM ticket_analyses WHERE ticket_id = ? AND (human_decision IS NULL OR human_decision = '')",
                (ticket_id,),
            )
            return cur.rowcount

    def update_analysis(self, analysis_id: int, updates: dict) -> bool:
        allowed = {
            "human_decision", "human_feedback", "human_edited_resolution",
            "resolution", "resolution_eta", "resolution_sources",
        }
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            return False
        if "resolution_sources" in fields:
            fields["resolution_sources"] = json.dumps(fields["resolution_sources"])
        fields["id"] = analysis_id
        set_clause = ", ".join(f"{k} = :{k}" for k in fields if k != "id")
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                f"UPDATE ticket_analyses SET {set_clause} WHERE id = :id",
                fields,
            )
            return cur.rowcount > 0

    def delete_analysis(self, analysis_id: int) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM ticket_analyses WHERE id = ?", (analysis_id,))
            return cur.rowcount > 0

    def count_analyses(self) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            return conn.execute("SELECT COUNT(*) FROM ticket_analyses").fetchone()[0]

    def seed_synthetic_data(self, tickets: list[dict], outage_logs: list[dict]):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM synthetic_tickets")
            conn.execute("DELETE FROM outage_logs")
            for t in tickets:
                conn.execute(
                    """INSERT INTO synthetic_tickets
                       (ticket_id, category, severity, status, subject, description,
                        customer_name, customer_account, contact_email, contact_phone,
                        created_at, resolved_at, resolution, priority_score)
                       VALUES (:ticket_id, :category, :severity, :status, :subject, :description,
                               :customer_name, :customer_account, :contact_email, :contact_phone,
                               :created_at, :resolved_at, :resolution, :priority_score)""",
                    t,
                )
            for log in outage_logs:
                conn.execute(
                    """INSERT INTO outage_logs
                       (outage_id, area, device, start_time, end_time,
                        duration_hours, affected_customers, root_cause, status)
                       VALUES (:outage_id, :area, :device, :start_time, :end_time,
                               :duration_hours, :affected_customers, :root_cause, :status)""",
                    log,
                )

    def list_synthetic_tickets(self) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM synthetic_tickets ORDER BY id ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def list_outage_logs(self) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM outage_logs ORDER BY id ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def save_pdf_document(self, filename: str, file_size: int = 0, chunk_count: int = 0, source: str = "manual") -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            existing = conn.execute(
                "SELECT id FROM pdf_documents WHERE filename = ?", (filename,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE pdf_documents SET file_size = ?, chunk_count = ?, source = ?, uploaded_at = datetime('now') WHERE filename = ?",
                    (file_size, chunk_count, source, filename),
                )
                return existing[0]
            cur = conn.execute(
                "INSERT INTO pdf_documents (filename, file_size, chunk_count, source) VALUES (?, ?, ?, ?)",
                (filename, file_size, chunk_count, source),
            )
            return cur.lastrowid

    def list_pdf_documents(self) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM pdf_documents ORDER BY uploaded_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_pdf_document(self, filename: str) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM pdf_documents WHERE filename = ?", (filename,))
            return cur.rowcount > 0
