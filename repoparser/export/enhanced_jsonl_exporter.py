"""
Enhanced JSONL Exporter for Git Repositories - Repository-aware export with context.

This module exports repository chunks with enhanced metadata and cross-file
context. It's specifically designed for GIT REPOSITORIES and adds repository
metadata, similar file context, and repository-level statistics.

ARCHITECTURE POSITION:
    - Repository Export Layer: Specialized for Git repositories
    - Context Enricher: Adds cross-file relationships
    - Statistics Generator: Creates repository-level analytics

KEY FEATURES:
    1. Repository metadata injection (git info, structure, dependencies)
    2. Cross-file context (similar files, repository context)
    3. Repository statistics generation
    4. Clean JSONL format with enhanced metadata
    5. Agentic framework detection (currently simplified)

DIFFERENCE FROM BASIC EXPORTER:
    - Adds full repository metadata (git history, structure)
    - Includes cross-file relationships
    - Generates repository-level statistics
    - Designed for repository-scale datasets

OUTPUT STRUCTURE:
    {
        "chunk_id": "...",
        "file_path": "...",
        "metadata": {
            "repo_info": {full repository metadata},
            "repository_context": {similar files, cross-file info}
        },
        ... other chunk fields
    }

USAGE:
    exporter = EnhancedRepoExporter()
    result = exporter.export_with_repo_analysis(chunks, output_path, repo_metadata)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..chunking.chunk_schema import CodeChunk


class EnhancedRepoExporter:
    """
    Enhanced exporter for GIT REPOSITORY files - SIMPLIFIED (no agentic analysis)
    """
    
    def export_with_repo_analysis(self,
                                 chunks: List[CodeChunk],
                                 output_path: Path,
                                 repo_metadata: Dict,
                                 print_stats: bool = True) -> Dict[str, Any]:
        """
        Export repository files with basic analysis (NO AGENTIC SCORING).
        """
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Enhance chunks with repository context
        enhanced_chunks = []
        for chunk in chunks:
            chunk_dict = self._chunk_to_dict(chunk)
            
            # Add repository metadata (SIMPLIFIED - no agentic)
            self._add_repo_metadata(chunk_dict, repo_metadata)
            
            # ✅ NO AGENTIC ANALYSIS - commented out
            # self._add_repo_agentic_analysis(chunk_dict, repo_metadata)
            
            # Add cross-file context
            self._add_cross_file_context(chunk_dict, chunks)
            
            enhanced_chunks.append(chunk_dict)
        
        # Write JSONL
        with output_path.open("w", encoding="utf-8") as f:
            for chunk_dict in enhanced_chunks:
                f.write(json.dumps(chunk_dict, ensure_ascii=False) + "\n")
        
        # Generate and save repository stats (SIMPLIFIED)
        stats = self._generate_repo_stats(enhanced_chunks, repo_metadata)
        stats_file = output_path.parent / f"{output_path.stem}_repo_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        if print_stats:
            self._print_repo_stats(stats)
        
        return {
            "chunks_file": str(output_path),
            "stats_file": str(stats_file),
            "total_chunks": len(chunks),
            "repo_name": repo_metadata.get("basic", {}).get("repo_name", "unknown"),
            "source_type": "git_repository"
        }
    
    def _chunk_to_dict(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Convert to dict - SAME format"""
        return {
            "chunk_id": chunk.chunk_id,
            "file_path": chunk.file_path,
            "language": chunk.language,
            "chunk_type": chunk.chunk_type,
            "code": chunk.code,
            "ast": {
                "symbol_type": chunk.ast.symbol_type,
                "name": chunk.ast.name,
                "parent": chunk.ast.parent,
                "docstring": chunk.ast.docstring,
                "decorators": chunk.ast.decorators,
                "imports": chunk.ast.imports,
            } if chunk.ast else None,
            "span": {
                "start_byte": chunk.span.start_byte,
                "end_byte": chunk.span.end_byte,
                "start_line": chunk.span.start_line,
                "end_line": chunk.span.end_line,
            } if chunk.span else None,
            "metadata": chunk.metadata.copy() if chunk.metadata else {},
            "hierarchy": {
                "parent_id": chunk.hierarchy.parent_id,
                "children_ids": chunk.hierarchy.children_ids,
                "depth": chunk.hierarchy.depth,
                "is_primary": chunk.hierarchy.is_primary,
                "is_extracted": chunk.hierarchy.is_extracted,
            }
        }
    
    def _add_repo_metadata(self, chunk_dict: Dict, repo_metadata: Dict):
        """Add repository metadata (SIMPLIFIED)"""
        metadata = chunk_dict.get("metadata", {})
        
        if "repo_info" not in metadata:
            metadata["repo_info"] = {}
        
        # Basic repo info only
        metadata["repo_info"].update({
            "repository": repo_metadata.get("basic", {}),
            "git_info": repo_metadata.get("git", {}),
            "dependencies": repo_metadata.get("dependencies", {}),
            "structure": repo_metadata.get("structure", {}),
            "source_type": "git_repository",
            "processing_timestamp": datetime.now().isoformat()
        })
        
        # ✅ NO AGENTIC FRAMEWORKS in metadata
        # metadata["repo_info"]["agentic_frameworks"] = repo_metadata.get("agentic_detection", {})
        
        chunk_dict["metadata"] = metadata
    
    def _add_cross_file_context(
        self,
        chunk_dict: Dict[str, Any],
        all_chunks: List[CodeChunk]
    ):
        """Add context from other files"""
        metadata = chunk_dict.get("metadata", {})
        current_file = chunk_dict["file_path"]
        similar_files_set = set()
        
        for other_chunk in all_chunks:
            other_file = other_chunk.file_path
            if other_file != current_file:
                similar_files_set.add(other_file)
        
        if similar_files_set:
            similar_files = list(similar_files_set)
            metadata["repository_context"] = {
                "similar_files": similar_files[:5],
                "total_similar_files": len(similar_files)
            }
        
        chunk_dict["metadata"] = metadata
    
    def _generate_repo_stats(self, chunks: List[Dict], repo_metadata: Dict) -> Dict:
        """Generate basic statistics (NO AGENTIC METRICS)"""
        stats = {
            "repository_summary": {
                "name": repo_metadata.get("basic", {}).get("repo_name", "unknown"),
                "total_files": repo_metadata.get("basic", {}).get("file_count", 0),
                "size_mb": repo_metadata.get("basic", {}).get("size_mb", 0),
                # ✅ NO AGENTIC FRAMEWORKS LISTED
                "processing_timestamp": datetime.now().isoformat()
            },
            "chunk_analysis": {
                "total_chunks": len(chunks),
                # ✅ NO AGENTIC METRICS
                "file_type_distribution": {},
                "chunk_type_distribution": {},
                "language_distribution": {}
            }
        }
        
        # Basic distributions only
        for chunk in chunks:
            file_path = chunk["file_path"]
            file_type = Path(file_path).suffix.lower()
            stats["chunk_analysis"]["file_type_distribution"][file_type] = \
                stats["chunk_analysis"]["file_type_distribution"].get(file_type, 0) + 1
            
            chunk_type = chunk["chunk_type"]
            stats["chunk_analysis"]["chunk_type_distribution"][chunk_type] = \
                stats["chunk_analysis"]["chunk_type_distribution"].get(chunk_type, 0) + 1
            
            language = chunk["language"]
            stats["chunk_analysis"]["language_distribution"][language] = \
                stats["chunk_analysis"]["language_distribution"].get(language, 0) + 1
        
        return stats
    
    def _print_repo_stats(self, stats: Dict):
        """Print basic statistics"""
        print("\n" + "="*70)
        print("📊 REPOSITORY ANALYSIS STATISTICS (SIMPLIFIED)")
        print("="*70)
        
        repo_summary = stats["repository_summary"]
        chunk_analysis = stats["chunk_analysis"]
        
        print(f"Repository: {repo_summary['name']}")
        print(f"Total Files: {repo_summary['total_files']}")
        print(f"Size: {repo_summary['size_mb']} MB")
        
        print(f"\nChunk Analysis:")
        print(f"  Total Chunks: {chunk_analysis['total_chunks']}")
        
        print("\n📁 File Types:")
        for ftype, count in sorted(chunk_analysis["file_type_distribution"].items(), 
                                  key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {ftype}: {count}")
        
        print("="*70)


# Backward compatibility
def export_repo_chunks_jsonl(
    chunks: List[CodeChunk],
    output_path: Path,
    repo_metadata: Dict,
    print_stats: bool = True
) -> Dict[str, Any]:
    exporter = EnhancedRepoExporter()
    return exporter.export_with_repo_analysis(
        chunks=chunks,
        output_path=output_path,
        repo_metadata=repo_metadata,
        print_stats=print_stats
    )

