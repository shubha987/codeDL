# Task 3 – Data Engineering

AST-based code chunking pipeline for Python and documentation files. Extracts semantically meaningful code chunks from local codebases and Git repositories, then generates positive pairs and triplets for embedding model fine-tuning.

---

## Directory Structure

```
src/task_3_data_engineering/
├── chunking/                        # All chunking strategies
│   ├── chunk_schema.py              # Core data schemas (CodeChunk, ChunkAST, ChunkHierarchy, ChunkSpan)
│   ├── ast_chunker.py               # Python AST-based chunker (primary authority layer)
│   ├── ts_chunker.py                # Tree-sitter chunker (byte-level span enrichment / fallback)
│   ├── hierarchical_chunker.py      # Coordinator: merges AST + Tree-sitter, builds hierarchy
│   ├── doc_chunker.py               # Markdown / RST documentation chunker
│   ├── repo_chunker.py              # Universal file-type dispatcher (routes to all chunkers)
│   └── hybrid_chunker.py            # ⚠️ Stub (commented out — logic moved to HierarchicalChunker)
│
├── ingestion/                       # Repository ingestion
│   ├── git_crawler.py               # Git clone, fast/rich/smart file listing, binary detection
│   └── repo_metadata.py             # Repository metadata & agentic framework detection
│
├── export/                          # Dataset export
│   ├── chunk_schema.py              # (imported from chunking/)
│   ├── jsonl_exporter.py            # Basic JSONL export (local codebases)
│   ├── enhanced_jsonl_exporter.py   # Enhanced JSONL export (Git repos + cross-file context)
│   ├── pairs_triplets_generator.py  # Positive pairs & triplets generator for training
│   ├── dataset_metadata.py          # Writes standardised dataset metadata JSON
│   ├── export_utils.py              # Shared export utilities
│   └── example_output.py            # Reference output examples
│
├── analysis/
│   └── dataset_stats.py             # Compute chunk-level statistics for quality assessment
│
├── utils/
│   └── id_utils.py                  # Deterministic SHA256-based chunk ID generation
│
├── metadata/                        # (Module placeholder — `__init__.py` only)
├── pipelines/                       # (Module placeholder — `__init__.py` only)
└── __init__.py
```

```

---

## Installation & Environment Setup

To ensure strict dependency mapping and prevent system conflicts, it is highly recommended to isolate RepoParser within a native Python virtual environment (`venv`).

```bash
# 1. Navigate to the repoparser directory
cd repoparser/

# 2. Initialize and activate the Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install required pipeline dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Basic Execution

Once the environment is active, you can interact securely through native execution layers:

```bash
# 1. To initialize raw AST repository chunking
# Define the framework bounds pointing to your target codebase:
python3 src/task_3_data_engineering/chunking/hierarchical_chunker.py \
    --input_dir path/to/local/langchain \
    --output processed/chunks.jsonl

# 2. To initialize semantic Pair Extraction & Triplet Negative Generation
# Evaluates chunk dictionaries and natively builds anchor-positive linkages applying algorithmic thresholds
python3 src/task_3_data_engineering/export/pairs_triplets_generator.py \
    --dataset processed/chunks.jsonl \
    --output data/synthetic/triplets.jsonl
```

---

## Architecture Overview

The pipeline has three distinct stages, each with clear module responsibilities:

```
Stage 1: Ingestion
  Git URL / Local Files
       │
       ▼
  git_crawler.py          ← Clone repo, list files (fast / rich / smart)
  repo_metadata.py        ← Extract git history, dependency info, agentic framework detection

Stage 2: Chunking
  File path
       │
       ├─ .py  ──────────► ast_chunker.py (semantic: modules, classes, functions, methods)
       │                    ts_chunker.py  (byte-level spans & fallback)
       │                    hierarchical_chunker.py (coordinates AST + Tree-sitter, builds parent-child tree)
       │
       ├─ .md/.rst ──────► doc_chunker.py (heading-aware, fenced code blocks, unfenced code recovery)
       │
       ├─ .json/yaml/toml ► repo_chunker.py (configuration chunker)
       │
       └─ other ─────────► repo_chunker.py (text chunker / binary detection / README handler)

       repo_chunker.py = universal dispatcher (routes ALL file types above)

Stage 3: Export
  List[CodeChunk]
       │
       ├─ Local files ──► jsonl_exporter.py         → chunks.jsonl
       ├─ Git repos ────► enhanced_jsonl_exporter.py → {name}_chunks.jsonl + repo_stats.json
       │
       └─ Training data ─► pairs_triplets_generator.py
                            → positive_pairs.jsonl / .json
                            → triplets.jsonl / .json
```

