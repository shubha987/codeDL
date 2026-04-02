"""
Git Repository Crawler - Intelligent repository cloning and file listing system.

This module serves as the entry point for ingesting Git repositories into our 
dataset pipeline. It handles cloning, file listing, metadata extraction, and
statistics generation with multiple strategies for different use cases.

ARCHITECTURE POSITION:
    - Ingestion Layer: Entry point for Git repositories
    - File Discovery: Finds and filters repository files
    - Metadata Collector: Gathers repo-level information

KEY FEATURES:
    1. Multi-strategy file listing (fast/rich/smart)
    2. Intelligent binary detection and filtering
    3. Repository metadata extraction with git history
    4. Agentic framework detection (through RepoMetadataExtractor)
    5. Repository statistics and cleanup utilities

DATA FLOW:
    Repository URL → Clone → File Discovery → Filtering → File Info/Metadata → Output

USE CASES:
    - FAST: When only file paths are needed (performance-critical)
    - RICH: When full metadata is required (dataset building)
    - SMART: Auto-chooses based on needs (balanced approach)

USAGE:
    crawler = GitCrawler()
    repo_path = crawler.clone_repository("https://github.com/org/repo.git")
    files_fast = crawler.list_files_fast(repo_path, extensions={'.py'})
    files_rich, stats = crawler.list_files_with_info(repo_path)
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Set, Dict, Tuple, Union, cast
import os
from dataclasses import dataclass
import time
from .repo_metadata import RepoMetadataExtractor


@dataclass
class RepoFileInfo:
    """Lightweight file info - optional for when you need it"""
    path: Path
    relative_path: str
    size: int = 0
    extension: str = ""
    is_binary: Optional[bool] = None


class GitCrawler:
    """
    Optimized Git crawler with fast listing + optional rich info
    """
    
    def __init__(self, cache_dir: Path = Path("data/raw/repos")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    # -------- CORE: Cloning (same for both) --------
    def clone_repository(self, repo_url: str) -> Optional[Path]:
        """Clone a repository if not already cloned"""
        repo_name = self._extract_repo_name(repo_url)
        repo_path = self.cache_dir / repo_name
        
        if repo_path.exists():
            print(f"✓ Repository already exists: {repo_path}")
            return repo_path
        
        print(f"📥 Cloning {repo_url}...")
        cmd = ["git", "clone", "--depth", "1", repo_url, str(repo_path)]
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            elapsed = time.time() - start_time
            print(f"✓ Cloned to {repo_path} ({elapsed:.1f}s)")
            return repo_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone {repo_url}: {e.stderr}")
            return None
        
    def extract_enhanced_metadata(self, repo_path: Path) -> Dict:
        """
        Extract enhanced metadata including agentic framework detection
        """
        extractor = RepoMetadataExtractor(repo_path)
        return extractor.extract_comprehensive_metadata()
    
    # -------- OPTION 1: FAST listing (old style) --------
    def list_files_fast(self, repo_path: Path, 
                       extensions: Optional[Set[str]] = None,
                       exclude_dirs: Optional[Set[str]] = None) -> List[Path]:
        """
        FAST file listing - returns just Path objects
        
        Use when you need speed and don't need metadata
        """
        if exclude_dirs is None:
            exclude_dirs = {'.git', '__pycache__', 'node_modules', 
                          'build', 'dist', '.venv', 'venv'}
        
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                
                # Filter by extension if specified
                if extensions:
                    if file_path.suffix.lower() in extensions:
                        files.append(file_path)
                else:
                    files.append(file_path)
        
        return sorted(files)  # Sort for consistency
    
    # -------- OPTION 2: RICH listing with metadata --------
    def list_files_with_info(self, repo_path: Path,
                            extensions: Optional[Set[str]] = None,
                            exclude_dirs: Optional[Set[str]] = None,
                            skip_binary: bool = True) -> Tuple[List[RepoFileInfo], Dict]:
        """
        RICH file listing - returns file info + statistics
        
        Use when you need metadata for better chunking
        """
        if exclude_dirs is None:
            exclude_dirs = {'.git', '__pycache__', 'node_modules', 
                          'build', 'dist', '.venv', 'venv', '.env'}
        
        file_infos = []
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_extension": {},
            "binary_files": 0,
            "text_files": 0
        }
        
        for root, dirs, filenames in os.walk(repo_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(repo_path)
                extension = file_path.suffix.lower()
                
                # Filter by extension
                if extensions and extension not in extensions:
                    continue
                
                try:
                    size = file_path.stat().st_size
                    is_binary = None
                    
                    # Check if binary (only when needed)
                    if skip_binary:
                        is_binary = self._is_binary_file(file_path)
                        if is_binary:
                            stats["binary_files"] += 1
                            continue  # Skip binary files
                        else:
                            stats["text_files"] += 1
                    
                    # Create file info
                    file_info = RepoFileInfo(
                        path=file_path,
                        relative_path=str(relative_path),
                        size=size,
                        extension=extension,
                        is_binary=is_binary
                    )
                    
                    file_infos.append(file_info)
                    
                    # Update stats
                    stats["total_files"] += 1
                    stats["total_size"] += size
                    stats["by_extension"][extension] = stats["by_extension"].get(extension, 0) + 1
                    
                except (OSError, PermissionError) as e:
                    print(f"⚠️ Could not read {file_path}: {e}")
                    continue
        
        # Sort by relative path
        file_infos.sort(key=lambda x: x.relative_path)
        
        return file_infos, stats
    
    # -------- OPTION 3: SMART listing (auto-chooses) --------
    def list_files(self, repo_path: Path, 
                  extensions: Optional[Set[str]] = None,
                  exclude_dirs: Optional[Set[str]] = None,
                  rich_metadata: bool = False,
                  skip_binary: bool = True) -> Union[List[Path], Tuple[List[RepoFileInfo], Dict]]:
        """
        SMART file listing - chooses method based on needs
        
        Args:
            rich_metadata: True for RepoFileInfo + stats, False for just Paths
            skip_binary: Skip binary files (only when rich_metadata=True)
        """
        if rich_metadata:
            return self.list_files_with_info(repo_path, extensions, exclude_dirs, skip_binary)
        else:
            return self.list_files_fast(repo_path, extensions, exclude_dirs)
    
    # -------- HELPER: Get README --------
    def get_readme_content(self, repo_path: Path) -> Optional[str]:
        """Quickly get README content if exists"""
        for pattern in ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md']:
            readme_path = repo_path / pattern
            if readme_path.exists():
                try:
                    return readme_path.read_text(encoding='utf-8', errors='ignore')[:5000]  # First 5k chars
                except:
                    continue
        return None
    
    # -------- HELPER: Get repository stats --------
   
    def get_repo_stats(self, repo_path: Path) -> Dict:
        """ACCURATE repository statistics (excludes .git)"""
        try:
            total_files = 0
            total_size = 0
            extensions = set()
            
            for root, dirs, files in os.walk(repo_path):
                # ✅ PROPERLY skip .git directory
                root_path = Path(root)
                if '.git' in root_path.parts:
                    continue  # Skip entire .git directory
                    
                total_files += len(files)
                for file in files:
                    file_path = Path(root) / file
                    try:
                        size = file_path.stat().st_size
                        total_size += size
                        if file_path.suffix:
                            extensions.add(file_path.suffix.lower())
                    except:
                        pass
            
            return {
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "unique_extensions": sorted(list(extensions))[:20],
                "path": str(repo_path),
                "name": repo_path.name,
                "note": "Size excludes .git directory"  # ✅ Add note
            }
        except Exception as e:
            return {"error": str(e)}

    
    # -------- UTILITY METHODS --------
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL"""
        name = repo_url.rstrip('/').split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name
    
    def _is_binary_file(self, file_path: Path, sample_size: int = 1024) -> bool:
        """Quick binary detection by sampling"""
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(sample_size)
            
            if not sample:
                return False
                
            # Check for null bytes (common in binaries)
            if b'\x00' in sample:
                return True
                
            # Count printable ASCII
            printable = sum(1 for byte in sample if 32 <= byte <= 126 or byte in (9, 10, 13))
            return (printable / len(sample)) < 0.8  # Less than 80% printable
        except:
            return True  # If we can't read, assume binary
    
    def cleanup_old_repos(self, max_age_days: int = 7):
        """Cleanup old cached repositories (optional)"""
        import shutil
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        for repo_dir in self.cache_dir.iterdir():
            if repo_dir.is_dir():
                try:
                    mtime = datetime.fromtimestamp(repo_dir.stat().st_mtime)
                    if mtime < cutoff:
                        print(f"🧹 Cleaning up old repo: {repo_dir.name}")
                        shutil.rmtree(repo_dir)
                except:
                    pass


