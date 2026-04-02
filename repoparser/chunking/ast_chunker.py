"""
AST-based semantic code chunker - Primary source of truth for code structure.

This module implements the core AST-based chunking strategy that forms the 
authority layer of our hybrid chunking pipeline. It uses Python's built-in 
AST parser to extract semantic chunks (modules, classes, functions, methods) 
while preserving hierarchical relationships.

ARCHITECTURE POSITION:
    - Authority Layer: Source of truth for semantic structure
    - Primary Chunker: Generates all primary chunks
    - Hierarchy Builder: Establishes parent-child relationships

KEY FEATURES:
    1. AST-first parsing for semantic accuracy
    2. Hierarchical chunk generation with depth tracking
    3. Byte-level span calculation for precise positioning
    4. Import and decorator extraction per node
    5. Deterministic chunk ID generation

FLOW:
    File → Python AST → ASTChunker visitor → Semantic chunks with hierarchy

USAGE:
    from ast_chunker import extract_ast_chunks
    chunks = extract_ast_chunks(Path("file.py"))
"""

import ast
from pathlib import Path
from typing import List, Optional, Union, Dict, Tuple
import hashlib

from ..utils.id_utils import deterministic_chunk_id
from .chunk_schema import CodeChunk, ChunkAST, ChunkSpan, ChunkHierarchy, ASTSymbolType, ChunkType

DocNode = Union[
    ast.Module,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
]


