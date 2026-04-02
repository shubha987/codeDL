"""
Deterministic ID generation for code chunks.

This module provides deterministic hashing for chunk IDs, ensuring that
identical code chunks receive the same ID across runs. This is crucial for:
1. Version tracking and change detection
2. Cache consistency
3. Reproducible datasets
4. Efficient deduplication

ID GENERATION STRATEGY:
    Hash = SHA256(file_path + chunk_type + name + parent + 
                  start_line + end_line + code + byte_spans)
    
    Result: prefix_hash (e.g., "primary_5c442008")

KEY PROPERTIES:
    1. Deterministic: Same input → same ID
    2. Content-aware: Code changes → ID changes
    3. Position-aware: Line/byte changes → ID changes
    4. Hierarchical: Parent relationships affect ID

USE CASE:
    Ensures that during RAG operations, identical code chunks are
    recognized as the same entity, improving retrieval accuracy.

EXAMPLE:
    deterministic_chunk_id(
        file_path="src/module.py",
        chunk_type="class",
        name="MyClass",
        parent="module",
        start_line=10,
        end_line=50,
        code="class MyClass: ...",
        start_byte=100,
        end_byte=500
    )
    → "primary_a1b2c3d4"
"""

import hashlib
from typing import Optional

def deterministic_chunk_id(
    *,
    file_path: str,
    chunk_type: str,
    name: Optional[str],
    parent: Optional[str],
    start_line: Optional[int],
    end_line: Optional[int],
    code: str,
    prefix: str = "primary",
    start_byte: Optional[int] = None,
    end_byte: Optional[int] = None,
) -> str:
    """
    Generate deterministic chunk ID that includes code content.
    
    Args:
        file_path: Path to source file
        chunk_type: Type of chunk (function, class, method, etc.)
        name: Name of the symbol
        parent: Parent symbol name
        start_line: Starting line number
        end_line: Ending line number
        code: Actual code content
        prefix: ID prefix (primary/secondary)
        start_byte: Starting byte offset
        end_byte: Ending byte offset
    
    Returns:
        Deterministic chunk ID
    """
    # Create a payload that uniquely identifies this chunk
    payload = f"""
    {file_path}
    {chunk_type}
    {name}
    {parent}
    {start_line}
    {end_line}
    {start_byte}
    {end_byte}
    {code}
    """.strip()
    
    # Generate hash and use first 8 chars for readability
    hash_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{hash_digest}"