# -------- SIMPLE USAGE EXAMPLES --------
def example_usage():
    """Example of how to use the crawler - FIXED VERSION"""
    crawler = GitCrawler()
    
    # 1. Clone a repository
    repo_path = crawler.clone_repository("https://github.com/microsoft/autogen.git")
    if not repo_path:
        print("❌ Failed to clone repository")
        return
    
    # 2. OPTION A: Fast listing (just paths)
    print("\n=== FAST LISTING ===")
    python_files = crawler.list_files_fast(repo_path, extensions={'.py'})
    print(f"Found {len(python_files)} Python files")
    
    # 3. OPTION B: Rich listing with metadata
    print("\n=== RICH LISTING ===")
    file_infos, stats = crawler.list_files_with_info(
        repo_path, 
        extensions={'.py', '.md', '.json', '.yaml'},
        skip_binary=True
    )
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size'] / 1024 / 1024:.2f} MB")
    print(f"Extensions: {stats['by_extension']}")
    
    # 4. OPTION C: Smart listing (auto) - FIXED
    print("\n=== SMART LISTING ===")
    # Returns just paths (fast)
    files_fast = crawler.list_files(repo_path, extensions={'.py'}, rich_metadata=False)
    # Type check for PyLance
    if isinstance(files_fast, list):
        print(f"Fast count: {len(files_fast)}")
    else:
        # This shouldn't happen with rich_metadata=False
        print("Unexpected return type from list_files()")
    
    # Returns info + stats (rich) - FIXED
    result = crawler.list_files(repo_path, extensions={'.py'}, rich_metadata=True)
    if isinstance(result, tuple):
        files_rich, stats = result
        print(f"Rich count: {len(files_rich)}")
    else:
        # This shouldn't happen with rich_metadata=True
        print("Unexpected return type from list_files()")
    
    # 5. Get README
    readme = crawler.get_readme_content(repo_path)
    if readme:
        print(f"\nREADME preview: {readme[:200]}...")
    
    # 6. Get repo stats
    repo_stats = crawler.get_repo_stats(repo_path)
    print(f"\nRepository stats: {repo_stats}")


if __name__ == "__main__":
    example_usage()





