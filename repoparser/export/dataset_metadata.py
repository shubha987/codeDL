"""
Dataset Metadata Generator - Creates metadata files for datasets.

This module generates standardized metadata files for datasets, capturing
essential information about the dataset's composition, creation context,
and chunking strategy. This metadata is crucial for dataset tracking,
versioning, and reproducibility.

ARCHITECTURE POSITION:
    - Metadata Layer: Creates standardized dataset metadata
    - Provenance Tracker: Records dataset creation context
    - Versioning Support: Enables dataset version management

KEY FEATURES:
    1. Standardized metadata format across all datasets
    2. Automatic collection of dataset statistics
    3. Chunking strategy documentation
    4. Python environment context
    5. Creation timestamp for reproducibility
"""    

import json
from pathlib import Path
from datetime import datetime
from typing import Iterable
import sys

from ..chunking.chunk_schema import CodeChunk


def write_dataset_metadata(
    chunks: Iterable[CodeChunk],
    output_path: Path,
    dataset_name: str,
    dataset_version: str,
):
    chunks = list(chunks)

    metadata = {
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "chunking_strategy": "pure_ast + tree_sitter_spans",
        "languages": sorted({c.language for c in chunks}),
        "python_version": sys.version.split()[0],
        "total_files": len({c.file_path for c in chunks}),
        "total_chunks": len(chunks),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )
