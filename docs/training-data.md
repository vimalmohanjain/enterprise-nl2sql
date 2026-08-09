# BIRD Training Data Pipeline

## 1. Objective

Prepare a real-world schema-aware NL2SQL dataset for QLoRA fine-tuning
of Qwen2.5-Coder-7B-Instruct.

## 2. BIRD Dataset Integration

Source files:
- train.json
- train_tables.json
- train_gold.sql
- train_databases.zip

Dataset validation:
- Training examples: 9,428
- Database schemas: 69
- Missing schemas: 0
- Successfully converted schemas: 69/69

## 3. BIRD Schema Conversion

BIRD schemas were converted into the project's internal DatabaseSchema
representation.

Special handling was required for composite primary keys.

Initial result:
- Successful: 30
- Failed: 39

Cause:
Some BIRD schemas represent primary keys as lists for composite keys.

After fixing composite-key handling:
- Successful: 69
- Failed: 0

## 4. Schema-Aware Training Format

Each BIRD example is transformed through:

BirdTrainingExample
    -> DatabaseSchema
    -> SchemaContext
    -> schema text
    -> TrainingFormatter
    -> QLoRA training record

PromptBuilder.build_schema_context() was introduced so training and
inference reuse the same schema representation.

Validated:
- Input examples: 9,428
- Formatted records: 9,428
- Empty records: 0

## 5. Initial Token-Length Analysis

Tokenizer:
Qwen/Qwen2.5-Coder-7B-Instruct

Full-schema results:

- Minimum: 102
- Median: 481
- P90: 1,103
- P95: 3,910
- P99: 3,976
- Maximum: 4,047

Threshold analysis:

- >1024: 1,153 (12.23%)
- >2048: 681 (7.22%)
- >4096: 0
- >8192: 0

Decision:
Keep max_seq_length=2048 rather than increasing all training examples
to 4096.

## 6. Schema Retrieval Coverage Experiment

The existing lexical + graph retriever was evaluated against tables
referenced by BIRD gold SQL.

Initial results:

- Full coverage: 4,922 (52.21%)
- Partial coverage: 2,788 (29.57%)
- Zero coverage: 1,718 (18.22%)

Investigation found that graph traversal followed only outgoing
foreign-key edges.

Example:

ratings.movie_id -> movies.movie_id

Starting from movies could therefore not discover ratings.

## 7. Bidirectional Retrieval Traversal

Retrieval graph expansion was changed to traverse both incoming and
outgoing FK edges while preserving the actual directed FK metadata.

After the change:

- Full coverage: 6,217 (65.94%)
- Partial coverage: 1,831 (19.42%)
- Zero coverage: 1,380 (14.64%)

This demonstrated a substantial improvement but also showed that the
lexical retriever is not reliable enough to prune supervised training
examples.

Examples include semantic mismatches such as:

    "film" -> movies

where the natural-language question contains no literal table or
column match.

Decision:
Do not use the runtime retriever to prune supervised BIRD training
contexts.

## 8. Conditional Gold-SQL Schema Pruning

Because gold SQL is available during supervised training, required
tables can be identified safely from the training label.

Strategy:

1. Build the full-schema training record.
2. Measure its token length.
3. If <= 2048 tokens, retain the full schema.
4. If > 2048 tokens, extract required tables from gold SQL.
5. Retain those tables and valid FK relationships.
6. Rebuild the training record.

Gold SQL is used only during training-data preparation and is not
available to or used by inference-time retrieval.

## 9. Final Token Profile

Records: 9,428
Records requiring pruning: 681

Before pruning:
- Median: 481
- P95: 3,910
- Maximum: 4,047

After conditional pruning:
- Median: 420
- P95: 1,024
- P99: 1,132
- Maximum: 1,239
- Records > 2048: 0

Result:
All BIRD training examples now fit comfortably within the planned
2048-token QLoRA sequence length.

## 10. BirdTrainingDatasetBuilder

A reusable BirdTrainingDatasetBuilder encapsulates the validated
pipeline:

BIRD example
    -> full schema context
    -> formatted training record
    -> token measurement
    -> conditional gold-SQL pruning
    -> final training record

Tests cover:
- Standard BIRD example formatting
- Full-schema context generation
- Oversized-schema pruning
- Preservation of gold-SQL tables
- Removal of unrelated tables

## 11. Current Status

Completed:
- BIRD ingestion
- 69/69 schema conversion
- 9,428 example/schema association
- schema-aware prompt formatting
- token profiling
- retrieval coverage analysis
- bidirectional graph traversal
- conditional schema pruning
- BirdTrainingDatasetBuilder

Next:
- deterministic train/validation split
- JSONL export
- QLoRA training on GPU
- adapter export
- fine-tuned evaluation
- comparison against baseline