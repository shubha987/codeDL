"""
Positive Pairs and Triplets Generator for Training Data

This module generates positive pairs and triplets from code chunks for 
contrastive learning and similarity-based model training.

ARCHITECTURE POSITION:
    - Training Data Generator: Creates pairs/triplets from code chunks
    - Question Generator: Creates natural language queries for code
    - Variance Generator: Creates multiple variations of pairs

KEY FEATURES:
    1. Positive Pairs: (question, code) with 4-5 variations per sample
    2. Triplets: (anchor_question, positive_code, negative_code)
    3. Global ID tracking via chunk_id
    4. Supports code-to-question and question-to-code mappings

OUTPUT FORMATS:
    Positive Pairs:
    {
        "id": "pair_001",
        "global_id": "chunk_id",
        "anchor": "How to create a state graph with conditional edges?",
        "positive": "<code snippet>"
    }
    
    Triplets:
    {
        "id": "triplet_001",
        "global_id": "chunk_id", 
        "anchor": "How to create a reusable prompt template?",
        "positive": "<relevant code>",
        "negative": "<irrelevant code>"
    }

USAGE:
    from export.pairs_triplets_generator import generate_pairs_and_triplets
    
    pairs, triplets = generate_pairs_and_triplets(
        chunks_path="data/processed/chunks/chunks.jsonl",
        output_dir="data/processed/training",
        num_pairs=100,
        variance=5
    )
"""

import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class PositivePairVariation:
    """A single anchor-positive variation."""
    anchor: str       # Question (natural language query)
    positive: str     # Code snippet


@dataclass
class PositivePair:
    """A positive pair document with multiple anchor-positive variations.
    
    Format:
    {
        "document_id": "b8bcf898f9644fc3eb9946092f96ca7a9ba8e6ac",
        "variations": [
            {"anchor": "How does async aadd_documents work in Python?", "positive": "<code>"},
            {"anchor": "What is the implementation of aadd_documents?", "positive": "<code>"},
            {"anchor": "How to implement async aadd_documents?", "positive": "<code>"},
            {"anchor": "Show the async aadd_documents code", "positive": "<code>"},
            {"anchor": "Explain async aadd_documents function", "positive": "<code>"}
        ],
        "framework": "crewai"
    }
    """
    document_id: str                       # Original chunk_id
    variations: List[PositivePairVariation]  # List of (anchor, positive) pairs
    framework: str                         # Framework name from file path


@dataclass
class Triplet:
    """A triplet for contrastive learning.
    
    Format:
    {
        "document_id": "b8bcf898f9644fc3eb9946092f96ca7a9ba8e6ac",
        "anchor": "Best practices for async aadd_documents",
        "positive": "async def aadd_documents(...)",
        "negative": "async def async_agent(self):...",
        "framework": "crewai"
    }
    """
    document_id: str    # Original chunk_id
    anchor: str         # Question (natural language query)
    positive: str       # Relevant code snippet
    negative: str       # Irrelevant/different code snippet
    framework: str      # Framework name from file path


# Question templates for different code patterns - IMPROVED for cleaner questions
QUESTION_TEMPLATES = {
    "class": [
        "How does the {name} class work in Python?",
        "What is the implementation of the {name} class?",
        "How to create a {name} class?",
        "Show me the {name} class implementation",
        "Explain the {name} class structure",
    ],
    "function": [
        "How does {name} function work in Python?",
        "What is the implementation of {name}?",
        "How to implement the {name} function?",
        "Show the code for {name} function",
        "Explain how {name} works",
    ],
    "method": [
        "How does the {name} method work in Python?",
        "What is the implementation of {name} method?",
        "How to implement the {name} method?",
        "Show me the {name} method code",
        "Explain the {name} method",
    ],
    "async_function": [
        "How does async {name} work in Python?",
        "What is the async implementation of {name}?",
        "How to implement async {name}?",
        "Show the async {name} code",
        "Explain async {name} function",
    ],
    "module": [
        "How to implement {name} module?",
        "What's the structure of {name}?",
        "Show the {name} module implementation",
        "Explain the {name} module",
        "How does {name} module work?",
    ],
    "workflow": [
        "How to create a {name} workflow?",
        "What's the pattern for {name}?",
        "Show the {name} workflow implementation",
        "Explain the {name} workflow",
        "How does the {name} workflow work?",
    ],
}

