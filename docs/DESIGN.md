# Design Notes

Architecture (logical):
- User/HR Portal → Document Upload Layer → OCR + LLM Processing → Data Normalization → Verification Engine → Fraud Detection + Risk Scoring → Human Review (if needed) → LLM Report Generation → HR Dashboard / System Integration

Business problem:
- Manual and fragmented background verification causes delays, high costs, inconsistent information, and increased fraud risk.

Proposed solution:
- Build an AI-driven platform that automates document processing, cross-verification, anomaly detection, and report generation using OCR, retrieval, and local/open-source models.

Business value:
- Reduce turnaround time from weeks to 1–3 days
- Lower costs by 30–50%
- Improve fraud detection and compliance readiness

Recommended approach:
- Hybrid AI + human review model
- Retrieval-Augmented Generation (RAG)
- Governance and compliance controls
- Phased rollout strategy

Components to implement:
- OCR pipeline
- Embeddings + Vector DB (RAG)
- Verification connectors (mocked)
- Fraud detection rules + ML
- Human review UI

Model usage policy:
- Use open-source models only.
- Prefer local inference setups rather than cloud-hosted APIs.
- For this prototype, keep model execution local to reduce data exposure and to support offline or low-latency use cases.
- For future LLM features such as summarization or verification explanations, Ollama is the preferred runtime.

Recommended tools for running models:
- Ollama (preferred for local LLM usage)
- Supported examples: Llama 3, Mistral, Phi-3, Gemma
- Sentence-transformers for local embedding generation and semantic retrieval

Model selection and justification:
- Current default embedding model: sentence-transformers/all-MiniLM-L6-v2
- Comparison model: sentence-transformers/all-mpnet-base-v2

| Criterion | MiniLM-L6-v2 | all-mpnet-base-v2 | Why it matters for this project |
|---|---:|---:|---|
| Approximate model size | Small (~80 MB) | Large (~400 MB+) | Smaller models are easier to run locally and fit lower-memory hardware |
| Embedding dimension | 384 | 768 | Lower dimension means faster search and lower memory use |
| Inference speed on CPU | Fast | Slower | Important for a lightweight prototype and local use |
| Memory footprint | Low | High | Better fit for laptops and edge/dev environments |
| Semantic quality | Good | Better | Higher quality is useful, but the smaller model is often sufficient for short document matching |
| Cost | Low | Higher | Local inference cost is effectively dominated by hardware usage |

Quantitative justification for the final selection:
- The selected MiniLM-L6-v2 model is roughly 5x smaller than mpnet-base-v2 and uses about half the embedding size, which directly improves latency and memory consumption.
- In practical local deployments, this usually translates to noticeably faster retrieval and lower compute requirements, which is beneficial for a prototype and for environments with limited GPU or CPU resources.
- The quality trade-off is acceptable for this use case because the system primarily needs good semantic matching over short extracted document text, not high-end generative reasoning.
- Therefore, MiniLM-L6-v2 is the best fit for the current project phase: strong enough for retrieval, much lighter to run, and aligned with the local/open-source policy.

Recommended production approach:
- Use the current MiniLM-L6-v2 model for retrieval and document similarity.
- If later the project needs richer summarization or reasoning, add Ollama with a local model such as Llama 3 or Phi-3 for report generation and explanation tasks.
