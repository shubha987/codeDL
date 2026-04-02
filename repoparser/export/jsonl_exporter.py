"""
Basic JSONL Exporter - Clean export for local codebase chunks.

This module provides a clean, simple JSONL export for LOCAL CODEBASE files.
It focuses on basic chunk serialization without repository metadata, making
it ideal for local examples, tests, and simpler datasets.

ARCHITECTURE POSITION:
    - Basic Export Layer: Simple serialization for local files
    - Text Sanitizer: Cleans binary characters from text
    - Language Inferrer: Detects language from file extensions

KEY FEATURES:
    1. Clean JSONL export format
    2. Text sanitization (removes null bytes)
    3. Language inference from file extensions
    4. Optional statistics printing
    5. Handles both CodeChunk objects and dictionaries

DIFFERENCE FROM ENHANCED EXPORTER:
    - No repository metadata
    - No cross-file context
    - Simple statistics only
    - Designed for local/small-scale datasets

OUTPUT STRUCTURE:
    {
        "chunk_id": "...",
        "file_path": "...",
        "language": "python/markdown/text/etc",
        "chunk_type": "...",
        "code": "...",
        "ast": {...},
        "span": {...},
        "hierarchy": {...},
        "metadata": {}  # Simple, local-only metadata
    }

USAGE:
    export_chunks_jsonl(chunks, Path("output/chunks.jsonl"), print_stats=True)
"""

import json
from pathlib import Path
from typing import Iterable, Optional

from ..chunking.chunk_schema import CodeChunk
from ..analysis.dataset_stats import compute_dataset_stats


def _sanitize_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return text.replace("\x00", "")


def _infer_language(file_path: str, existing: Optional[str]) -> str:
    if existing:
        return existing
    suffix = Path(file_path).suffix.lower()
    return {
        ".py": "python",
        ".md": "markdown",
        ".txt": "text",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")


def export_chunks_jsonl(
    chunks: Iterable[CodeChunk],
    output_path: Path,
    print_stats: bool = False,
) -> None:
    chunks_list = list(chunks)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for chunk in chunks_list:
            if isinstance(chunk, dict):
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                continue
            code_text = _sanitize_text(chunk.code)

            chunk_dict = {
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.file_path,
                "language": _infer_language(chunk.file_path, chunk.language),
                "chunk_type": chunk.chunk_type,
                "code": code_text,
                "ast": (
                    {
                        "symbol_type": chunk.ast.symbol_type,
                        "name": chunk.ast.name,
                        "parent": chunk.ast.parent,
                        "docstring": _sanitize_text(chunk.ast.docstring),
                        "decorators": chunk.ast.decorators,
                        "imports": chunk.ast.imports,
                    }
                    if chunk.ast
                    else None
                ),
                "span": (
                    {
                        "start_byte": chunk.span.start_byte,
                        "end_byte": chunk.span.end_byte,
                        "start_line": chunk.span.start_line,
                        "end_line": chunk.span.end_line,
                    }
                    if chunk.span
                    else None
                ),
                "metadata": chunk.metadata,
                "hierarchy": (
                    {
                        "parent_id": chunk.hierarchy.parent_id,
                        "children_ids": chunk.hierarchy.children_ids,
                        "depth": chunk.hierarchy.depth,
                        "is_primary": chunk.hierarchy.is_primary,
                        "is_extracted": chunk.hierarchy.is_extracted,
                    }
                    if getattr(chunk, "hierarchy", None)
                    else None
                ),
            }

            f.write(json.dumps(chunk_dict, ensure_ascii=False) + "\n")

    if print_stats:
        code_chunks = [c for c in chunks_list if isinstance(c, CodeChunk)]
        stats = compute_dataset_stats(code_chunks)

        print("\n=== Dataset Statistics ===")
        for k, v in stats.items():
            print(f"{k}: {v}")

# Example usage
if __name__ == "__main__":
    from pathlib import Path
    from ..chunking.ast_chunker import extract_ast_chunks

    example_file = Path("path/to/example.py")
    chunks = extract_ast_chunks(example_file)
    export_chunks_jsonl(chunks, Path("output/example_chunks.jsonl"), print_stats=True)     
