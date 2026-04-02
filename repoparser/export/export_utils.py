# # Export utilities for language normalization and statistics

# import re
# import json
# from typing import Dict, Any, List, Optional
# from datetime import datetime


# def normalize_language(lang: Optional[str]) -> str:
#     """
#     Clean and normalize language strings.
    
#     Args:
#         lang: Language string (can be None)
    
#     Returns:
#         Normalized language string
#     """
#     if not lang or lang == "unknown":
#         return "unknown"
    
#     lang_str = str(lang)
    
#     # Remove everything after first space (title=..., hl_lines=...)
#     if ' ' in lang_str:
#         lang_str = lang_str.split(' ')[0]
    
#     # Clean quotes and extra characters
#     lang_str = re.sub(r'[`\'"\{\}\[\]]', '', lang_str)
    
#     # Normalize common language names
#     language_map = {
#         # Python variations
#         'py': 'python',
#         'python3': 'python',
#         'pycon': 'python',
#         'ipython': 'python',
        
#         # JavaScript/TypeScript
#         'js': 'javascript',
#         'javascript6': 'javascript',
#         'es6': 'javascript',
#         'node': 'javascript',
#         'ts': 'typescript',
#         'tsx': 'typescript',
#         'jsx': 'javascript',
        
#         # Shell/Bash
#         'bash': 'bash',
#         'shell': 'bash',
#         'sh': 'bash',
#         'zsh': 'bash',
#         'console': 'bash',
#         'powershell': 'powershell',
#         'ps1': 'powershell',
        
#         # Markup/Config
#         'md': 'markdown',
#         'markdown': 'markdown',
#         'rst': 'rst',
#         'restructuredtext': 'rst',
#         'yml': 'yaml',
#         'toml': 'toml',
#         'json': 'json',
#         'json5': 'json',
#         'xml': 'xml',
#         'html': 'html',
#         'css': 'css',
        
#         # Data/Query
#         'sql': 'sql',
#         'postgresql': 'sql',
#         'mysql': 'sql',
#         'graphql': 'graphql',
        
#         # Other common languages
#         'java': 'java',
#         'cpp': 'cpp',
#         'c++': 'cpp',
#         'c': 'c',
#         'c#': 'csharp',
#         'cs': 'csharp',
#         'go': 'go',
#         'golang': 'go',
#         'rust': 'rust',
#         'rs': 'rust',
#         'ruby': 'ruby',
#         'rb': 'ruby',
#         'php': 'php',
#         'swift': 'swift',
#         'kotlin': 'kotlin',
#         'scala': 'scala',
#         'r': 'r',
#         'perl': 'perl',
#         'pl': 'perl',
        
#         # Special/Other
#         'dockerfile': 'docker',
#         'docker': 'docker',
#         'makefile': 'make',
#         'make': 'make',
#         'cmake': 'cmake',
#         'requirements': 'text',
#         'txt': 'text',
#         'text': 'text',
#         'plain': 'text',
#         'output': 'text',
#         'result': 'text',
#         'mermaid': 'mermaid',
#         'plantuml': 'plantuml',
#         'puml': 'plantuml',
#         'dot': 'graphviz',
#         'graphviz': 'graphviz',
#     }
    
#     # Normalize case
#     lang_lower = lang_str.lower()
    
#     # First check exact match in language map
#     if lang_lower in language_map:
#         return language_map[lang_lower]
    
#     # Check for common patterns
#     if any(pattern in lang_lower for pattern in ['python', 'py']):
#         return 'python'
#     elif any(pattern in lang_lower for pattern in ['javascript', 'js', 'ts']):
#         if 'type' in lang_lower or 'ts' in lang_lower:
#             return 'typescript'
#         return 'javascript'
#     elif any(pattern in lang_lower for pattern in ['bash', 'shell', 'sh']):
#         return 'bash'
#     elif any(pattern in lang_lower for pattern in ['markdown', 'md']):
#         return 'markdown'
#     elif any(pattern in lang_lower for pattern in ['docker', 'container']):
#         return 'docker'
#     elif any(pattern in lang_lower for pattern in ['json', 'yaml', 'toml']):
#         if 'json' in lang_lower:
#             return 'json'
#         elif 'yaml' in lang_lower or 'yml' in lang_lower:
#             return 'yaml'
#         elif 'toml' in lang_lower:
#             return 'toml'
    
#     # Default to unknown for unrecognized languages
#     return "unknown"


# def clean_language_distribution(lang_dist: Dict[str, int]) -> Dict[str, int]:
#     """Clean up messy language distribution statistics"""
#     cleaned = {}
    
#     for lang, count in lang_dist.items():
#         clean_lang = normalize_language(lang)
#         cleaned[clean_lang] = cleaned.get(clean_lang, 0) + count
    
#     return cleaned


# def format_statistics(stats: Dict[str, Any]) -> str:
#     """Format statistics for clean display"""
#     lines = []
#     lines.append("\n" + "="*60)
#     lines.append("📊 DATASET STATISTICS")
#     lines.append("="*60)
    
#     # Basic stats
#     total_chunks = stats.get('total_chunks', 0)
    
#     if total_chunks > 0:
#         lines.append(f"Total Chunks: {total_chunks:,}")
    
#     if 'total_files' in stats:
#         lines.append(f"Total Files: {stats['total_files']:,}")
    
#     if 'unique_languages' in stats:
#         lines.append(f"Unique Languages: {stats['unique_languages']}")
    
#     if 'docstring_coverage_ratio' in stats:
#         coverage = stats['docstring_coverage_ratio'] * 100
#         lines.append(f"Docstring Coverage: {coverage:.1f}%")
    
#     # Chunk type distribution
#     if 'chunk_type_distribution' in stats:
#         lines.append("\n📁 Chunk Types:")
#         chunk_types = stats['chunk_type_distribution']
#         for chunk_type, count in sorted(
#             chunk_types.items(),
#             key=lambda x: x[1],
#             reverse=True
#         )[:10]:
#             percentage = (count / total_chunks) * 100 if total_chunks > 0 else 0
#             lines.append(f"  {chunk_type:20} {count:6,} ({percentage:5.1f}%)")
    
#     # Language distribution (cleaned)
#     if 'language_distribution' in stats:
#         lines.append("\n🌐 Languages:")
#         lang_dist = clean_language_distribution(stats['language_distribution'])
#         for lang, count in sorted(lang_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
#             percentage = (count / total_chunks) * 100 if total_chunks > 0 else 0
#             lines.append(f"  {lang:20} {count:6,} ({percentage:5.1f}%)")
    
#     # AST symbol distribution
#     if 'ast_symbol_distribution' in stats:
#         lines.append("\n🔧 AST Symbols:")
#         ast_symbols = stats['ast_symbol_distribution']
#         for symbol, count in sorted(
#             ast_symbols.items(),
#             key=lambda x: x[1],
#             reverse=True
#         )[:10]:
#             percentage = (count / total_chunks) * 100 if total_chunks > 0 else 0
#             lines.append(f"  {symbol:20} {count:6,} ({percentage:5.1f}%)")
    
#     lines.append("="*60)
#     return "\n".join(lines)


# def generate_dataset_metadata(chunks: List[Dict], source_info: Dict) -> Dict[str, Any]:
#     """Generate metadata for a dataset"""
#     total_chunks = len(chunks)
    
#     # Count by type and language
#     chunk_types = {}
#     languages = {}
    
#     for chunk in chunks:
#         chunk_type = chunk.get('chunk_type', 'unknown')
#         language = chunk.get('language', 'unknown')
        
#         chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
#         languages[language] = languages.get(language, 0) + 1
    
#     # Clean languages
#     languages = clean_language_distribution(languages)
    
#     # Calculate average sizes
#     total_code_chars = sum(len(chunk.get('code', '')) for chunk in chunks)
#     avg_code_size = total_code_chars / total_chunks if total_chunks > 0 else 0
    
#     return {
#         "dataset_info": {
#             "name": source_info.get("name", "unnamed_dataset"),
#             "source": source_info.get("source", "unknown"),
#             "source_type": source_info.get("source_type", "unknown"),
#             "created_at": datetime.now().isoformat(),
#             "version": "1.0.0"
#         },
#         "statistics": {
#             "total_chunks": total_chunks,
#             "chunk_types": chunk_types,
#             "languages": languages,
#             "avg_code_size_chars": round(avg_code_size, 2),
#             "total_code_chars": total_code_chars
#         },
#         "source_info": source_info,
#         "schema_version": "1.0",
#         "generated_by": "CodeMode Agentic Embeddings Pipeline"
#     }