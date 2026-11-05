# Evals

- `datasets/questions.jsonl`: 30-50 questions with known answers, one JSON object per line, for example
  `{"id": "storage-public-001", "question": "...", "expected": {...}, "scoring": "set_match", "tags": ["storage"]}`.
- `injection/`: prompt-injection cases, such as a resource tag that tries to redirect the agent.
- `run_evals.py`: runs the agent over the dataset, scores it, and writes a timestamped file to `results/`.

CI runs evals on every PR and fails if the pass rate drops below the committed baseline.
During eval development, tool responses are cached (`OPSAGENT_TOOL_CACHE_DIR`) and routine runs use a smaller model.
