"""
Dataset Statistics Calculator - Computes comprehensive statistics for datasets.

This module analyzes datasets to provide statistical insights into chunk
distribution, language coverage, AST symbol distribution, and quality metrics.
These statistics are essential for dataset quality assessment, balancing,
and optimization.

ARCHITECTURE POSITION:
    - Analytics Layer: Statistical analysis of datasets
    - Quality Metrics: Calculates dataset quality indicators
    - Balance Assessment: Analyzes chunk distribution

KEY METRICS:
    1. Chunk type distribution (module, class, function, documentation)
    2. Language distribution (Python, Markdown, JSON, etc.)
    3. AST symbol distribution (what types of AST nodes are present)
    4. Docstring coverage (percentage of chunks with docstrings)
    5. Average code length (character count per chunk)
"""    

from collections import Counter, defaultdict
from typing import Iterable, Dict

from ..chunking.chunk_schema import CodeChunk


def compute_dataset_stats(chunks: Iterable[CodeChunk]) -> Dict:
    chunks = list(chunks)

    total = len(chunks)

    by_type = Counter(c.chunk_type for c in chunks)
    by_language = Counter(c.language for c in chunks)

    ast_symbols = Counter(
        c.ast.symbol_type for c in chunks if c.ast and c.ast.symbol_type
    )

    docstring_coverage = sum(
        1 for c in chunks if c.ast and c.ast.docstring
    )

    avg_code_length = (
        sum(len(c.code) for c in chunks) / total
        if total else 0
    )

    return {
        "total_chunks": total,
        "chunk_type_distribution": dict(by_type),
        "language_distribution": dict(by_language),
        "ast_symbol_distribution": dict(ast_symbols),
        "docstring_coverage_ratio": (
            docstring_coverage / total if total else 0
        ),
        "average_code_length_chars": round(avg_code_length, 2),
    }
