"""
Repository File Type Chunker - Universal chunker for all file types.

This module provides file-type-aware chunking for repositories, handling
everything from Python code to configuration files, documentation, and
special files. It's the universal interface that delegates to specialized
chunkers based on file type.

ARCHITECTURE POSITION:
    - File Type Dispatcher: Routes files to appropriate chunkers
    - Universal Interface: Single entry point for all file types
    - Metadata Enricher: Adds repository context to all chunks

KEY FEATURES:
    1. File type detection and intelligent routing
    2. Hierarchical chunking for Python files
    3. Documentation chunking for markdown/RST
    4. Configuration file handling (JSON/YAML/TOML)
    5. Special file handling (README, requirements.txt, Dockerfile)
    6. Binary file detection and skipping

FILE TYPE SUPPORT:
    - .py: HierarchicalChunker (AST + Tree-sitter)
    - .md/.mdx/.rst: Documentation chunker
    - .json/.yaml/.toml: Configuration chunker
    - requirements.txt/Dockerfile: Special chunker
    - .txt/.cfg/.ini: Text chunker
    - README/LICENSE: Documentation chunker
    - Others: Text chunker with binary detection

DATA FLOW:
    File → Type detection → Route to specialized chunker → 
    Add repo metadata → Return chunks

USAGE:
    chunker = RepoChunker()
    chunks = chunker.chunk_file(Path("file.py"), repo_metadata)
"""

from pathlib import Path
from typing import List, Dict, Optional, cast
import json
import yaml
import re
import hashlib
from .hierarchical_chunker import HierarchicalChunker
from .chunk_schema import CodeChunk, ChunkAST, ChunkSpan, ChunkHierarchy, ChunkType, ASTSymbolType
from .doc_chunker import chunk_document as chunk_markdown_file


from pathlib import Path
from typing import List, Dict, Optional, cast
import json
import yaml
import re
import hashlib
from .hierarchical_chunker import HierarchicalChunker
from .chunk_schema import CodeChunk, ChunkAST, ChunkSpan, ChunkHierarchy, ChunkType, ASTSymbolType
from .doc_chunker import chunk_document as chunk_markdown_file


