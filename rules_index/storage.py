import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .chunking import RuleChunk


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    heading_path: str
    file: str
    entity_type: str
    entity_name: str
    body: str
    rank: float


class RuleIndexStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def setup(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                source_system TEXT NOT NULL,
                file TEXT NOT NULL,
                heading_path TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                body TEXT NOT NULL,
                commit_or_release TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(
                heading_path,
                body,
                content='chunks',
                content_rowid='rowid'
            )
            """
        )
        self.conn.commit()

    def replace_chunks(self, chunks: list[RuleChunk]) -> None:
        self.conn.execute("DELETE FROM chunks")
        self.conn.executemany(
            """
            INSERT INTO chunks (
                chunk_id, source_system, file, heading_path,
                entity_type, entity_name, body, commit_or_release
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.chunk_id,
                    chunk.source_system,
                    chunk.file,
                    chunk.heading_path,
                    chunk.entity_type,
                    chunk.entity_name,
                    chunk.body,
                    chunk.commit_or_release,
                )
                for chunk in chunks
            ],
        )
        self.rebuild_fts()

    def rebuild_fts(self) -> None:
        self.conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        self.conn.commit()

    def search(
        self,
        query: str,
        *,
        entity_type: str | None = None,
        limit: int = 5,
    ) -> list[SearchHit]:
        where = "chunks_fts MATCH ?"
        params: list[object] = [query]
        if entity_type:
            where += " AND c.entity_type = ?"
            params.append(entity_type)
        params.append(limit)

        rows = self.conn.execute(
            f"""
            SELECT
                c.chunk_id,
                c.heading_path,
                c.file,
                c.entity_type,
                c.entity_name,
                c.body,
                bm25(chunks_fts, 2.0, 1.0) AS rank
            FROM chunks_fts
            JOIN chunks c ON c.rowid = chunks_fts.rowid
            WHERE {where}
            ORDER BY rank ASC
            LIMIT ?
            """,
            params,
        ).fetchall()

        return [
            SearchHit(
                chunk_id=row["chunk_id"],
                heading_path=row["heading_path"],
                file=row["file"],
                entity_type=row["entity_type"],
                entity_name=row["entity_name"],
                body=row["body"],
                rank=float(row["rank"]),
            )
            for row in rows
        ]
