# 🚀 CodeDL: The Agentic Code Retrieval Benchmark

Welcome to the **CodeDL Benchmark**! 

As Large Language Models rapidly shift software development towards **Agentic AI** frameworks via profound orchestration engines (like LangChain, LangGraph, AutoGen, and CrewAI), standard programmatic rules have fundamentally changed. Legacy general-purpose code retrieval benchmarks (such as CodeSearchNet) are built for standalone Javascript functions or Python sorting algorithms—they structurally **fail** to capture the deeply nested callback architectures and massive node routing logic unique to modern generative agents!

**CodeDL** solves this! We have engineered a totally automated, end-to-end framework specialized strictly for benchmarking, extracting, and accelerating Information Retrieval (IR) across Agentic structures via localized semantic mappings and native AST chunking engines.

🔗 **Try it live on Kaggle:** [CodeDL Complete Pipeline & Training Kernels](https://www.kaggle.com/code/shubharuidas/codedl)

---

## 🌟 Key Contributions & Breakthroughs

1. **RepoParser & The GenAI Corpus** 
   We built `RepoParser`, a Tree-sitter powered AST engine that eliminates catastrophic contextual code splits. This engine successfully mapped 5 bleeding-edge Agent frameworks into the pristine **5,000-pair GenAI Code Corpus**. 
2. **Astonishing MRL Dimensional Elasticity** 
   By injecting Matryoshka Representation Learning (MRL) into our Bi-Encoders, we successfully truncated baseline matrices from 768 to 128 dimensions. This didn't just save memory; it annihilated underlying structural noise scaling an enormous **84% footprint reduction directly matched with a +1.9% performance elevation on nDCG@10!**
3. **Cracking The "Semantic Chasm"**
   TctColBERT (and other massive Late-Interaction frameworks) are notoriously revered in conventional IR. However, on highly specialized Agentic logic, our hyper-lightweight Domain-Fine-Tuned Bi-Encoders completely overmatched them, throwing down a **+20.9% dominance leap**.
4. **Exposing the LLM Judge Rank Inversion**
   Never trust a generalist LLM operating code validation! We definitively proved that swapping a generalist Judge (Llama-8B) for an explicit code-aware Judge (Qwen-Coder-7B) resulted in staggering leaderboard inversions (Kendall-$\tau$ = 0.20 anomaly). Generalist Judges reward raw overlapping tokens; Specialized Judges validate true programmatic architectures!

---

## 📂 Core Navigation Matrix

Dive straight into the underlying engine. The absolute hierarchy is cleanly mapped directly across four principal ecosystems:

```shell
CodeDL/
├── data/
│   ├── synthetic/     # The ultimate 5,000 anchor-positive pair dataset generated across LangChain, AutoGen, CrewAI, etc.
│   └── processed/     # The raw, hierarchical AST chunk dictionaries exported natively by the RepoParser.
│
├── notebooks/
│   ├── codedl.ipynb                 # Phase 1-3 Engine: Triggers Depth-100 pooling, QWK LLM LLM evaluation, and standard baseline tracking.
│   ├── mrl_finetuning_codebert.ipynb# Active Training array injecting MultipleNegativesRankingLoss wrapped cleanly into Matryoshka configurations.
│   └── mrl_finetuning_dense.ipynb   # Constant testing array deploying semantic tunings tracking massive continuous gradient improvements.
│
├── repoparser/
│   ├── src/                         # The pure orchestration engine linking cross-repo crawling, syntactic chunking, and deterministic hashing.
│   ├── requirements.txt             # Targeted Python dependency grids mapping tree-sitter, PyTorch, and sentence-transformers.
│   └── README.md                    # Explicit initialization commands & venv deployment guides!
│
└── output/
    ├── *.csv                        # Pristine empirical evaluation datasets exporting system outcomes and specific benchmark limits.
    └── figures/                     # Active dimensional rendering plots detailing metric tracking natively matched to evaluation datasets.
```

## 🚀 Getting Started

If you want to view exactly how the deep-learning models train and compute the empirical benchmarks, head directly to our [Kaggle Notebook Execution](https://www.kaggle.com/code/shubharuidas/codedl). 

If you want to boot up the **RepoParser** locally to parse your own massive Agentic architectures into clean positive-pair datasets natively—fire up your terminal, navigate directly into `repoparser/`, and follow the dedicated initialization README!
