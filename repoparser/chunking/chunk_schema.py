"""
chunk_schema.py - UPDATED with enhanced hierarchy
"""

from typing import Dict, List, Optional, Literal, Union
from dataclasses import dataclass, field


# ✅ EXPANDED ChunkType to support ALL file types
ChunkType = Literal[
    "module",        # Python module
    "class",         # Python class  
    "function",      # Python function
    "method",        # Python method
    "context",       # General context
    "documentation", # Markdown/RST docs
    "configuration", # Config files (JSON, YAML, TOML)
    "notebook",      # Jupyter notebook
    "script",        # Shell scripts
    "dockerfile",    # Docker files
    "typescript",    # TypeScript files
    "javascript",    # JavaScript files
    "text",          # Plain text
    "imports",       # Import statements
    "unknown"        # Unknown file type
]

# For AST symbol types
ASTSymbolType = Literal[
    "module", "class", "function", "method", "context",
    "documentation", "configuration", "notebook", "script",
    "dockerfile", "typescript", "javascript", "text", 
    "imports",
    "unknown"
]


# @dataclass  
# class ChunkHierarchy:
#     """Enhanced hierarchical relationship metadata"""
#     parent_id: Optional[str] = None
#     children_ids: List[str] = field(default_factory=list)
#     depth: int = 0
#     is_primary: bool = True
#     is_extracted: bool = False
#     lineage: List[str] = field(default_factory=list)  # Path from root
#     sibling_index: int = 0  # Position among siblings

@dataclass  
class ChunkHierarchy:
    """Enhanced hierarchical relationship metadata"""
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    depth: int = 0
    is_primary: bool = True
    is_extracted: bool = False
    lineage: List[str] = field(default_factory=list)  # Path from root
    sibling_index: int = 0  # Position among siblings
    
    # Optional: Add methods for type-safe operations
    def add_child(self, child_id: str) -> None:
        """Type-safe method to add child"""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)
    
    def remove_child(self, child_id: str) -> None:
        """Type-safe method to remove child"""
        if child_id in self.children_ids:
            self.children_ids.remove(child_id)
    
    def set_parent(self, parent_id: Optional[str]) -> None:
        """Type-safe method to set parent"""
        self.parent_id = parent_id
    
    def increment_depth(self) -> None:
        """Increment depth by 1"""
        self.depth += 1


@dataclass
class ChunkAST:
    symbol_type: Optional[ASTSymbolType] = None
    name: Optional[str] = None
    parent: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    node_type: Optional[str] = None  # Original AST node type


@dataclass
class ChunkSpan:
    start_byte: Optional[int] = None
    end_byte: Optional[int] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    char_count: Optional[int] = None  # Character count for quick reference



@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    language: str
    chunk_type: ChunkType  # ✅ Now accepts ALL types
    code: str
    ast: ChunkAST
    span: ChunkSpan
    metadata: Dict = field(default_factory=dict)
    hierarchy: ChunkHierarchy = field(default_factory=ChunkHierarchy)

