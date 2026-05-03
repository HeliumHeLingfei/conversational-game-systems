import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EntityRecord:
    resource_type: str
    index_key: str
    name: str
    payload: dict[str, Any]
    source_release: str


class EntityStore:
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
            CREATE TABLE IF NOT EXISTS entities (
                resource_type TEXT NOT NULL,
                index_key TEXT NOT NULL,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                source_release TEXT NOT NULL,
                PRIMARY KEY (resource_type, index_key)
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)"
        )
        self.conn.commit()

    def replace_entities(self, records: list[EntityRecord]) -> None:
        self.conn.execute("DELETE FROM entities")
        self.conn.executemany(
            """
            INSERT INTO entities(resource_type, index_key, name, payload_json, source_release)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    record.resource_type,
                    record.index_key,
                    record.name,
                    json.dumps(record.payload, ensure_ascii=False),
                    record.source_release,
                )
                for record in records
            ],
        )
        self.conn.commit()

    def ingest_json_snapshot(self, snapshot_root: Path, source_release: str) -> int:
        deduped: dict[tuple[str, str], EntityRecord] = {}
        for file_path in sorted(snapshot_root.rglob("*.json")):
            resource_type = self._infer_resource_type(file_path)
            parsed = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                maybe = self._record_from_obj(parsed, resource_type, source_release)
                if maybe:
                    deduped[(maybe.resource_type, maybe.index_key)] = maybe
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        maybe = self._record_from_obj(item, resource_type, source_release)
                        if maybe:
                            deduped[(maybe.resource_type, maybe.index_key)] = maybe
        records = list(deduped.values())
        self.replace_entities(records)
        return len(records)

    def _infer_resource_type(self, file_path: Path) -> str:
        parent = file_path.parent.name
        if parent not in {"en", "pt-BR", "fr-FR", "ru"}:
            return parent

        stem = file_path.stem
        if stem.startswith("5e-SRD-"):
            tail = stem[len("5e-SRD-") :].strip()
            if tail:
                return tail.replace("-", "_").lower()
        return parent

    def _record_from_obj(
        self, obj: dict[str, Any], resource_type: str, source_release: str
    ) -> EntityRecord | None:
        index_key = obj.get("index")
        name = obj.get("name")
        if not isinstance(index_key, str) or not isinstance(name, str):
            return None
        return EntityRecord(
            resource_type=resource_type,
            index_key=index_key,
            name=name,
            payload=obj,
            source_release=source_release,
        )

    def get_entity(self, resource_type: str, index_key: str) -> EntityRecord | None:
        row = self.conn.execute(
            """
            SELECT resource_type, index_key, name, payload_json, source_release
            FROM entities
            WHERE resource_type = ? AND index_key = ?
            """,
            (resource_type, index_key),
        ).fetchone()
        if row is None:
            return None
        return EntityRecord(
            resource_type=row["resource_type"],
            index_key=row["index_key"],
            name=row["name"],
            payload=json.loads(row["payload_json"]),
            source_release=row["source_release"],
        )

    def search_by_name(
        self, resource_type: str, query: str, limit: int = 5
    ) -> list[EntityRecord]:
        rows = self.conn.execute(
            """
            SELECT resource_type, index_key, name, payload_json, source_release
            FROM entities
            WHERE resource_type = ? AND lower(name) LIKE lower(?)
            ORDER BY name ASC
            LIMIT ?
            """,
            (resource_type, f"%{query}%", limit),
        ).fetchall()
        return [
            EntityRecord(
                resource_type=row["resource_type"],
                index_key=row["index_key"],
                name=row["name"],
                payload=json.loads(row["payload_json"]),
                source_release=row["source_release"],
            )
            for row in rows
        ]

    def get_spell(self, index_key: str) -> EntityRecord | None:
        return self.get_entity("spells", index_key)

    def get_monster(self, index_key: str) -> EntityRecord | None:
        return self.get_entity("monsters", index_key)
