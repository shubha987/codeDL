"""
Hierarchical chunk coordinator - Orchestrates AST and Tree-sitter chunking.

This module serves as the coordination layer that integrates AST (semantic)
and Tree-sitter (syntactic) chunking. It ensures that:
1. AST chunks get precise byte spans from Tree-sitter
2. Hierarchy relationships are preserved across both sources
3. Parent-child relationships are correctly established
4. All chunks have consistent metadata and structure

ARCHITECTURE POSITION:
    - Coordination Layer: Integrates AST and Tree-sitter
    - Relationship Manager: Maintains parent-child links
    - Quality Enforcer: Ensures consistent chunk structure

KEY RESPONSIBILITIES:
    1. Enrich AST chunks with Tree-sitter byte spans
    2. Build and verify hierarchy relationships
    3. Create secondary chunks for extracted content
    4. Ensure type safety across all chunk operations

FLOW:
    File → AST chunks (semantic) + Tree-sitter chunks (spans)
           → HierarchicalChunker.enrich_and_link()
           → Final chunks with hierarchy + precise spans

USAGE:
    chunker = HierarchicalChunker()
    chunks = chunker.chunk_file(Path("file.py"))
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, cast
import uuid

from .ast_chunker import extract_ast_chunks
from .ts_chunker import extract_ts_chunks
from .chunk_schema import CodeChunk, ChunkHierarchy, ChunkType


class HierarchicalChunker:
    def __init__(self):
        self.chunks_by_id: Dict[str, CodeChunk] = {}
        self.imports_by_file: Dict[str, str] = {}  # Track imports chunks by file

    # ---------------- helpers ----------------

    def _build_ts_span_map(
        self, ts_chunks: List[CodeChunk]
    ) -> Dict[Tuple[int, int], CodeChunk]:
        span_map: Dict[Tuple[int, int], CodeChunk] = {}

        for c in ts_chunks:
            if c.span.start_line is None or c.span.end_line is None:
                continue

            span_map[(c.span.start_line, c.span.end_line)] = c

        return span_map

    def _enrich_spans_with_tree_sitter(
        self, ast_chunks: List[CodeChunk], ts_chunks: List[CodeChunk]
    ) -> List[CodeChunk]:
        """Enrich AST chunks with Tree-sitter precise byte spans"""
        ts_span_map = self._build_ts_span_map(ts_chunks)
        
        for ast_chunk in ast_chunks:
            if ast_chunk.span.start_line is not None and ast_chunk.span.end_line is not None:
                key: Tuple[int, int] = (ast_chunk.span.start_line, ast_chunk.span.end_line)
                ts_match = ts_span_map.get(key)
                
                if ts_match:
                    # Update byte spans from Tree-sitter
                    ast_chunk.span.start_byte = ts_match.span.start_byte
                    ast_chunk.span.end_byte = ts_match.span.end_byte
        
        return ast_chunks

    def _preserve_hierarchy_relationships(self, all_chunks: List[CodeChunk]) -> None:
        """Ensure all hierarchy relationships are preserved with proper typing"""
        # Build mapping for quick lookup
        for chunk in all_chunks:
            self.chunks_by_id[chunk.chunk_id] = chunk
        
        # Verify and fix parent-child relationships with type safety
        for chunk in all_chunks:
            # Ensure hierarchy exists
            if not hasattr(chunk, 'hierarchy') or chunk.hierarchy is None:
                chunk.hierarchy = ChunkHierarchy()
            
            if chunk.hierarchy.parent_id:
                parent = self.chunks_by_id.get(chunk.hierarchy.parent_id)
                if parent:
                    # Ensure parent has hierarchy
                    if not hasattr(parent, 'hierarchy') or parent.hierarchy is None:
                        parent.hierarchy = ChunkHierarchy()
                    
                    # Add child to parent with type safety
                    if chunk.chunk_id not in parent.hierarchy.children_ids:
                        parent.hierarchy.children_ids.append(chunk.chunk_id)

    def _create_secondary_chunks_for_extracted_content(
        self, ast_chunks: List[CodeChunk]
    ) -> List[CodeChunk]:
        """Create secondary chunks for extracted content (if needed)"""
        secondary_chunks: List[CodeChunk] = []
        
        # Currently, our AST chunker creates everything as primary
        # This method is for future extensions
        return secondary_chunks

    def _update_hierarchy_relationships(self, all_chunks: List[CodeChunk]) -> None:
        """Update parent-child relationships based on AST parent field with proper typing"""
        # Create mapping from (name, type) to chunk_id
        chunk_map: Dict[Tuple[Optional[str], ChunkType], str] = {}
        
        for chunk in all_chunks:
            if chunk.ast and chunk.ast.name:
                key = (chunk.ast.name, chunk.chunk_type)
                chunk_map[key] = chunk.chunk_id
        
        # Update parent relationships with type safety
        for chunk in all_chunks:
            # Ensure hierarchy exists
            if not hasattr(chunk, 'hierarchy') or chunk.hierarchy is None:
                chunk.hierarchy = ChunkHierarchy()
            
            if chunk.ast and chunk.ast.parent and chunk.ast.parent != "None":
                # Determine parent type based on current chunk type
                parent_type: ChunkType = "class" if chunk.chunk_type == "method" else "module"
                
                # Try to find parent chunk
                parent_key = (chunk.ast.parent, parent_type)
                parent_id = chunk_map.get(parent_key)
                
                if parent_id and parent_id in self.chunks_by_id:
                    chunk.hierarchy.parent_id = parent_id
                    
                    # Add this chunk to parent's children with type safety
                    parent_chunk = self.chunks_by_id.get(parent_id)
                    if parent_chunk:
                        # Ensure parent has hierarchy
                        if not hasattr(parent_chunk, 'hierarchy') or parent_chunk.hierarchy is None:
                            parent_chunk.hierarchy = ChunkHierarchy()
                        
                        if chunk.chunk_id not in parent_chunk.hierarchy.children_ids:
                            parent_chunk.hierarchy.children_ids.append(chunk.chunk_id)
        
        # Set depth based on parent relationships
        for chunk in all_chunks:
            if chunk.hierarchy.parent_id:
                parent = self.chunks_by_id.get(chunk.hierarchy.parent_id)
                if parent and hasattr(parent, 'hierarchy') and parent.hierarchy:
                    chunk.hierarchy.depth = parent.hierarchy.depth + 1

    # ---------------- public API ----------------

    def chunk_file(self, file_path: Path) -> List[CodeChunk]:
        self.chunks_by_id.clear()
        self.imports_by_file.clear()

        try:
            ast_chunks = extract_ast_chunks(file_path)
        except SyntaxError:
            ast_chunks = []

        # Get Tree-sitter chunks for byte-level precision
        ts_chunks = extract_ts_chunks(file_path)
        
        # Enrich AST chunks with Tree-sitter byte spans
        enriched_chunks = self._enrich_spans_with_tree_sitter(ast_chunks, ts_chunks)
        
        # Update hierarchy relationships with proper typing
        self._update_hierarchy_relationships(enriched_chunks)
        
        # Preserve any existing relationships
        self._preserve_hierarchy_relationships(enriched_chunks)
        
        # Create any needed secondary chunks
        secondary_chunks = self._create_secondary_chunks_for_extracted_content(enriched_chunks)
        
        return enriched_chunks + secondary_chunks
