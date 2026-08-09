SQL
 │
 ▼
SchemaParser
 │
 ▼
CreateTableContext
 │
 ▼
Extractor Pipeline
 │
 ├── ColumnExtractor
 ├── ColumnPrimaryKeyExtractor
 ├── TablePrimaryKeyExtractor
 └── ForeignKeyExtractor
 │
 ▼
DatabaseSchema
 │
 ▼
SchemaGraph
 │
 ▼
Retriever
 │
 ▼
Prompt Builder
 │
 ▼
LLM

DatabaseSchema
    │
    ├── Table
    │      ├── Column
    │      └── ForeignKey


DatabaseSchema                                                          
    │
    ├── employees
    │      ├── employee_id
    │      ├── department_id                           
    │      └── salary
    │
    └── departments
           ├── department_id
           └── name


employees
   │
   ├── HAS_COLUMN ─────► employee_id
   ├── HAS_COLUMN ─────► department_id
   ├── HAS_COLUMN ─────► salary
   │
   └── FOREIGN_KEY ────► departments

departments
   │
   └── HAS_COLUMN ─────► department_id


   Question:
"Show employee names and their department names"

                    Retriever
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
      employees                  departments
      ├─ name                    ├─ name
      └─ department_id            └─ department_id
                │
                └──── FK ──────────┘

RetrievalResult
├── tables
│   ├── employees
│   └── departments
└── relationships
    └── employees → departments

SchemaRetriever
      │
      ▼
RetrievalResult
   ├── tables
   └── relationships


## Training and Evaluation Architecture

The training pipeline extends the runtime NL2SQL architecture with
BIRD ingestion, schema-aware training-data preparation, QLoRA
fine-tuning, adapter inference, and held-out evaluation.

```text
BIRD Dataset
│
▼
BirdDatasetLoader
│
├── question
├── SQL
├── evidence
├── db_id
└── DatabaseSchema
│
▼
Training Schema Preparation
│
├── full schema when within token budget
└── gold-SQL-based pruning for oversized training examples
│
▼
TrainingFormatter
│
▼
Deterministic Train / Validation Split
│
├── Train      8,486
└── Validation   942
│
▼
QLoRA Training
│
├── Qwen2.5-Coder-7B-Instruct
├── 4-bit model loading
├── LoRA adapters
├── Unsloth
└── TRL SFTTrainer
│
▼
Saved Adapter
│
▼
AdapterInference
│
├── tokenize prompt
├── generate completion
├── remove prompt tokens
└── clean generated SQL
│
▼
BIRD Evaluation Pipeline
│
├── reconstruct deterministic validation split
├── build schema-aware prompt
├── generate SQL
├── normalized strict match
└── SQLite execution match
```

## BIRD Dataset Integration

`BirdDatasetLoader` converts BIRD metadata into the project's
domain model.

Each training example is represented as:

```text
BirdTrainingExample
├── db_id
├── question
├── SQL
├── evidence
└── DatabaseSchema
```

BIRD schemas are converted into the same `DatabaseSchema` model used
by the SQL parser and runtime retrieval pipeline. This prevents the
training pipeline from introducing a second schema representation.

The current BIRD training corpus contains:

| Item | Count |
| --- | ---: |
| Total examples | 9,428 |
| Training examples | 8,486 |
| Validation examples | 942 |

The split is deterministic and uses seed `42`.

## Schema Retrieval Coverage

Retrieval coverage was measured against the tables referenced by the
gold SQL across all 9,428 BIRD examples.

The initial retrieval implementation achieved:

| Metric | Result |
| --- | ---: |
| Full coverage | 4,922 (52.21%) |
| Partial coverage | 2,788 (29.57%) |
| Zero coverage | 1,718 (18.22%) |

After retrieval improvements:

| Metric | Result |
| --- | ---: |
| Full coverage | 6,217 (65.94%) |
| Partial coverage | 1,831 (19.42%) |
| Zero coverage | 1,380 (14.64%) |

This represents an improvement of **13.73 percentage points** in
full table coverage.

Retrieval remains an important source of potential inference errors,
so retrieval quality is measured independently from model quality.

## Training Schema Context Strategy

Training examples use the complete database schema whenever the
formatted example fits within the configured sequence length.

For oversized examples only, the training schema is pruned using
tables referenced by the gold SQL.

Gold SQL is used exclusively during supervised training-data
preparation and is never available during inference or held-out
evaluation.

Token profiling before pruning:

| Statistic | Tokens |
| --- | ---: |
| Median | 481 |
| P95 | 3,910 |
| Maximum | 4,047 |

Token profiling after pruning:

| Statistic | Tokens |
| --- | ---: |
| Median | 420 |
| P95 | 1,024 |
| P99 | 1,132 |
| Maximum | 1,239 |

681 of the 9,428 records required pruning.

After pruning, **zero training records exceed the 2,048-token
sequence limit**.

## QLoRA Fine-Tuning

The initial fine-tuning experiment uses:

```text
Base model:
Qwen/Qwen2.5-Coder-7B-Instruct

Method:
QLoRA

Model loading:
4-bit

LoRA rank:
16

LoRA alpha:
32

Target modules:
q_proj
k_proj
v_proj
o_proj
gate_proj
up_proj
down_proj

Sequence length:
2048

Effective batch size:
4 for the current Colab run

Training framework:
Unsloth + TRL
```

A 200-example smoke test was successfully completed before starting
the full training run.

The smoke test verified:

- Qwen model loading on a Tesla T4
- 4-bit loading
- LoRA adapter creation
- training-data tokenization
- TRL trainer construction
- gradient updates
- checkpoint creation
- adapter saving

LoRA dropout was subsequently changed from `0.05` to `0` so that
Unsloth could apply its optimized LoRA patching path.

The full first-epoch training run contains:

```text
Training examples:       8,486
Epochs:                       1
Effective batch size:         4
Training steps:           2,122
```

The first epoch is intentionally evaluated before deciding whether
additional epochs are useful.

## Adapter Inference

`AdapterInference` provides the inference boundary for a trained
adapter.

```text
prompt
│
▼
tokenizer
│
▼
model.generate()
│
▼
remove input/prompt tokens
│
▼
decode completion
│
▼
clean_sql()
│
▼
SQL
```

SQL cleanup is shared with `NL2SQLGenerator` through `clean_sql()`.
This prevents the baseline and fine-tuned inference paths from
implementing different response-cleaning rules.

## Held-Out BIRD Evaluation

The validation split is reconstructed from the original BIRD
examples using the same deterministic split configuration used
during training.

Each evaluation record preserves its database identity:

```text
BirdEvaluationExample
├── db_id
├── question
└── expected_sql
```

Evaluation uses:

```text
BirdEvaluationExample
│
▼
BirdPromptBuilder
│
├── load BIRD schema
├── convert to DatabaseSchema
├── build full SchemaContext
└── build model prompt
│
▼
AdapterInference
│
▼
predicted SQL
│
├───────────────┐
▼               ▼
Strict Match    Execution Match
                │
                ▼
        BirdDatabaseResolver
                │
                ▼
       <db_id>/<db_id>.sqlite
```

`BirdPromptBuilder` uses the complete schema during held-out
evaluation. It does not use gold SQL for schema pruning.

`BirdDatabaseResolver` maps each BIRD `db_id` to its corresponding
SQLite database so that execution accuracy is measured against the
correct database.

The evaluation pipeline reports both:

- normalized strict SQL accuracy
- SQLite execution accuracy

Execution accuracy remains the primary model-quality metric.