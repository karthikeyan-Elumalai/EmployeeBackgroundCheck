# Model Selection Report

## 1. Project Context
This project is a prototype for an AI-powered employee background check workflow. The current implementation focuses on:
- document upload through a web API
- OCR-based text extraction
- semantic retrieval over extracted text

Because the project is intended to be local-first and open-source-friendly, model selection should favor small, local, and privacy-conscious options.

## 2. Model Usage Policy
- Use open-source models only.
- Prefer local inference setups such as Ollama or LM Studio.
- Keep sensitive employee data local where possible.
- Avoid external hosted APIs unless approved by the organization.

## 3. Recommended Runtime Tools
- Ollama for local LLM usage
- Supported example models: Llama 3, Mistral, Phi-3, Gemma
- Sentence-transformers for local embedding generation and semantic retrieval

## 4. Dataset Guidelines
Allowed data sources for this project:
- Public datasets such as Kaggle
- Hugging Face Datasets
- Synthetic or generated data where appropriate
- Open government datasets

Data handling expectations:
- Prefer datasets that are publicly available and legally reusable.
- For employee-related use cases, ensure compliance with privacy and consent requirements.
- If synthetic data is used, clearly document its origin and intended purpose.

## 5. Prompt Engineering / Optimization
For any LLM-based features, test multiple prompt strategies and record the outcome.

Suggested prompt strategies:
- Zero-shot prompting
- Few-shot prompting
- Chain-of-thought prompting (used carefully and only when appropriate)
- Role-based prompts such as Document: ...
- Prompt variations for the same task
- Comparison of observed improvements across variations

Expected outcome:
- Measure whether different prompts improve accuracy, clarity, or consistency.
- Keep a small prompt comparison table for the final report.

## 6. Candidate Models for Retrieval
The current retrieval task does not require full generative reasoning; it mainly needs good semantic similarity over short extracted document text.

### Candidate A: sentence-transformers/all-MiniLM-L6-v2
- Small embedding model
- Good balance of quality and speed
- Well-suited for local CPU inference

### Candidate B: sentence-transformers/all-mpnet-base-v2
- Stronger semantic quality
- Larger and heavier model
- More memory and CPU demand

## 5. Comparison Criteria

| Criterion | MiniLM-L6-v2 | all-mpnet-base-v2 | Notes |
|---|---:|---:|---|
| Approximate model size | Small (~80 MB) | Large (~400 MB+) | Smaller models are easier to run locally |
| Embedding dimension | 384 | 768 | Lower dimension improves search speed and lowers memory use |
| CPU inference speed | Fast | Slower | Important for lightweight local deployment |
| Memory footprint | Low | High | Better fit for laptops or low-resource environments |
| Semantic quality | Good | Better | Higher quality is useful, but the smaller model is often sufficient for short document matching |
| Cost | Low | Higher | Local inference cost is mainly hardware-driven |

## 6. Quantitative Justification for Final Selection
The recommended model for the current project phase is sentence-transformers/all-MiniLM-L6-v2.

Why this model is the best fit:
- It is roughly 5x smaller than all-mpnet-base-v2.
- It uses a much smaller embedding dimension (384 vs 768), which improves retrieval throughput and reduces memory usage.
- It is noticeably faster on CPU, which is important for a prototype and for local deployment on modest hardware.
- The quality trade-off is acceptable for this use case because the system mainly needs semantic matching over short extracted text rather than deep reasoning.

## 7. Final Recommendation
- Use sentence-transformers/all-MiniLM-L6-v2 for the current retrieval prototype.
- If the project later needs summarization, explanation generation, or richer language understanding, add a local LLM via Ollama such as Llama 3 or Phi-3.

## 8. Demo Requirements
The project should include either a live demo or a recorded walkthrough that clearly shows:
- Input → Output flow
- Model behavior
- Edge cases and failure handling

Suggested demo structure:
- Upload a sample document
- Show OCR extraction output
- Show retrieval or semantic matching results
- Highlight one edge case such as poor scan quality, missing fields, or ambiguous text

## 9. Documentation Deliverables
The final report should include the following sections:
1. Problem Statement
2. Dataset Source
3. Model Comparison
4. Selection Justification (with scoring)
5. Demo Results
6. Limitations and Future Work
7. Documentation of Prompts Used

## 10. Summary
For this project, the best model choice is the lighter, local-first, open-source option. MiniLM-L6-v2 provides a strong balance of speed, efficiency, and acceptable accuracy for retrieval tasks while staying aligned with the project’s model usage policy.