class RepoChunker:
    """
    Repository chunker that handles ALL file types with proper structure
    """
    
    def __init__(self, use_hierarchical: bool = True):
        if use_hierarchical:
            self.hierarchical_chunker = HierarchicalChunker()
        self.use_hierarchical = use_hierarchical
    
    def _generate_stable_id(self, content: str, prefix: str = "stable") -> str:
        """
        Generate deterministic chunk ID using SHA256.
        
        IMPORTANT: This ensures IDs are stable across runs, processes,
        and Python versions - crucial for RAG reproducibility.
        
        Args:
            content: The text content to hash
            prefix: ID prefix (config, doc, text, etc.)
            
        Returns:
            Deterministic ID like "config_8a3b2c1d"
        """
        # Use SHA256 for consistency with id_utils.py
        hash_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
        return f"{prefix}_{hash_digest}"
    
    def chunk_file(self, file_path: Path, repo_metadata: Optional[Dict] = None) -> List[CodeChunk]:
        """
        Chunk ANY file type with repository context
        
        Args:
            file_path: Path to the file
            repo_metadata: Optional dict with repo metadata
        """
        suffix = file_path.suffix.lower()
        
        # Python files - use your advanced hierarchical chunker
        if suffix == '.py':
            return self._chunk_python_file(file_path, repo_metadata)
        
        # Markdown/RST documentation
        elif suffix in ['.md', '.mdx', '.rst']:
            return self._chunk_markdown_file_wrapper(file_path, repo_metadata)
        
        # JSON config files
        elif suffix == '.json':
            return self._chunk_json_file(file_path, repo_metadata)
        
        # YAML/TOML config files
        elif suffix in ['.yaml', '.yml', '.toml']:
            return self._chunk_config_file(file_path, repo_metadata)
        
        # Requirements/Docker files
        elif file_path.name.lower() in ['requirements.txt', 'dockerfile', 'docker-compose.yml']:
            return self._chunk_special_file(file_path, repo_metadata)
        
        # Text files
        elif suffix in ['.txt', '.cfg', '.ini', '.conf']:
            return self._chunk_text_file(file_path, repo_metadata)
        
        # README/LICENSE files
        elif file_path.name.lower() in ['readme', 'readme.md', 'license', 'license.txt', 'license.md']:
            return self._chunk_readme_file(file_path, repo_metadata)
        
        # All other files
        else:
            return self._chunk_other_file(file_path, repo_metadata)
    
    def _chunk_python_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Use our hierarchical chunker for Python files"""
        try:
            if self.use_hierarchical:
                chunks = self.hierarchical_chunker.chunk_file(file_path)
            else:
                # Fallback to basic text chunking instead of hybrid
                return self._chunk_text_file(file_path, repo_metadata)
            
            # Add repository metadata
            if repo_metadata:
                for chunk in chunks:
                    if "repo_info" not in chunk.metadata:
                        chunk.metadata["repo_info"] = {}
                    chunk.metadata["repo_info"].update(repo_metadata)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Error chunking Python file {file_path}: {e}")
            return self._chunk_text_file(file_path, repo_metadata)
    
    def _chunk_markdown_file_wrapper(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Chunk markdown files using our doc_chunker"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Use your existing doc_chunker
            doc_chunks = chunk_markdown_file(
                content, 
                source_name=file_path.name,
                source_url=f"file://{file_path}"
            )
            
            # Convert to CodeChunk schema
            code_chunks = []
            for doc_chunk in doc_chunks:
                code_chunk = CodeChunk(
                    chunk_id=doc_chunk["chunk_id"],  # Already uses SHA1 from doc_chunker.py
                    file_path=str(file_path),
                    language=doc_chunk.get("language", "markdown"),
                    chunk_type="documentation",
                    code=doc_chunk["content"],
                    ast=ChunkAST(
                        symbol_type="documentation",
                        name=file_path.name,
                        parent=None,
                        docstring=None
                    ),
                    span=ChunkSpan(
                        start_line=doc_chunk.get("metadata", {}).get("line_start", 1),
                        end_line=doc_chunk.get("metadata", {}).get("line_end", 1)
                    ),
                    metadata={
                        "doc_chunk_type": doc_chunk.get("chunk_type", "text"),
                        "repo_info": repo_metadata or {},
                        **doc_chunk.get("metadata", {})
                    },
                    hierarchy=ChunkHierarchy(
                        is_primary=True,
                        is_extracted=False,
                        depth=0
                    )
                )
                code_chunks.append(code_chunk)
            
            return code_chunks
            
        except Exception as e:
            print(f"⚠️ Error chunking markdown file {file_path}: {e}")
            return self._chunk_text_file(file_path, repo_metadata)
    
    def _chunk_json_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Chunk JSON config files"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            data = json.loads(content)
            
            pretty_content = json.dumps(data, indent=2)
            
            # ✅ FIXED: Use deterministic SHA256 instead of hash()
            chunk = CodeChunk(
                chunk_id=self._generate_stable_id(pretty_content, "config"),
                file_path=str(file_path),
                language="json",
                chunk_type="configuration",
                code=pretty_content,
                ast=ChunkAST(
                    symbol_type="configuration",
                    name=file_path.name,
                    parent=None,
                    docstring=None
                ),
                span=ChunkSpan(
                    start_line=1,
                    end_line=len(pretty_content.split('\n'))
                ),
                metadata={
                    "file_type": "json_config",
                    "config_keys": list(data.keys()) if isinstance(data, dict) else [],
                    "repo_info": repo_metadata or {}
                },
                hierarchy=ChunkHierarchy(
                    is_primary=True,
                    is_extracted=False,
                    depth=0
                )
            )
            
            return [chunk]
            
        except Exception as e:
            print(f"⚠️ Error chunking JSON file {file_path}: {e}")
            return self._chunk_text_file(file_path, repo_metadata)
    
    def _chunk_config_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Chunk YAML/TOML config files"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            suffix = file_path.suffix.lower()
            
            language = "yaml" if suffix in ['.yaml', '.yml'] else "toml"
            
            # ✅ FIXED: Use deterministic SHA256 instead of hash()
            chunk = CodeChunk(
                chunk_id=self._generate_stable_id(content, "config"),
                file_path=str(file_path),
                language=language,
                chunk_type="configuration",
                code=content,
                ast=ChunkAST(
                    symbol_type="configuration",
                    name=file_path.name,
                    parent=None,
                    docstring=None
                ),
                span=ChunkSpan(
                    start_line=1,
                    end_line=len(content.split('\n'))
                ),
                metadata={
                    "file_type": f"{language}_config",
                    "repo_info": repo_metadata or {}
                },
                hierarchy=ChunkHierarchy(
                    is_primary=True,
                    is_extracted=False,
                    depth=0
                )
            )
            
            return [chunk]
            
        except Exception as e:
            print(f"⚠️ Error chunking config file {file_path}: {e}")
            return self._chunk_text_file(file_path, repo_metadata)
    
    def _chunk_special_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Chunk special files (requirements.txt, Dockerfile, etc.)"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            file_name = file_path.name.lower()
            
            if 'requirements' in file_name:
                language = "requirements"
                chunk_type = "configuration"
                prefix = "config"
            elif 'docker' in file_name:
                language = "dockerfile"
                chunk_type = "script"
                prefix = "script"
            else:
                language = "text"
                chunk_type = "text"
                prefix = "text"
            
            # ✅ FIXED: Use deterministic SHA256 instead of hash()
            chunk = CodeChunk(
                chunk_id=self._generate_stable_id(content, prefix),
                file_path=str(file_path),
                language=language,
                chunk_type=chunk_type,
                code=content,
                ast=ChunkAST(
                    symbol_type=chunk_type,
                    name=file_path.name,
                    parent=None,
                    docstring=None
                ),
                span=ChunkSpan(
                    start_line=1,
                    end_line=len(content.split('\n'))
                ),
                metadata={
                    "file_type": file_name,
                    "repo_info": repo_metadata or {},
                    "dependencies": self._extract_dependencies(content) if "requirements" in file_name else []
                },
                hierarchy=ChunkHierarchy(
                    is_primary=True,
                    is_extracted=False,
                    depth=0
                )
            )
            
            return [chunk]
            
        except Exception as e:
            print(f"⚠️ Error chunking special file {file_path}: {e}")
            return self._chunk_text_file(file_path, repo_metadata)
    
    def _chunk_text_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Chunk plain text files"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Create a single chunk for small files, multiple for large ones
            if len(content.split('\n')) <= 200:
                chunks = [self._create_text_chunk(content, file_path, repo_metadata)]
            else:
                # Split large text files into reasonable chunks
                chunks = []
                lines = content.split('\n')
                chunk_size = 100
                
                for i in range(0, len(lines), chunk_size):
                    chunk_lines = lines[i:i + chunk_size]
                    chunk_content = '\n'.join(chunk_lines)
                    
                    chunk = self._create_text_chunk(
                        chunk_content, 
                        file_path, 
                        repo_metadata,
                        chunk_index=i // chunk_size
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Error reading text file {file_path}: {e}")
            return []
    
    def _chunk_readme_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Special handling for README/LICENSE files"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            file_name_lower = file_path.name.lower()
            
            # Determine appropriate prefix
            if 'readme' in file_name_lower:
                prefix = "doc"
            elif 'license' in file_name_lower:
                prefix = "license"
            else:
                prefix = "doc"
            
            # ✅ FIXED: Use deterministic SHA256 instead of hash()
            chunk = CodeChunk(
                chunk_id=self._generate_stable_id(content, prefix),
                file_path=str(file_path),
                language="markdown" if file_path.suffix in ['.md', '.mdx'] else "text",
                chunk_type="documentation",
                code=content,
                ast=ChunkAST(
                    symbol_type="documentation",
                    name=file_path.name,
                    parent=None,
                    docstring=None
                ),
                span=ChunkSpan(
                    start_line=1,
                    end_line=len(content.split('\n'))
                ),
                metadata={
                    "file_type": "readme_license",
                    "is_readme": "readme" in file_name_lower,
                    "is_license": "license" in file_name_lower,
                    "repo_info": repo_metadata or {}
                },
                hierarchy=ChunkHierarchy(
                    is_primary=True,
                    is_extracted=False,
                    depth=0
                )
            )
            
            return [chunk]
            
        except Exception as e:
            print(f"⚠️ Error chunking README file {file_path}: {e}")
            return self._chunk_text_file(file_path, repo_metadata)
    
    def _chunk_other_file(self, file_path: Path, repo_metadata: Optional[Dict]) -> List[CodeChunk]:
        """Fallback for unknown file types (binary or unsupported)"""
        try:
            # Try to read as text first
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # If it looks like binary (mostly non-printable characters)
            if self._looks_like_binary(content):
                print(f"⚠️ Skipping binary file: {file_path}")
                return []
            
            # If readable text, treat as text file
            return self._chunk_text_file(file_path, repo_metadata)
            
        except UnicodeDecodeError:
            print(f"⚠️ Skipping binary file: {file_path}")
            return []
        except Exception as e:
            print(f"⚠️ Error with file {file_path}: {e}")
            return []
    
    def _create_text_chunk(self, content: str, file_path: Path, 
                          repo_metadata: Optional[Dict], chunk_index: int = 0) -> CodeChunk:
        """Helper to create a text chunk"""
        lines = content.split('\n')
        
        # ✅ ENHANCED: Use deterministic ID that includes chunk_index for uniqueness
        id_payload = f"{content}_{chunk_index}"
        
        return CodeChunk(
            chunk_id=self._generate_stable_id(id_payload, "text"),
            file_path=str(file_path),
            language="text",
            chunk_type="text",
            code=content,
            ast=ChunkAST(
                symbol_type="text",
                name=file_path.name,
                parent=None,
                docstring=None
            ),
            span=ChunkSpan(
                start_line=1,
                end_line=len(lines)
            ),
            metadata={
                "file_type": "text",
                "chunk_index": chunk_index,
                "total_lines": len(lines),
                "repo_info": repo_metadata or {}
            },
            hierarchy=ChunkHierarchy(
                is_primary=True,
                is_extracted=False,
                depth=0
            )
        )
    
    def _extract_dependencies(self, requirements_content: str) -> List[str]:
        """Extract package names from requirements.txt"""
        dependencies = []
        for line in requirements_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before version specifiers)
                package = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                if package:
                    dependencies.append(package)
        return dependencies
    
    def _looks_like_binary(self, content: str, threshold: float = 0.3) -> bool:
        """Check if content looks like binary data"""
        if not content:
            return False
        
        # Count printable vs non-printable characters
        printable = sum(1 for c in content if 32 <= ord(c) <= 126 or c in '\n\r\t')
        total = len(content)
        
        if total == 0:
            return False
        
        ratio = printable / total
        return ratio < threshold