# Variance templates to create multiple questions for the same code
VARIANCE_TEMPLATES = [
    "How to {action}?",
    "What's the code for {action}?",
    "Show me how to {action}",
    "Implement {action}",
    "Write code that {action}",
]


def extract_code_context(code: str, ast_info: Dict, file_path: str) -> Dict[str, str]:
    """Extract contextual information from code for question generation."""
    context = {
        "name": ast_info.get("name", "unknown"),
        "parent": ast_info.get("parent", ""),
        "symbol_type": ast_info.get("symbol_type", "unknown"),
        "docstring": ast_info.get("docstring", ""),
        "file_name": Path(file_path).stem if file_path else "unknown",
    }
    
    # Extract purpose/description from docstring or code patterns
    if context["docstring"]:
        # Use first sentence of docstring as description
        desc = context["docstring"].split(".")[0].strip()
        context["description"] = desc[:100] if len(desc) > 100 else desc
    else:
        # Generate description from code patterns
        context["description"] = _infer_description(code, context["name"])
    
    context["purpose"] = context["description"].lower()
    
    return context


def _infer_description(code: str, name: str) -> str:
    """Infer a description from code patterns when no docstring exists."""
    code_lower = code.lower()
    
    # Common patterns
    if "stategraph" in code_lower or "workflow" in code_lower:
        return f"building a stateful workflow"
    elif "agent" in code_lower:
        return f"creating an AI agent"
    elif "tool" in code_lower or "@tool" in code:
        return f"implementing a tool"
    elif "async" in code_lower:
        return f"async operations"
    elif "api" in code_lower or "request" in code_lower:
        return f"API interactions"
    elif "database" in code_lower or "sql" in code_lower:
        return f"database operations"
    elif "parse" in code_lower:
        return f"parsing data"
    elif "format" in code_lower:
        return f"formatting output"
    elif "template" in code_lower:
        return f"creating templates"
    elif "filter" in code_lower:
        return f"filtering data"
    elif "search" in code_lower:
        return f"search functionality"
    elif "create" in code_lower or "build" in code_lower:
        return f"building {name}"
    else:
        return f"implementing {name}"


def generate_question(code: str, ast_info: Dict, file_path: str, 
                     variation_index: int = 0) -> str:
    """Generate a clean natural language question for a code snippet."""
    name = ast_info.get("name", "unknown")
    symbol_type = ast_info.get("symbol_type", "function")
    
    # Clean up the name for display
    clean_name = name.replace("_", " ") if name else "this code"
    
    # Check if it's async
    is_async = code.strip().startswith("async ") or "async def" in code[:100]
    
    # Determine template category
    if is_async and symbol_type in ("function", "method"):
        template_category = "async_function"
    elif symbol_type in QUESTION_TEMPLATES:
        template_category = symbol_type
    elif "graph" in code.lower() or "workflow" in code.lower() or "state" in code.lower():
        template_category = "workflow"
    else:
        template_category = "function"
    
    templates = QUESTION_TEMPLATES[template_category]
    
    # Select template based on variation index
    template_idx = variation_index % len(templates)
    template = templates[template_idx]
    
    # Fill in template with clean name
    question = template.format(name=name)
    
    return question


def generate_question_variations(code: str, ast_info: Dict, file_path: str,
                                 num_variations: int = 5) -> List[str]:
    """Generate multiple unique question variations for a code snippet."""
    questions = []
    seen_questions = set()
    
    # Generate primary variations using templates
    for i in range(num_variations):
        q = generate_question(code, ast_info, file_path, variation_index=i)
        q_lower = q.lower()
        if q_lower not in seen_questions:
            questions.append(q)
            seen_questions.add(q_lower)
    
    # Return exactly num_variations (templates should provide enough)
    return questions[:num_variations]