---

## Module Reference

### `chunking/chunk_schema.py`

Defines the core data types used throughout the entire pipeline.

| Class | Purpose |
|-------|---------|
| `CodeChunk` | Root dataclass: `chunk_id`, `file_path`, `language`, `chunk_type`, `code`, `ast`, `span`, `hierarchy`, `metadata` |
| `ChunkHierarchy` | Parent-child relationship: `parent_id`, `children_ids`, `depth`, `is_primary`, `lineage`, `sibling_index` |
| `ChunkAST` | AST metadata: `symbol_type`, `name`, `parent`, `docstring`, `decorators`, `imports`, `node_type` |
| `ChunkSpan` | Byte/line positions: `start_byte`, `end_byte`, `start_line`, `end_line`, `char_count` |

**Supported `ChunkType` values:**
`module`, `class`, `function`, `method`, `context`, `documentation`, `configuration`, `notebook`, `script`, `dockerfile`, `typescript`, `javascript`, `text`, `imports`, `unknown`

---

### `chunking/ast_chunker.py`

**Role:** Authority / Primary layer — the semantic source of truth.

Uses Python's built-in `ast` module to walk the parse tree and create semantically meaningful chunks.

**What it extracts:**
- `module` — entire file (root chunk, depth=0)
- `class` — class definitions (depth=1)
- `function` — top-level functions (depth=1)
- `method` — methods inside classes (depth=2)
- Async functions/methods handled identically to sync variants
- Decorators, imports, and docstrings per node
- Byte-level spans via line-to-byte conversion

**Public API:**
```python
from src.task_3_data_engineering.chunking.ast_chunker import extract_ast_chunks
chunks = extract_ast_chunks(Path("file.py"))
# Returns List[CodeChunk] with full hierarchy
```

**Key properties:**
- Deterministic chunk IDs (via `id_utils.deterministic_chunk_id`)
- Parent stack tracking for accurate `depth` and `lineage`
- Falls back gracefully via `SyntaxError` catch in `HierarchicalChunker`

---

### `chunking/ts_chunker.py`

**Role:** Enrichment / Fallback layer — byte-level precision.

Uses `tree-sitter` + `tree-sitter-python` to produce an alternative parse tree. Tree-sitter chunks are **not primary** (`is_primary=False`, `is_extracted=True`). Their sole purpose is to provide exact byte positions to AST chunks.

**Mapped node types:**
| Tree-sitter type | `ChunkType` |
|-----------------|-------------|
| `module` | `module` |
| `class_definition` | `class` |
| `function_definition` | `function` |
| `async_function_definition` | `function` |
| `import_statement` | `imports` |
| `import_from_statement` | `imports` |

**Public API:**
```python
from src.task_3_data_engineering.chunking.ts_chunker import extract_ts_chunks
chunks = extract_ts_chunks(Path("file.py"))
# Returns List[CodeChunk] — byte spans only, not primary
```

**Requirements:** `tree-sitter==0.25.2`, `tree-sitter-python==0.25.0`

---

### `chunking/hierarchical_chunker.py`

**Role:** Coordination layer — merges AST semantics with Tree-sitter byte precision.

**Processing steps for a single file:**
1. `extract_ast_chunks()` → semantic chunks with hierarchy
2. `extract_ts_chunks()` → byte-level span map
3. `_enrich_spans_with_tree_sitter()` → match by `(start_line, end_line)`, update `start_byte` / `end_byte`
4. `_update_hierarchy_relationships()` → resolve parent IDs from `(name, type)` pairs
5. `_preserve_hierarchy_relationships()` → fix any missing `children_ids` via full chunk map
6. Returns enriched + secondary chunks

