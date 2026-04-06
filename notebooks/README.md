# CodeDL Experimental Notebooks

This directory houses the three primary Jupyter computational notebooks executing the data-science tracking, deep representation training, and rigorous evaluation mapping governing the CodeDL benchmark.

## 📓 Notebook Breakdown

### 1. `codedl.ipynb` (Main Benchmark & Pipeline Evaluation)
**Purpose:** Executes the primary baseline benchmarking array, operating exactly across Phase 0 through Phase 3 CodeDL protocols.
*   **Phase 0A & 0B (Judge Calibration):** Runs candidate evaluators (Llama 8B vs Qwen Coder) sequentially against standard human-annotated `CodeSearchNet` test-splits computing precise Quadratic Weighted Kappa (QWK) limits.
*   **Phase 1 & Phase 2 (Pooling):** Initializes depth-100 pooling queries mapping over baseline lexicons (BM25), TctColBERT late interactions, and CodeBERT bounds, then dispatches the resulting union grid dynamically into the calibrated Qwen LLM for absolute 0-3 grading.
*   **Phase 3 (Benchmark Execution):** Tracks explicit `pyterrier_dr` mapping parameters rendering `rq1_table6.csv` output statistics.

### 2. `mrl_finetuning_codebert.ipynb` (MRL-LangChain Tuning)
**Purpose:** Trains a foundational Base Encoder utilizing Matryoshka Representation parameters explicitly.
*   **Initialization:** Ingests the generic `microsoft/codebert-base` pre-trained structure.
*   **Configuration:** Wraps standard isolated `MultipleNegativesRankingLoss` (MNRL) natively inside a rigorous nested `MatryoshkaLoss` configuration bounded utilizing dimensions: `{768, 512, 256, 128, 64}`.
*   **Deployment:** Evaluates lack of catastrophic breakdown against generic parameters, then actively uploads the tuned output model parameters dynamically to `shubharuidas/codebert-base-code-embed-mrl-[framework]`.

### 3. `mrl_finetuning_dense.ipynb` (MRL-Dense Incremental Tuning)
**Purpose:** Determines efficacy of chained / continuous dense fine-tuning.
*   **Initialization:** Ingests an actively pre-configured dense embedding logic frame (`shubharuidas/codebert-embed-base-dense-retriever`) mapping sentence-transformer alignment logic.
*   **Configuration:** Mirrors the nested dimensional clipping loops inside `MatryoshkaLoss`, observing training collapse boundaries and gradient tracking across accelerated hardware thresholds.
*   **Outcome:** Responsible for actively lifting the CSN general benchmark capability simultaneously from 0.823 to a striking 0.909 nDCG@10 mark alongside massive LangChain corpus retrieval boosts.
