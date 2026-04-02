"""
Tree-sitter based syntactic chunker - Span enrichment and fallback parser.

This module provides byte-level precise chunking using Tree-sitter, which
serves as a structural fallback and span enrichment layer. Tree-sitter is
language-aware and robust against malformed code, making it ideal for
extracting exact byte spans and as a backup parser.

ARCHITECTURE POSITION:
    - Enrichment Layer: Provides byte-level precision
    - Fallback Parser: Robust parsing for malformed code
    - Span Authority: Source of truth for byte positions

KEY FEATURES:
    1. Byte-level accurate spans (exact source positions)
    2. Language-aware parsing (supports multiple languages)
    3. Robust against syntax errors
    4. Extracts structural nodes even from partial code

FLOW:
    File → Tree-sitter parser → Structural nodes → Spans for enrichment

USAGE:
    from ts_chunker import extract_ts_chunks
    chunks = extract_ts_chunks(Path("file.py"))
    
NOTE: Tree-sitter chunks are NOT primary - they enrich AST chunks with
      precise byte spans and serve as fallback for syntax errors.
"""

from pathlib import Path
from typing import List, Optional, Literal, Dict, Tuple

from tree_sitter import Parser, Language, Node
import tree_sitter_python as tspython

from .chunk_schema import CodeChunk, ChunkAST, ChunkSpan, ChunkHierarchy, ChunkType

# ----------------------------
# Types
# ----------------------------

TS_TO_CHUNK_TYPE: Dict[str, ChunkType] = {
    "module": "module",
    "class_definition": "class",
    "function_definition": "function",
    "async_function_definition": "function",
    "import_statement": "imports",
    "import_from_statement": "imports",
}

MAX_TS_DEPTH = 3  # module → imports → class/function → method


# ----------------------------
# Helpers
# ----------------------------

def _safe_decode(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="ignore")


def _get_node_name(node: Node) -> Optional[str]:
    """
    Extract identifier name for class / function nodes.
    """
    for child in node.children:
        if child.type == "identifier":
            text = child.text
            if isinstance(text, (bytes, bytearray)):
                return _safe_decode(text)
    return None


# ----------------------------
# Public API
# ----------------------------

def extract_ts_chunks(file_path: Path) -> List[CodeChunk]:
    source_bytes = file_path.read_bytes()

    language = Language(tspython.language())
    parser = Parser(language=language)

    tree = parser.parse(source_bytes)
    root = tree.root_node

    chunks: List[CodeChunk] = []

    def walk(node: Node, depth: int = 0, parent_node: Optional[Node] = None) -> None:
        if depth > MAX_TS_DEPTH:
            return

        node_type = node.type

        if node_type in TS_TO_CHUNK_TYPE:
            code_bytes = source_bytes[node.start_byte : node.end_byte]
            code = _safe_decode(code_bytes)
            
            chunk_type = TS_TO_CHUNK_TYPE[node_type]
            name = _get_node_name(node)
            
            # For imports, use the full import as name
            if chunk_type == "imports":
                name = code.strip()
            
            # Create chunk with byte-level precision
            chunks.append(
                CodeChunk(
                    chunk_id=f"ts_{node.start_byte}_{node.end_byte}",
                    file_path=str(file_path),
                    language="python",
                    chunk_type=chunk_type,
                    code=code,
                    ast=ChunkAST(
                        symbol_type=None,  # TS doesn't provide semantic types
                        name=name,
                        parent=None,  # Parent relationships from AST
                        docstring=None,
                        decorators=[],
                        imports=[],
                        node_type=node_type,
                    ),
                    span=ChunkSpan(
                        start_byte=node.start_byte,
                        end_byte=node.end_byte,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        char_count=len(code),
                    ),
                    hierarchy=ChunkHierarchy(
                        is_primary=False,  # Tree-sitter chunks are for span enrichment only
                        is_extracted=True,
                        depth=depth,
                        parent_id=None,  # Parent relationships from AST
                    ),
                    metadata={
                        "byte_span": {
                            "start": node.start_byte,
                            "end": node.end_byte,
                        },
                        "tree_sitter_node_type": node_type,
                        "is_exact_span": True,
                    },
                )
            )

        for child in node.children:
            walk(child, depth + 1, node)

    walk(root)
    return chunks