**Public API:**
```python
from src.task_3_data_engineering.chunking.hierarchical_chunker import HierarchicalChunker
chunker = HierarchicalChunker()
chunks = chunker.chunk_file(Path("file.py"))
# Returns List[CodeChunk] — full AST hierarchy with correct byte spans
```

---

### `chunking/doc_chunker.py`

**Role:** Documentation chunker for Markdown, RST, and plain text.

**What it does:**
- Parses headings (`##` through `######`) to build a heading-context stack
- Detects fenced code blocks (` ``` `) and extracts them as `chunk_type="code"`
- Distinguishes actual executable code from formatted text inside fenced blocks (`_is_actual_code`)
- Recovers unfenced code blocks from prose via heuristics (`_looks_like_code_block`)
- Outputs `chunk_type="text"` for prose and `chunk_type="code"` for code blocks
- Each chunk carries `heading`, `heading_level`, `heading_path` metadata

**Key functions:**

| Function | Purpose |
|----------|---------|
| `chunk_document(raw_text, source_name, source_url)` | Main parsing function → `List[Dict]` |
| `wrap_doc_chunks(doc_chunks)` | Adapter: converts `List[Dict]` → `List[CodeChunk]` for pipeline compatibility |
| `_is_actual_code(text)` | Distinguishes real Python code from formatted fenced blocks |
| `_looks_like_code_block(lines)` | Heuristic for unfenced code recovery |
| `_looks_like_executable_code(text)` | Checks for Python execution patterns |

**Usage:**
```python
from src.task_3_data_engineering.chunking.doc_chunker import chunk_document, wrap_doc_chunks

raw = Path("README.md").read_text()
doc_chunks = chunk_document(raw, source_name="README.md", source_url=None)
code_chunks = wrap_doc_chunks(doc_chunks)
```

---

### `chunking/repo_chunker.py`

**Role:** Universal file-type dispatcher for full repository processing.

Routes every file to the appropriate specialised chunker based on file extension and filename, with fallback strategies.

**Routing table:**

| File type | Handler |
|-----------|---------|
| `.py` | `HierarchicalChunker` (AST + Tree-sitter) |
| `.md`, `.mdx`, `.rst` | `doc_chunker.chunk_document` |
| `.json` | JSON config chunker (pretty-prints + extracts top-level keys) |
| `.yaml`, `.yml`, `.toml` | Config chunker |
| `requirements.txt`, `Dockerfile`, `docker-compose.yml` | Special file chunker (extracts dependencies for requirements) |
| `.txt`, `.cfg`, `.ini`, `.conf` | Text chunker (splits files >200 lines into 100-line chunks) |
| `README`, `README.md`, `LICENSE` | Documentation chunker |
| Anything else | Binary detection → text chunker or skip |

All chunks receive `repo_metadata` injected into `metadata["repo_info"]`.

**Public API:**
```python
from src.task_3_data_engineering.chunking.repo_chunker import RepoChunker
chunker = RepoChunker(use_hierarchical=True)
chunks = chunker.chunk_file(Path("some_file.py"), repo_metadata={"repo_url": "..."})
```

**ID generation:** All IDs use deterministic SHA256 (`_generate_stable_id`) for reproducibility across runs.

---

### `chunking/hybrid_chunker.py`

⚠️ **Deprecated stub.** The content is entirely commented out. The hybrid logic (AST + Tree-sitter span merging) was moved and improved in `hierarchical_chunker.py`.

---

### `ingestion/git_crawler.py`

**Role:** Entry point for Git repository ingestion.

**Classes:**
- `RepoFileInfo` — lightweight dataclass: `path`, `relative_path`, `size`, `extension`, `is_binary`
- `GitCrawler` — main crawler class (default cache: `data/raw/repos/`)

**Listing strategies:**

| Method | Returns | Use when |
|--------|---------|----------|
| `list_files_fast(repo_path, extensions, exclude_dirs)` | `List[Path]` | Speed-critical; metadata not needed |
| `list_files_with_info(repo_path, extensions, skip_binary)` | `Tuple[List[RepoFileInfo], Dict stats]` | Full dataset building |
| `list_files(repo_path, rich_metadata=False/True)` | Either of the above | Auto-choose based on `rich_metadata` flag |

**Key methods:**

| Method | Purpose |
|--------|---------|
| `clone_repository(repo_url)` | `git clone --depth 1` (skip if already cloned) |
| `extract_enhanced_metadata(repo_path)` | Delegates to `RepoMetadataExtractor` |
| `get_readme_content(repo_path)` | Reads first 5,000 chars of README |
| `get_repo_stats(repo_path)` | File count, total size, extension breakdown (excludes `.git`) |
| `_is_binary_file(file_path)` | Samples 1,024 bytes; checks for null bytes + printable ratio |
| `cleanup_old_repos(max_age_days)` | Removes cached repos older than N days |

**Default excluded directories:** `.git`, `__pycache__`, `node_modules`, `build`, `dist`, `.venv`, `venv`, `.env`

**Usage:**
```python
from src.task_3_data_engineering.ingestion.git_crawler import GitCrawler

crawler = GitCrawler()
repo_path = crawler.clone_repository("https://github.com/langchain-ai/langchain")
file_infos, stats = crawler.list_files_with_info(repo_path, extensions={'.py', '.md'})
```

---

### `ingestion/repo_metadata.py`

**Role:** Deep metadata extraction with agentic framework detection.

**Class:** `RepoMetadataExtractor(repo_path)`

**`extract_comprehensive_metadata()` returns:**

| Key | Content |
|-----|---------|
| `basic` | Repo name (from git remote URL), local path, size (MB), file count, timestamp |
| `git` | Remote URL, current branch, latest commit (hash, author, date, message), branch list, tag list |
| `dependencies` | Python packages (from `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`), Node.js packages (`package.json`), Docker flag |
| `structure` | Top-level directory names, file type distribution (top 10), `has_agentic_structure` flag |
| `agentic_detection` | Dict of detected frameworks → detection method (`dependency` or `usage`) |
| `entry_points` | Paths matching `main.py`, `app.py`, `run.py`, `cli.py`, `agent.py`, etc. |
| `config_files` | Paths matching `*.yaml`, `*.toml`, `*.json`, `settings*.py`, etc. |

**Agentic frameworks detected:**

| Framework | Detection keywords |
|-----------|-------------------|
| `langchain` | `langchain`, `langsmith`, `lc`, `chain`, `agent` |
| `autogen` | `autogen`, `agent`, `groupchat` |
| `crewai` | `crewai`, `crew`, `task`, `agent` |
| `haystack` | `haystack`, `pipeline`, `node` |
| `llamaindex` | `llama_index`, `query_engine`, `index` |
| `semantic_kernel` | `semantic_kernel`, `sk` |
| `agents` | `agent`, `tool`, `workflow`, `orchestrator` |

Detection checks: Python package dependencies first, then `import` statements in `.py` files, then class/def patterns (`class.*Agent`, `@tool`, `@workflow`, etc.).

---

### `export/jsonl_exporter.py`

**Role:** Basic JSONL export for local codebase chunks.

**When to use:** Processing local files via `run_python_pipeline.py`. No repository context.

**Output format per line:**
```json
{
  "chunk_id": "primary_a1b2c3d4",
  "file_path": "data/raw/codebases/crewai/agent.py",
  "language": "python",
  "chunk_type": "function",
  "code": "def run_agent(...):\n    ...",
  "ast": {"symbol_type": "function", "name": "run_agent", "parent": "module", "docstring": "...", "decorators": [], "imports": []},
  "span": {"start_byte": 100, "end_byte": 500, "start_line": 10, "end_line": 30},
  "hierarchy": {"parent_id": "...", "children_ids": [], "depth": 1, "is_primary": true, "is_extracted": false},
  "metadata": {}
}
```

**Public API:**
```python
from src.task_3_data_engineering.export.jsonl_exporter import export_chunks_jsonl
export_chunks_jsonl(chunks, Path("output/chunks.jsonl"), print_stats=True)
```

---

### `export/enhanced_jsonl_exporter.py`

**Role:** Repository-aware JSONL export with cross-file context.

**When to use:** Processing Git repositories via `run_repo_pipeline.py`.

**Adds to each chunk's `metadata`:**
- `repo_info.repository` — basic repo metadata (name, size, file count)
- `repo_info.git_info` — branch, latest commit details
- `repo_info.dependencies` — Python/Node packages and Docker flag
- `repo_info.structure` — top-level dirs and file type counts  
- `repo_info.processing_timestamp`
- `repository_context.similar_files` — up to 5 other files in the repo

**Also generates:** `{chunk_file_stem}_repo_stats.json` with chunk type / language / file type distributions.

**Public API:**
```python
from src.task_3_data_engineering.export.enhanced_jsonl_exporter import export_repo_chunks_jsonl
result = export_repo_chunks_jsonl(chunks, output_path, repo_metadata, print_stats=True)
# result: {"chunks_file": "...", "stats_file": "...", "total_chunks": N, ...}
```

---

### `export/pairs_triplets_generator.py`

**Role:** Generates training data (positive pairs + triplets) from chunks.

**Data structures:**

| Class | Fields |
|-------|--------|
| `PositivePair` | `document_id` (chunk_id), `variations` (List of anchor+positive), `framework` |
| `PositivePairVariation` | `anchor` (NL question), `positive` (code snippet) |
| `Triplet` | `document_id`, `anchor` (NL question), `positive` (relevant code), `negative` (different code), `framework` |

**Question generation:**

Templates are defined per `symbol_type` (`class`, `function`, `method`, `async_function`, `module`, `workflow`). Example templates for `function`:
- `"How does {name} function work in Python?"`
- `"What is the implementation of {name}?"`
- `"How to implement the {name} function?"`

`_infer_description()` generates fallback descriptions from code patterns when no docstring exists (detects `stategraph`, `agent`, `@tool`, `async`, `api`, `database`, etc.).

**Negative sample selection (`select_negative_sample`):**
Picks a chunk with low semantic keyword overlap (< 30% overlap on keywords like `agent`, `tool`, `graph`, `workflow`, `async`, etc.).

**Framework detection (`extract_framework`):**
Infers framework from file path (e.g. `data/raw/codebases/crewai/...` → `crewai`, `data/processed/repos/langgraph_20260116/...` → `langgraph`).

**Chunk filtering (`filter_valid_chunks`):**
- Skips chunks shorter than 50 characters
- Skips `imports`-type chunks and undocumented `module` chunks
- Skips `__init__.py` files with fewer than 100 characters

**Main entry point:**
```python
from src.task_3_data_engineering.export.pairs_triplets_generator import generate_pairs_and_triplets

pairs, triplets = generate_pairs_and_triplets(
    chunks_path=Path("data/processed/chunks/crewai/chunks.jsonl"),
    output_dir=Path("data/processed/training_crewai"),
    num_pairs=100,
    num_triplets=100,
    variance=5,          # 5 question variations per positive pair
    export_format="both" # "jsonl", "json", or "both"
)
```

**Output files:**
```
output_dir/
├── positive_pairs.jsonl   # One PositivePair per line (with variations list)
├── positive_pairs.json    # Same, as JSON array (easier inspection)
├── triplets.jsonl         # One Triplet per line (flat)
└── triplets.json          # Same, as JSON array
```

---

### `export/dataset_metadata.py`

**Role:** Writes a standardised `dataset_metadata.json` alongside every dataset.

**Output:**
```json
{
  "dataset_name": "crewai_local",
  "dataset_version": "v1",
  "created_at": "2026-02-24T00:00:00Z",
  "chunking_strategy": "pure_ast + tree_sitter_spans",
  "languages": ["python", "markdown"],
  "python_version": "3.11.0",
  "total_files": 42,
  "total_chunks": 1873
}
```

---

### `analysis/dataset_stats.py`

**Role:** Computes quality statistics for a list of `CodeChunk` objects.

**`compute_dataset_stats(chunks)` returns:**

| Key | Description |
|-----|-------------|
| `total_chunks` | Total number of chunks |
| `chunk_type_distribution` | `{type: count}` |
| `language_distribution` | `{language: count}` |
| `ast_symbol_distribution` | `{symbol_type: count}` |
| `docstring_coverage_ratio` | Fraction of chunks that have a docstring |
| `average_code_length_chars` | Mean character count per chunk |

Used by both `jsonl_exporter.py` (print_stats) and `run_python_pipeline.py`.

---

### `utils/id_utils.py`

**Role:** Deterministic, content-aware chunk ID generation.

**Algorithm:** SHA256 of `file_path + chunk_type + name + parent + start_line + end_line + start_byte + end_byte + code`. First 8 hex chars are used as the readable ID.

**Format:** `primary_a1b2c3d4` (prefix defaults to `"primary"`)

**Properties:**
- Same input → same ID (reproducible across Python versions and OS)
- Code change → ID change (content-aware)
- Position change → ID change (line/byte-aware)
- Parent relationship → affects ID (hierarchical)

**Usage:**
```python
from src.task_3_data_engineering.utils.id_utils import deterministic_chunk_id

chunk_id = deterministic_chunk_id(
    file_path="src/agent.py",
    chunk_type="class",
    name="MyAgent",
    parent="module",
    start_line=10,
    end_line=50,
    code="class MyAgent:\n    ...",
)
# → "primary_a1b2c3d4"
```

---

## Data Flow (End-to-End)

### Local codebase → training data

```
data/raw/codebases/{framework}/    (place files here)
         │
    run_python_pipeline.py
    python -m scripts.run_python_pipeline --name crewai_local --include crewai
         │
    HierarchicalChunker (Python) + doc_chunker (Markdown)
         │
    data/processed/chunks/crewai_local/
    ├── chunks.jsonl
    ├── dataset_stats.json
    └── dataset_metadata.json
         │
    run_pairs_triplets_pipeline.py
    python -m scripts.run_pairs_triplets_pipeline --chunks ... --output ...
         │
    data/processed/training_crewai/
    ├── positive_pairs.jsonl / .json
    └── triplets.jsonl / .json
```

### Git repository → training data

```
GitHub URL
         │
    run_repo_pipeline.py
    python -m scripts.run_repo_pipeline single <url> --name langchain_code
         │
    GitCrawler.clone_repository()
    RepoMetadataExtractor.extract_comprehensive_metadata()
    RepoChunker.chunk_file() per file
    enhanced_jsonl_exporter.export_repo_chunks_jsonl()
         │
    data/processed/repos/langchain_code_{timestamp}/
    ├── langchain_code_chunks.jsonl
    ├── repository_metadata.json
    ├── langchain_code_stats.json
    └── langchain_code_chunks_repo_stats.json
         │
    run_pairs_triplets_pipeline.py
         │
    data/processed/training_langchain/
    ├── positive_pairs.jsonl / .json
    └── triplets.jsonl / .json
```

---

## Running the Pipeline

```bash
# Step 1A: Clone + chunk a Git repo
python -m scripts.run_repo_pipeline single https://github.com/langchain-ai/langchain \
    --name langchain_code --extensions .py

# Step 1B: Chunk a local codebase
python -m scripts.run_python_pipeline --name crewai_local --include crewai

# Step 2: Generate training pairs and triplets
python -m scripts.run_pairs_triplets_pipeline \
    --chunks data/processed/chunks/crewai_local/chunks.jsonl \
    --output data/processed/training_crewai \
    --pairs 200 --triplets 200 --variance 5

# Process all discovered chunk files at once
python scripts/generate_all_frameworks.py

# Run the test suite
pytest testing/ -v
```

---

## Testing

Tests for this module live in `testing/`:

| Test file | Covers |
|-----------|--------|
| `test_chunking.py` | `ASTChunker`, `doc_chunker`, `HierarchicalChunker` |
| `test_pipelines.py` | `run_python_pipeline`, `run_repo_pipeline` |
| `test_dataset_generation.py` | `pairs_triplets_generator` |
| `test_export.py` | `jsonl_exporter`, `enhanced_jsonl_exporter` |
| `test_data_quality.py` | Data integrity, chunk field completeness |
| `test_repo_chunker.py` | `RepoChunker` file-type routing |
| `test_repo_metadata_fix.py` | `RepoMetadataExtractor` regression tests |
| `test_all_id_generators_fixed.py` | `deterministic_chunk_id` consistency |
| `test_id_consistency.py` | Cross-chunk ID stability |