def extract_framework(file_path: str) -> str:
    """Extract framework name from file path.
    
    Examples:
        'data/raw/codebases/crewai/...' -> 'crewai'
        'data/raw/codebases/langgraph/...' -> 'langgraph'
        'data/processed/repos/langgraph_20260116/...' -> 'langgraph'
    """
    path_lower = file_path.lower()
    
    # Known frameworks to detect
    frameworks = [
        "crewai", "langgraph", "langchain", "autogen", "llamaindex", 
        "dspy", "haystack", "semantic_kernel", "fastapi", "flask", "django"
    ]
    
    for framework in frameworks:
        if framework in path_lower:
            return framework
    
    # Try to extract from path structure
    parts = file_path.replace("\\", "/").split("/")
    for part in parts:
        if "codebases" in parts or "repos" in parts:
            # Get the next part after codebases/repos
            try:
                idx = parts.index("codebases") if "codebases" in parts else parts.index("repos")
                if idx + 1 < len(parts):
                    framework_part = parts[idx + 1].split("_")[0]  # Handle 'langgraph_20260116'
                    if framework_part and framework_part not in ["raw", "processed"]:
                        return framework_part
            except (ValueError, IndexError):
                pass
    
    return "unknown"


def is_semantically_different(chunk1: Dict, chunk2: Dict) -> bool:
    """Check if two chunks are semantically different (good for negative pairs)."""
    # Different symbol types
    type1 = chunk1.get("ast", {}).get("symbol_type", "")
    type2 = chunk2.get("ast", {}).get("symbol_type", "")
    
    # Different purposes (check for different keywords)
    code1 = chunk1.get("code", "").lower()
    code2 = chunk2.get("code", "").lower()
    
    # Keywords that indicate different functionality
    keywords = [
        "parse", "format", "create", "delete", "update", "read", "write",
        "input", "output", "agent", "tool", "graph", "state", "workflow",
        "template", "filter", "search", "database", "api", "async"
    ]
    
    keywords1 = set(k for k in keywords if k in code1)
    keywords2 = set(k for k in keywords if k in code2)
    
    # Consider different if keyword overlap is low
    if not keywords1 or not keywords2:
        return type1 != type2
    
    overlap = len(keywords1 & keywords2) / len(keywords1 | keywords2)
    return overlap < 0.3


def select_negative_sample(anchor_chunk: Dict, all_chunks: List[Dict], 
                          max_attempts: int = 50) -> Optional[Dict]:
    """Select a semantically different chunk as negative sample."""
    anchor_id = anchor_chunk.get("chunk_id", "")
    
    # Shuffle chunks for random selection
    candidates = [c for c in all_chunks if c.get("chunk_id") != anchor_id]
    random.shuffle(candidates)
    
    for candidate in candidates[:max_attempts]:
        if is_semantically_different(anchor_chunk, candidate):
            return candidate
    
    # Fallback: return any different chunk
    if candidates:
        return candidates[0]
    return None


def load_chunks(chunks_path: Path) -> List[Dict]:
    """Load chunks from JSONL file."""
    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return chunks


def filter_valid_chunks(chunks: List[Dict], min_code_length: int = 50) -> List[Dict]:
    """Filter chunks that are suitable for training pairs."""
    valid_chunks = []
    
    for chunk in chunks:
        code = chunk.get("code", "")
        chunk_type = chunk.get("chunk_type", "")
        ast_info = chunk.get("ast", {})
        
        # Skip empty or very short chunks
        if len(code) < min_code_length:
            continue
        
        # Skip pure imports or empty modules
        if chunk_type == "imports" or (chunk_type == "module" and not ast_info.get("docstring")):
            symbol_type = ast_info.get("symbol_type", "")
            if symbol_type == "imports":
                continue
        
        # Skip __init__ files without content
        if "__init__" in chunk.get("file_path", "") and len(code) < 100:
            continue
        
        valid_chunks.append(chunk)
    
    return valid_chunks


