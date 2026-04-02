"""
Repository Metadata Extractor - Advanced metadata extraction for Git repositories.

This module extracts comprehensive metadata from Git repositories with a 
special focus on agentic framework detection. It analyzes repository structure,
dependencies, git history, and patterns to identify agentic code patterns.

ARCHITECTURE POSITION:
    - Repository Analyzer: Deep analysis of Git repositories
    - Agentic Detector: Identifies agentic framework usage
    - Dependency Mapper: Extracts dependency information

KEY FEATURES:
    1. Agentic framework detection across multiple frameworks
    2. Comprehensive dependency extraction (Python, Node.js, Docker)
    3. Git metadata extraction (commits, branches, tags)
    4. Repository structure analysis
    5. Entry point and configuration file discovery
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class RepoMetadataExtractor:
    """Enhanced metadata extractor for agentic codebases"""

    AGENTIC_FRAMEWORKS = {
        "langchain": ["langchain", "langsmith", "lc", "chain", "agent"],
        "autogen": ["autogen", "agent", "groupchat"],
        "crewai": ["crewai", "crew", "task", "agent"],
        "haystack": ["haystack", "pipeline", "node"],
        "llamaindex": ["llama_index", "query_engine", "index"],
        "semantic_kernel": ["semantic_kernel", "sk"],
        "transformers_agents": ["transformers_agents", "huggingface"],
        "camel": ["camel", "role_playing"],
        "agents": ["agent", "tool", "workflow", "orchestrator"],
    }

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def extract_comprehensive_metadata(self) -> Dict:
        return {
            "basic": self.extract_basic_metadata(),
            "git": self.extract_git_metadata(),
            "dependencies": self.extract_dependency_info(),
            "structure": self.extract_structure_info(),
            "agentic_detection": self.detect_agentic_frameworks(),
            "entry_points": self.find_entry_points(),
            "config_files": self.find_config_files(),
        }

    # 🔧 FIXED: Now returns actual repo name, not folder name
    def extract_basic_metadata(self) -> Dict:
        """Extract basic repository metadata"""
        return {
            "repo_name": self._get_actual_repo_name(),  # 🎯 FIXED LINE
            "local_path": str(self.repo_path),
            "size_mb": self._get_repo_size_mb(),
            "file_count": self._count_files(),
            "extracted_at": datetime.now().isoformat(),
        }

    # 🆕 NEW HELPER METHOD 
    def _get_actual_repo_name(self) -> str:
        """
        Get actual repository name from Git remote or folder structure.
        Returns 'crewAI' not 'crewai_test'.
        """
        # 1. Try to get from git remote URL
        try:
            remote_url = self._run_git_command(["config", "--get", "remote.origin.url"])
            if remote_url:
                remote_url = remote_url.strip()
                # Extract repo name from URL
                # github.com/owner/repo.git -> repo
                if '/' in remote_url:
                    repo_name = remote_url.split('/')[-1]
                    if repo_name.endswith('.git'):
                        repo_name = repo_name[:-4]
                    return repo_name
        except Exception:
            pass
        
        # 2. Fallback: clean folder name
        folder_name = self.repo_path.name
        
        # Remove common suffixes
        for suffix in ['_test', '_copy', '_backup', '_temp', '_local']:
            if folder_name.lower().endswith(suffix.lower()):
                return folder_name[:-len(suffix)]
        
        return folder_name

    def extract_git_metadata(self) -> Dict:
        try:
            remote_url = self._run_git_command(
                ["config", "--get", "remote.origin.url"]
            )

            latest_commit = self._run_git_command(
                ["log", "-1", "--pretty=format:%H|%an|%ae|%ad|%s"]
            )
            commit_parts = latest_commit.split("|") if latest_commit else []

            branches_raw = self._run_git_command(["branch", "-a"])
            branch_list = (
                [
                    b.strip().replace("* ", "")
                    for b in branches_raw.split("\n")
                    if b.strip()
                ]
                if branches_raw
                else []
            )

            tags_raw = self._run_git_command(["tag", "-l"])
            tag_list = (
                [t.strip() for t in tags_raw.split("\n") if t.strip()]
                if tags_raw
                else []
            )

            current_branch = self._run_git_command(["branch", "--show-current"])

            return {
                "remote_url": remote_url or "",
                "branch": current_branch or "",
                "latest_commit": {
                    "hash": commit_parts[0] if len(commit_parts) > 0 else "",
                    "author": commit_parts[1] if len(commit_parts) > 1 else "",
                    "email": commit_parts[2] if len(commit_parts) > 2 else "",
                    "date": commit_parts[3] if len(commit_parts) > 3 else "",
                    "message": commit_parts[4] if len(commit_parts) > 4 else "",
                },
                "branch_count": len(branch_list),
                "branches": branch_list[:10],
                "tag_count": len(tag_list),
                "tags": tag_list[:10],
            }

        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------------------
    # Agentic detection
    # ---------------------------------------------------------------------

    def detect_agentic_frameworks(self) -> Dict:
        detected: Dict[str, str] = {}

        deps = self.extract_dependency_info()
        python_packages = deps.get("python_packages", [])

        for framework, keywords in self.AGENTIC_FRAMEWORKS.items():
            for package in python_packages:
                if any(k in package.lower() for k in keywords):
                    detected[framework] = "dependency"
                    break
            else:
                if self._scan_for_framework(keywords):
                    detected[framework] = "usage"

        if self._has_agent_patterns():
            detected["custom_agents"] = "implementation"

        return detected

    def _scan_for_framework(self, keywords: List[str]) -> bool:
        python_files = list(self.repo_path.rglob("*.py"))[:50]

        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()

                if any(f"import {k}" in content or f"from {k}" in content for k in keywords):
                    return True

                if any(re.search(rf"class.*{k}", content) for k in keywords):
                    return True

            except Exception:
                continue

        return False

    def _has_agent_patterns(self) -> bool:
        patterns = [
            r"class.*Agent",
            r"def.*agent",
            r"class.*Tool",
            r"def.*tool",
            r"class.*Workflow",
            r"def.*workflow",
            r"class.*Orchestrator",
            r"def.*orchestrator",
            r"@tool",
            r"@agent",
            r"@workflow",
        ]

        python_files = list(self.repo_path.rglob("*.py"))[:20]

        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if any(re.search(p, content, re.IGNORECASE) for p in patterns):
                    return True
            except Exception:
                continue

        return False

    # ---------------------------------------------------------------------
    # Dependencies
    # ---------------------------------------------------------------------

    def extract_dependency_info(self) -> Dict:
        deps = {
            "python_packages": [],
            "nodejs_packages": [],
            "docker": False,
            "other_dependencies": [],
        }

        req_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Pipfile",
            "environment.yml",
        ]

        for req_file in req_files:
            path = self.repo_path / req_file
            if path.exists():
                try:
                    deps["python_packages"].extend(
                        self._parse_python_dependencies(path, req_file)
                    )
                except Exception as e:
                    print(f"⚠️ Error parsing {req_file}: {e}")

        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps["nodejs_packages"].extend(data.get("dependencies", {}).keys())
                deps["nodejs_packages"].extend(data.get("devDependencies", {}).keys())
            except Exception:
                pass

        deps["docker"] = any(
            (self.repo_path / f).exists()
            for f in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]
        )

        return deps

    def _parse_python_dependencies(self, path: Path, file_name: str) -> List[str]:
        packages: List[str] = []

        if file_name == "requirements.txt":
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = (
                        line.split("==")[0]
                        .split(">=")[0]
                        .split("<=")[0]
                        .split("~=")[0]
                        .strip()
                    )
                    if pkg and not pkg.startswith("-"):
                        packages.append(pkg)

        elif file_name == "pyproject.toml":
            import toml

            data = toml.load(path)
            deps = data.get("project", {}).get("dependencies", [])
            for d in deps:
                packages.append(d.split("==")[0].split(">=")[0].strip())

        return packages

    # ---------------------------------------------------------------------
    # Structure & utilities
    # ---------------------------------------------------------------------

    def extract_structure_info(self) -> Dict:
        structure = {
            "directories": [],
            "file_types": {},
            "has_agentic_structure": False,
        }

        for item in self.repo_path.iterdir():
            if item.is_dir() and item.name != ".git":
                structure["directories"].append(item.name)

        ext_count: Dict[str, int] = {}
        for f in self.repo_path.rglob("*"):
            if f.is_file():
                ext_count[f.suffix.lower()] = ext_count.get(f.suffix.lower(), 0) + 1

        structure["file_types"] = dict(
            sorted(ext_count.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        agentic_dirs = {
            "agent",
            "agents",
            "workflow",
            "workflows",
            "tool",
            "tools",
            "pipeline",
            "pipelines",
            "orchestrator",
        }

        structure["has_agentic_structure"] = any(
            any(k in d.lower() for k in agentic_dirs)
            for d in structure["directories"]
        )

        return structure

    def find_entry_points(self) -> List[str]:
        patterns = [
            "main.py",
            "app.py",
            "run.py",
            "cli.py",
            "server.py",
            "agent.py",
            "pipeline.py",
            "__main__.py",
        ]

        return [
            str(p.relative_to(self.repo_path))
            for pat in patterns
            for p in self.repo_path.rglob(pat)
        ][:5]

    def find_config_files(self) -> List[str]:
        patterns = [
            "config*.py",
            "settings*.py",
            ".env*",
            "*.toml",
            "*.yaml",
            "*.yml",
            "*.json",
            "*.cfg",
            "*.ini",
        ]

        files: List[str] = []
        for pat in patterns:
            for p in self.repo_path.rglob(pat):
                rel = str(p.relative_to(self.repo_path))
                if not any(x in rel for x in [".git", "__pycache__", "node_modules"]):
                    files.append(rel)

        return sorted(files)[:10]

    # ---------------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------------

    def _get_repo_size_mb(self) -> float:
        total = sum(
            f.stat().st_size for f in self.repo_path.rglob("*") if f.is_file()
        )
        return round(total / (1024 * 1024), 2)

    def _count_files(self) -> int:
        return sum(
            1
            for f in self.repo_path.rglob("*")
            if f.is_file() and ".git" not in str(f)
        )

    def _run_git_command(self, args: List[str]) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path)] + args,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip() or None
        except Exception:
            return None

