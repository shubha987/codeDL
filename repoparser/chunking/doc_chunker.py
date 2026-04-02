from __future__ import annotations

import hashlib
import re
from typing import List, Dict, Optional
from .chunk_schema import CodeChunk, ChunkAST, ChunkSpan, ChunkHierarchy

def _hash_id(text: str, prefix: str) -> str:
    """
    Generate deterministic ID using SHA256 (standardized).
    
    Previously used SHA1, now standardized to SHA256 for consistency
    with repo_chunker.py and id_utils.py.
    """
    # CHANGED: sha1 → sha256
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def _is_actual_code(text: str) -> bool:
    """
    Check if text inside a fenced block is actual executable code
    or just formatted text.
    """
    text = text.strip()
    
    # Common patterns that indicate formatted text, not code
    formatted_text_patterns = [
        # Lines with many = or - characters (dividers)
        r'^=+\s*[A-Za-z\s]+\s*=+$',
        r'^-+\s*[A-Za-z\s]+\s*-+$',
        # Lines that look like headers/separators
        r'^[=_-]{20,}$',
        # Contains natural language sentences
        r'\b(the|and|that|this|with|for|are|is|was|were|have|has|had)\b',
        r'[.!?]\s+[A-Z]',  # Sentence boundaries
        # Message-like patterns
        r'^\s*(Human|AI|Tool|System|User|Assistant)\s+(Message|Response|Input|Output)?\s*[:=-]',
        r'^\s*[A-Z][a-z]+\s*:',  # "Reasoning:", "Acting:", etc.
    ]
    
    # Check if it looks like formatted text
    lines = text.split('\n')
    formatted_line_count = 0
    code_line_count = 0
    
    # Patterns that indicate actual code
    code_patterns = [
        r'^\s*(def|class|import|from|async|await|return|if|for|while|try|except|with)\b',
        r'^\s*@\w+',
        r'^\s*\w+\s*=\s*.+',
        r'^\s*\w+\(.+\)',
        r'^\s*print\(.+\)',
        r'^\s*\{.*\}',  # JSON/dict
        r'^\s*\[.*\]',  # List
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for formatted text patterns
        is_formatted = any(re.search(pattern, line, re.IGNORECASE) for pattern in formatted_text_patterns)
        
        # Check for code patterns
        is_code = any(re.search(pattern, line) for pattern in code_patterns)
        
        if is_formatted:
            formatted_line_count += 1
        if is_code:
            code_line_count += 1
    
    # If it has many formatted text lines and few/no code lines, it's not actual code
    if formatted_line_count > 1 and code_line_count == 0:
        return False
    
    # Default to treating fenced blocks as code (original behavior)
    return True


def _looks_like_code_block(lines: List[str]) -> bool:
    """
    Heuristic to recover code blocks when Markdown fences are missing
    (common after HTML → MD conversion).
    """
    if not lines:
        return False
    
    # Join lines and check for minimum length
    joined = "\n".join(lines)
    text = joined.strip()
    
    # Too short? Probably not code
    if len(text) < 50:
        return False
    
    # Check for code patterns
    code_patterns = [
        # Python keywords at line start
        r'^\s*(def\s+\w+\s*\(|class\s+\w+|import\s+\w+|from\s+\w+\s+import)',
        # Function calls or assignments
        r'^\s*\w+\s*=\s*.+|^\s*\w+\s*\(.+\)',
        # Control structures
        r'^\s*(if|for|while|with|try|except|finally|async|await)\s+',
        # Decorators
        r'^\s*@\w+',
        # Return statements
        r'^\s*return\b',
        # Print statements
        r'^\s*print\(',
        # Indented blocks (common in Python)
        r'^\s{4,}\S',
    ]
    
    # Check for prose indicators (if these are present, it's likely text)
    prose_indicators = [
        # Common English words in prose
        r'\b(the|and|that|this|with|for|are|is|was|were|have|has|had)\b',
        # Sentence endings followed by capital
        r'[.!?]\s+[A-Z]',
        # Articles
        r'\b(a|an|the)\s+\w+',
    ]
    
    lines_list = text.split('\n')
    code_line_count = 0
    prose_line_count = 0
    
    for line in lines_list:
        line = line.strip()
        if not line:
            continue
            
        # Check if line looks like code
        is_code = any(re.search(pattern, line) for pattern in code_patterns)
        
        # Check if line looks like prose (but only if it's not empty/short)
        is_prose = len(line) > 20 and any(re.search(pattern, line, re.IGNORECASE) for pattern in prose_indicators)
        
        if is_code:
            code_line_count += 1
        if is_prose:
            prose_line_count += 1
    
    # Need strong evidence for code
    total_non_empty_lines = len([l for l in lines_list if l.strip()])
    
    # If more than 2 lines look like code and not many look like prose
    if code_line_count >= 2 and prose_line_count <= code_line_count // 2:
        return True
    
    # Special case: single strong code line in short text
    if total_non_empty_lines <= 3 and code_line_count >= 1 and prose_line_count == 0:
        return True
    
    # Check for specific code-only patterns
    code_only_patterns = [
        r'^\s*from langchain\.',  
        r'^\s*import langchain',  
        r'^\s*@tool\b',  # Decorator
        r'^\s*agent = create_agent\(', 
        r'^\s*result = agent\.invoke\(', 
    ]
    
    if any(re.search(pattern, text) for pattern in code_only_patterns):
        return True
    
    return False


def _looks_like_executable_code(text: str) -> bool:
    """Check if code looks like it could be executed"""
    # First check if it's actually code (not formatted text)
    if not _is_actual_code(text):
        return False
    
    # Check for actual Python syntax patterns
    patterns = [
        r'\bdef\s+\w+\s*\([^)]*\)\s*:',
        r'\bclass\s+\w+\s*\(?[^:]*\)?\s*:',
        r'^\s*from\s+\w+\s+import\s+\w+',
        r'^\s*import\s+\w+',
        r'\breturn\b',
        r'\bprint\(',
        r'^\s*\w+\s*=\s*[^=\n]+$',  # Variable assignment
    ]
    
    lines = text.split('\n')
    executable_lines = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('"""'):
            continue
        if any(re.search(pattern, line) for pattern in patterns):
            executable_lines += 1
    
    # Need at least 2 executable lines or 1 strong executable line
    return executable_lines >= 2 or (
        executable_lines >= 1 and len([l for l in lines if l.strip()]) <= 3
    )


def chunk_document(
    raw_text: str,
    source_name: str,
    source_url: Optional[str] = None,
) -> List[Dict]:
    """
    Chunk documentation text containing headings, prose, and code examples.

    Design goals:
    - Preserve document hierarchy
    - Separate prose vs code
    - Recover code even if Markdown fences are lost
    - Deterministic chunk IDs
    """

    chunks: List[Dict] = []

    heading_stack: List[str] = []
    current_heading: Optional[str] = None
    current_heading_level: Optional[int] = None

    buffer: List[str] = []

    code_block = False
    code_language: Optional[str] = None
    code_lines: List[str] = []

    lines = raw_text.splitlines()
    chunk_index = 0
    line_cursor = 0

    def heading_path() -> Optional[str]:
        return " > ".join(heading_stack) if heading_stack else None

    def flush_text(start_line: int, end_line: int):
        nonlocal buffer, chunk_index
        if not buffer:
            return

        text = "\n".join(buffer).strip()
        buffer = []

        if not text:
            return

        lines_local = text.splitlines()

        # 🔹 Recover unfenced code blocks - use stricter heuristic
        # Only mark as code if it's very clearly code
        if _looks_like_code_block(lines_local) and len(text) > 30:
            # Double-check: make sure it doesn't look like prose
            looks_like_prose = any(word in text.lower() for word in 
                                  ['the', 'and', 'that', 'this', 'with', 'for', 'are', 'is', 'was'])
            
            if not looks_like_prose:
                chunks.append(
                    {
                        "chunk_id": _hash_id(text, "doc_code"),
                        "source": "documentation",
                        "source_name": source_name,
                        "source_url": source_url,
                        "language": "python",
                        "chunk_type": "code",
                        "content": text,
                        "chunk_index": chunk_index,
                        "metadata": {
                            "heading": current_heading,
                            "heading_level": current_heading_level,
                            "heading_path": heading_path(),
                            "line_start": start_line,
                            "line_end": end_line,
                            "inferred_block": True,
                        },
                    }
                )
                chunk_index += 1
                return
        
        # Default to text
        chunks.append(
            {
                "chunk_id": _hash_id(text, "doc_text"),
                "source": "documentation",
                "source_name": source_name,
                "source_url": source_url,
                "language": "markdown",
                "chunk_type": "text",
                "content": text,
                "chunk_index": chunk_index,
                "metadata": {
                    "heading": current_heading,
                    "heading_level": current_heading_level,
                    "heading_path": heading_path(),
                    "line_start": start_line,
                    "line_end": end_line,
                },
            }
        )
        chunk_index += 1

    def flush_code(start_line: int, end_line: int):
        nonlocal code_lines, code_language, chunk_index
        if not code_lines:
            return

        code = "\n".join(code_lines)
        code_lines = []

        # Check if this is actually code or just formatted text
        is_actual_code = _is_actual_code(code)
        
        if is_actual_code:
            chunks.append(
                {
                    "chunk_id": _hash_id(code, "doc_code"),
                    "source": "documentation",
                    "source_name": source_name,
                    "source_url": source_url,
                    "language": code_language or "unknown",
                    "chunk_type": "code",
                    "content": code,
                    "chunk_index": chunk_index,
                    "metadata": {
                        "heading": current_heading,
                        "heading_level": current_heading_level,
                        "heading_path": heading_path(),
                        "fenced_block": True,
                        "line_start": start_line,
                        "line_end": end_line,
                        "looks_executable": _looks_like_executable_code(code),
                    },
                }
            )
        else:
            # It's formatted text, not actual code
            chunks.append(
                {
                    "chunk_id": _hash_id(code, "doc_text"),
                    "source": "documentation",
                    "source_name": source_name,
                    "source_url": source_url,
                    "language": "markdown",
                    "chunk_type": "text",
                    "content": code,
                    "chunk_index": chunk_index,
                    "metadata": {
                        "heading": current_heading,
                        "heading_level": current_heading_level,
                        "heading_path": heading_path(),
                        "line_start": start_line,
                        "line_end": end_line,
                        "was_fenced_block": True,  # Note: was in ``` but isn't code
                    },
                }
            )

        chunk_index += 1
        code_language = None

    buffer_start_line = 0
    code_start_line = 0

    for i, line in enumerate(lines):
        line_cursor = i + 1

        # ---- Heading detection ----
        m = re.match(r"^(#{2,6})\s+(.*)", line)
        if not code_block and m:
            flush_text(buffer_start_line, line_cursor - 1)

            level = len(m.group(1))
            title = m.group(2).strip()

            # Maintain heading stack
            heading_stack[:] = heading_stack[: level - 2]
            heading_stack.append(title)

            current_heading = title
            current_heading_level = level
            buffer_start_line = line_cursor
            continue

        # ---- Code fence detection ----
        if line.strip().startswith("```"):
            if not code_block:
                flush_text(buffer_start_line, line_cursor - 1)
                code_block = True
                code_language = line.strip().replace("```", "").strip() or None
                code_start_line = line_cursor + 1
            else:
                code_block = False
                flush_code(code_start_line, line_cursor - 1)
                buffer_start_line = line_cursor + 1
            continue

        if code_block:
            code_lines.append(line)
        else:
            if not buffer:
                buffer_start_line = line_cursor
            buffer.append(line)

    flush_text(buffer_start_line, line_cursor)
    flush_code(code_start_line, line_cursor)

    return chunks


def wrap_doc_chunks(doc_chunks: List[dict]) -> List[CodeChunk]:
    """
    Adapter: convert doc_chunker output (dict)
    into CodeChunk(documentation).
    Does NOT affect core doc_chunker parsing logic.
    """
    wrapped: List[CodeChunk] = []

    for d in doc_chunks:
        wrapped.append(
            CodeChunk(
                chunk_id=d["chunk_id"],
                file_path=d["source_name"],
                language=d.get("language", "markdown"),
                chunk_type="documentation",
                code=d["content"],
                ast=ChunkAST(
                    symbol_type="documentation",
                    name=d.get("metadata", {}).get("heading"),
                    parent=d.get("metadata", {}).get("heading_path"),
                ),
                span=ChunkSpan(
                    start_line=d.get("metadata", {}).get("line_start"),
                    end_line=d.get("metadata", {}).get("line_end"),
                ),
                hierarchy=ChunkHierarchy(
                    is_primary=True,
                    is_extracted=True,
                ),
                metadata=d.get("metadata", {}),
            )
        )

    return wrapped