def generate_positive_pairs(chunks: List[Dict], num_pairs: int = 100,
                           variance: int = 5) -> List[PositivePair]:
    """
    Generate positive pairs from chunks with multiple (anchor, positive) variations per document.
    
    Output format:
    {
        "document_id": "b8bcf898f9644fc3eb9946092f96ca7a9ba8e6ac",
        "variations": [
            {"anchor": "How does async aadd_documents work in Python?", "positive": "<code>"},
            {"anchor": "What is the implementation of aadd_documents?", "positive": "<code>"},
            ...
        ],
        "framework": "crewai"
    }
    
    Args:
        chunks: List of code chunks
        num_pairs: Number of documents to generate (each with `variance` variations)
        variance: Number of (anchor, positive) variations per document (4-5 recommended)
    
    Returns:
        List of PositivePair objects (one per document, each with multiple variations)
    """
    pairs = []
    
    # Filter valid chunks
    valid_chunks = filter_valid_chunks(chunks)
    
    # Sample chunks if needed
    if len(valid_chunks) > num_pairs:
        selected_chunks = random.sample(valid_chunks, num_pairs)
    else:
        selected_chunks = valid_chunks
    
    for chunk in selected_chunks:
        code = chunk.get("code", "")
        ast_info = chunk.get("ast", {})
        file_path = chunk.get("file_path", "")
        document_id = chunk.get("chunk_id", "")
        
        # Extract framework from file path
        framework = extract_framework(file_path)
        
        # Generate multiple question variations
        anchors = generate_question_variations(code, ast_info, file_path, variance)
        
        # Create variations list with (anchor, positive) pairs
        variations = [
            PositivePairVariation(anchor=anchor, positive=code)
            for anchor in anchors
        ]
        
        pair = PositivePair(
            document_id=document_id,
            variations=variations,
            framework=framework
        )
        pairs.append(pair)
    
    return pairs


def generate_triplets(chunks: List[Dict], num_triplets: int = 100) -> List[Triplet]:
    """
    Generate triplets from chunks (no variations, flat structure).
    
    Output format:
    {
        "document_id": "b8bcf898f9644fc3eb9946092f96ca7a9ba8e6ac",
        "anchor": "Best practices for async aadd_documents",
        "positive": "async def aadd_documents(...)",
        "negative": "async def async_agent(self):...",
        "framework": "crewai"
    }
    
    Args:
        chunks: List of code chunks
        num_triplets: Number of triplets to generate (100, no variance)
    
    Returns:
        List of Triplet objects
    """
    triplets = []
    
    # Filter valid chunks
    valid_chunks = filter_valid_chunks(chunks)
    
    if len(valid_chunks) < 2:
        return triplets
    
    # Sample chunks if needed
    if len(valid_chunks) > num_triplets:
        selected_chunks = random.sample(valid_chunks, num_triplets)
    else:
        selected_chunks = valid_chunks
    
    for anchor_chunk in selected_chunks:
        # Find a semantically different chunk as negative
        negative_chunk = select_negative_sample(anchor_chunk, valid_chunks)
        
        if negative_chunk is None:
            continue
        
        code = anchor_chunk.get("code", "")
        ast_info = anchor_chunk.get("ast", {})
        file_path = anchor_chunk.get("file_path", "")
        document_id = anchor_chunk.get("chunk_id", "")
        
        # Extract framework from file path
        framework = extract_framework(file_path)
        
        # Generate question for anchor
        question = generate_question(code, ast_info, file_path)
        
        triplet = Triplet(
            document_id=document_id,
            anchor=question,
            positive=code,
            negative=negative_chunk.get("code", ""),
            framework=framework
        )
        triplets.append(triplet)
    
    return triplets


def export_pairs_jsonl(pairs: List[PositivePair], output_path: Path) -> None:
    """Export positive pairs to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")
    
    print(f"✅ Exported {len(pairs)} positive pairs to {output_path}")


def export_triplets_jsonl(triplets: List[Triplet], output_path: Path) -> None:
    """Export triplets to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for triplet in triplets:
            f.write(json.dumps(asdict(triplet), ensure_ascii=False) + "\n")
    
    print(f"✅ Exported {len(triplets)} triplets to {output_path}")


