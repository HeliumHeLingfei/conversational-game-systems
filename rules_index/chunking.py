import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


@dataclass(frozen=True)
class RuleChunk:
    chunk_id: str
    source_system: str
    file: str
    heading_path: str
    entity_type: str
    entity_name: str
    body: str
    commit_or_release: str


def _normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _entity_type_from_path(path: Path) -> str:
    lowered = "/".join(path.parts).lower()
    if "spell" in lowered:
        return "spell"
    if "monster" in lowered:
        return "monster"
    if "class" in lowered:
        return "class"
    if "equipment" in lowered or "item" in lowered:
        return "equipment"
    return "rule_section"


def _entity_name(path: Path, heading_path: str, entity_type: str) -> str:
    if entity_type in {"spell", "monster", "class", "equipment"} and heading_path:
        return heading_path.split(" > ")[-1]
    return path.stem.replace("-", " ").replace("_", " ").strip()


def chunk_markdown_file(
    source_file: Path,
    source_root: Path,
    source_system: str,
    commit_or_release: str,
) -> list[RuleChunk]:
    lines = source_file.read_text(encoding="utf-8").splitlines()
    rel_file = source_file.relative_to(source_root).as_posix()
    entity_type = _entity_type_from_path(Path(rel_file))

    heading_stack: list[str] = []
    current_body: list[str] = []
    chunks: list[RuleChunk] = []
    ordinal = 0

    def flush_chunk() -> None:
        nonlocal ordinal
        body = "\n".join(current_body).strip()
        if not body:
            return
        heading_path = " > ".join(heading_stack) if heading_stack else "__root__"
        digest = hashlib.sha256(
            f"{rel_file}|{heading_path}|{ordinal}".encode("utf-8")
        ).hexdigest()
        chunks.append(
            RuleChunk(
                chunk_id=digest,
                source_system=source_system,
                file=rel_file,
                heading_path=heading_path,
                entity_type=entity_type,
                entity_name=_entity_name(Path(rel_file), heading_path, entity_type),
                body=body,
                commit_or_release=commit_or_release,
            )
        )
        ordinal += 1

    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            flush_chunk()
            current_body = []
            level = len(match.group(1))
            heading = _normalize_heading(match.group(2))
            while len(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(heading)
            continue
        current_body.append(line)

    flush_chunk()
    return chunks


def ingest_markdown_tree(
    source_root: Path,
    source_system: str,
    commit_or_release: str,
) -> list[RuleChunk]:
    chunks: list[RuleChunk] = []
    for file_path in sorted(source_root.rglob("*.md")):
        if file_path.is_file():
            chunks.extend(
                chunk_markdown_file(
                    source_file=file_path,
                    source_root=source_root,
                    source_system=source_system,
                    commit_or_release=commit_or_release,
                )
            )
    return chunks


def write_chunks_jsonl(chunks: list[RuleChunk], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def write_manifest(
    chunks: list[RuleChunk],
    source_root: Path,
    source_system: str,
    commit_or_release: str,
    output_path: Path,
) -> dict[str, Any]:
    files = sorted({chunk.file for chunk in chunks})
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.chunk_id.encode("utf-8"))

    manifest: dict[str, Any] = {
        "source_system": source_system,
        "commit_or_release": commit_or_release,
        "source_root": str(source_root),
        "generated_at": datetime.now(UTC).isoformat(),
        "file_count": len(files),
        "chunk_count": len(chunks),
        "files": files,
        "chunk_index_sha256": digest.hexdigest(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