class ASTChunker(ast.NodeVisitor):
    def __init__(self, source: str, file_path: str):
        self.source = source
        self.file_path = file_path
        self.source_bytes = source.encode('utf-8')
        self.chunks: List[CodeChunk] = []
        self.tree = ast.parse(source)
        
        # Track hierarchy
        self.current_class: Optional[str] = None
        self.imports_list: List[str] = []
        
        # For hierarchy tracking
        self.parent_stack: List[CodeChunk] = []
        self.sibling_counters: Dict[str, int] = {}
        
        # Attach parents to nodes
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                setattr(child, "parent", node)

    # ---------------- utilities ----------------

    def _get_code(self, node: ast.AST) -> str:
        code = ast.get_source_segment(self.source, node)
        return code.strip() if code else ""

    def _get_byte_span(self, start_line: int, end_line: int) -> Tuple[int, int]:
        """Convert line numbers to byte positions"""
        lines = self.source.split('\n')
        
        # Calculate start byte
        start_byte = sum(len(line.encode()) + 1 for line in lines[:start_line-1])
        
        # Calculate end byte (up to end_line)
        end_byte = sum(len(line.encode()) + 1 for line in lines[:end_line])
        
        return start_byte, end_byte

    def _extract_node_imports(self, node: ast.AST) -> List[str]:
        """Extract imports specific to this node (not all module imports)"""
        imports: List[str] = []
        
        # Walk through this node's body
        for child in ast.walk(node):
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                try:
                    imports.append(ast.unparse(child))
                except Exception:
                    imports.append(str(child))
        return imports

    def _extract_decorators(self, node: ast.AST) -> List[str]:
        decorators: List[str] = []
        if hasattr(node, "decorator_list"):
            for d in node.decorator_list:  # type: ignore[attr-defined]
                try:
                    decorators.append(ast.unparse(d))
                except Exception:
                    decorators.append(str(d))
        return decorators

    # ---------------- chunk creation ----------------

    def _create_chunk(
        self,
        node: DocNode,
        chunk_type: ChunkType,
        name: str,
        parent: Optional[str] = None,
        parent_chunk: Optional[CodeChunk] = None,
    ) -> CodeChunk:
        code = self._get_code(node)
        
        # Get line numbers
        start_line = getattr(node, "lineno", None)
        end_line = getattr(node, "end_lineno", None)
        
        # Calculate byte span
        start_byte, end_byte = None, None
        if start_line and end_line:
            start_byte, end_byte = self._get_byte_span(start_line, end_line)

        # Determine parent if not provided
        if parent is None and chunk_type == "method":
            parent = self.current_class

        decorators: List[str] = []
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = self._extract_decorators(node)

        # Get imports specific to this node (not all module imports)
        node_imports = self._extract_node_imports(node)

        # Get docstring only for nodes that can have one
        docstring: Optional[str] = None
        if hasattr(node, 'body'):
            docstring = ast.get_docstring(node)

        # Determine hierarchy depth
        depth = 0
        lineage: List[str] = []
        sibling_index = 0
        
        if parent_chunk:
            depth = parent_chunk.hierarchy.depth + 1
            lineage = parent_chunk.hierarchy.lineage.copy()
            lineage.append(parent_chunk.chunk_id)
            
            # Update sibling counter
            parent_key = parent_chunk.chunk_id
            self.sibling_counters[parent_key] = self.sibling_counters.get(parent_key, 0) + 1
            sibling_index = self.sibling_counters[parent_key] - 1

        ast_info = ChunkAST(
            symbol_type=chunk_type,
            name=name,
            parent=parent,
            docstring=docstring,
            decorators=decorators,
            imports=node_imports,
        )

        span = ChunkSpan(
            start_byte=start_byte,
            end_byte=end_byte,
            start_line=start_line,
            end_line=end_line,
        )

        # Generate chunk ID
        chunk_id = deterministic_chunk_id(
            file_path=self.file_path,
            chunk_type=chunk_type,
            name=name,
            parent=parent,
            start_line=start_line,
            end_line=end_line,
            code=code,
        )

        chunk = CodeChunk(
            chunk_id=chunk_id,
            file_path=self.file_path,
            language="python",
            chunk_type=chunk_type,
            code=code,
            ast=ast_info,
            span=span,
            hierarchy=ChunkHierarchy(
                parent_id=parent_chunk.chunk_id if parent_chunk else None,
                children_ids=[],
                depth=depth,
                is_primary=True,
                is_extracted=False,
                lineage=lineage,
                sibling_index=sibling_index,
            ),
        )

        # Add to parent's children if parent exists
        if parent_chunk:
            parent_chunk.hierarchy.children_ids.append(chunk_id)

        self.chunks.append(chunk)
        return chunk

    def _create_module_chunk(self) -> CodeChunk:
        """Create module chunk with all imports"""
        module_name = Path(self.file_path).stem
        start_line = 1
        end_line = len(self.source.split('\n'))
        start_byte, end_byte = self._get_byte_span(start_line, end_line)
        
        # Module code - entire file
        module_code = self.source
        
        # Extract ALL imports for module
        module_imports: List[str] = []
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    module_imports.append(ast.unparse(node))
                except Exception:
                    pass
        
        chunk_id = deterministic_chunk_id(
            file_path=self.file_path,
            chunk_type="module",
            name=module_name,
            parent=None,
            start_line=start_line,
            end_line=end_line,
            code=module_code,
        )
        
        ast_info = ChunkAST(
            symbol_type="module",
            name=module_name,
            parent=None,
            docstring=ast.get_docstring(self.tree),
            decorators=[],
            imports=module_imports,  # ALL imports in module
        )
        
        span = ChunkSpan(
            start_byte=start_byte,
            end_byte=end_byte,
            start_line=start_line,
            end_line=end_line,
        )
        
        chunk = CodeChunk(
            chunk_id=chunk_id,
            file_path=self.file_path,
            language="python",
            chunk_type="module",
            code=module_code,
            ast=ast_info,
            span=span,
            hierarchy=ChunkHierarchy(
                parent_id=None,
                children_ids=[],
                depth=0,
                is_primary=True,
                is_extracted=False,
                lineage=[],
                sibling_index=0,
            ),
        )
        
        self.chunks.append(chunk)
        return chunk

    # ---------------- visitors ----------------

    def visit_Import(self, node: ast.Import) -> None:
        try:
            self.imports_list.append(ast.unparse(node))
        except Exception:
            pass
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        try:
            self.imports_list.append(ast.unparse(node))
        except Exception:
            pass
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Create class chunk
        class_chunk = self._create_chunk(
            node, 
            "class", 
            node.name,
            parent="module",
            parent_chunk=self.parent_stack[-1] if self.parent_stack else None,
        )
        
        # Save current class context
        previous_class = self.current_class
        self.current_class = node.name
        
        # Push class to stack
        self.parent_stack.append(class_chunk)
        
        # Visit class body
        self.generic_visit(node)
        
        # Restore previous context
        self.current_class = previous_class
        self.parent_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        parent = getattr(node, "parent", None)
        
        if isinstance(parent, ast.Module):
            # Top-level function
            self._create_chunk(
                node, 
                "function", 
                node.name,
                parent="module",
                parent_chunk=self.parent_stack[-1] if self.parent_stack else None,
            )
        elif isinstance(parent, ast.ClassDef):
            # Method inside class
            self._create_chunk(
                node, 
                "method", 
                node.name,
                parent=parent.name,
                parent_chunk=self.parent_stack[-1] if self.parent_stack else None,
            )
        
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        parent = getattr(node, "parent", None)
        
        if isinstance(parent, ast.Module):
            # Top-level async function
            self._create_chunk(
                node, 
                "function", 
                node.name,
                parent="module",
                parent_chunk=self.parent_stack[-1] if self.parent_stack else None,
            )
        elif isinstance(parent, ast.ClassDef):
            # Async method inside class
            self._create_chunk(
                node, 
                "method", 
                node.name,
                parent=parent.name,
                parent_chunk=self.parent_stack[-1] if self.parent_stack else None,
            )
        
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        # Create module chunk first (root)
        module_chunk = self._create_module_chunk()
        
        # Push module to stack
        self.parent_stack.append(module_chunk)
        
        # Visit children to create classes and functions
        self.generic_visit(node)
        
        # Pop module from stack
        self.parent_stack.pop()


# ---------------- public API ----------------

def extract_ast_chunks(file_path: Path) -> List[CodeChunk]:
    source = file_path.read_text(encoding="utf-8")
    chunker = ASTChunker(source, str(file_path))
    
    # Visit the tree (creates all chunks with relationships)
    chunker.visit(chunker.tree)
    
    return chunker.chunks