def export_pairs_json(pairs: List[PositivePair], output_path: Path) -> None:
    """Export positive pairs to JSON file (list format for easier inspection)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [asdict(p) for p in pairs]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(pairs)} positive pairs to {output_path}")


def export_triplets_json(triplets: List[Triplet], output_path: Path) -> None:
    """Export triplets to JSON file (flat list format)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [asdict(t) for t in triplets]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(triplets)} triplets to {output_path}")


def generate_pairs_and_triplets(
    chunks_path: Path,
    output_dir: Path,
    num_pairs: int = 100,
    num_triplets: int = 100,
    variance: int = 5,
    export_format: str = "both"  # "jsonl", "json", or "both"
) -> Tuple[List[PositivePair], List[Triplet]]:
    """
    Main function to generate positive pairs and triplets from chunks.
    
    Args:
        chunks_path: Path to chunks JSONL file
        output_dir: Directory to save output files
        num_pairs: Number of base pairs (will generate num_pairs * variance total)
        num_triplets: Number of triplets (no variance)
        variance: Number of variations per positive pair (4-5)
        export_format: Output format ("jsonl", "json", or "both")
    
    Returns:
        Tuple of (pairs, triplets)
    """
    print(f"📖 Loading chunks from {chunks_path}...")
    chunks = load_chunks(chunks_path)
    print(f"   Loaded {len(chunks)} chunks")
    
    # Generate positive pairs with variance
    print(f"\n🔄 Generating positive pairs (base={num_pairs}, variance={variance})...")
    pairs = generate_positive_pairs(chunks, num_pairs=num_pairs, variance=variance)
    print(f"   Generated {len(pairs)} positive pairs")
    
    # Generate triplets (no variance)
    print(f"\n🔄 Generating triplets (count={num_triplets})...")
    triplets = generate_triplets(chunks, num_triplets=num_triplets)
    print(f"   Generated {len(triplets)} triplets")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export based on format
    if export_format in ("jsonl", "both"):
        export_pairs_jsonl(pairs, output_dir / "positive_pairs.jsonl")
        export_triplets_jsonl(triplets, output_dir / "triplets.jsonl")
    
    if export_format in ("json", "both"):
        export_pairs_json(pairs, output_dir / "positive_pairs.json")
        export_triplets_json(triplets, output_dir / "triplets.json")
    
    # Print summary statistics
    print("\n📊 Summary Statistics:")
    print(f"   Total Positive Pair Documents: {len(pairs)}")
    print(f"   Total Variations: {sum(len(p.variations) for p in pairs)}")
    print(f"   Total Triplets: {len(triplets)}")
    
    return pairs, triplets


def main():
    """CLI entry point for generating pairs and triplets."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate positive pairs and triplets from code chunks")
    parser.add_argument("--chunks", "-c", type=str, required=True,
                       help="Path to chunks JSONL file")
    parser.add_argument("--output", "-o", type=str, required=True,
                       help="Output directory for generated files")
    parser.add_argument("--pairs", "-p", type=int, default=100,
                       help="Number of base positive pairs (default: 100)")
    parser.add_argument("--triplets", "-t", type=int, default=100,
                       help="Number of triplets (default: 100)")
    parser.add_argument("--variance", "-v", type=int, default=5,
                       help="Number of variations per pair (default: 5)")
    parser.add_argument("--format", "-f", type=str, default="both",
                       choices=["jsonl", "json", "both"],
                       help="Output format (default: both)")
    
    args = parser.parse_args()
    
    generate_pairs_and_triplets(
        chunks_path=Path(args.chunks),
        output_dir=Path(args.output),
        num_pairs=args.pairs,
        num_triplets=args.triplets,
        variance=args.variance,
        export_format=args.format
    )


if __name__ == "__main__":
    main()
