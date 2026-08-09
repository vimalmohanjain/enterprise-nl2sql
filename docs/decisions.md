Architecture Decision Records (ADRs

ADR-001
    DatabaseSchema is the central domain model.
Reason:
    Independent of sqlglot
    Independent of NetworkX
    Independent of LLMs

ADR-002
    Foreign keys store names instead of object references.
Reason:
    Easier serialization
    Simpler testing
    Avoids circular references
    Graph builder resolves references later

ADR-003
    Parser uses an extractor pipeline.
Reason:
    Open/Closed Principle
    Easy extensibility
    Cleaner parser

ADR-004
    SchemaGraph is built from DatabaseSchema rather than directly from SQL/sqlglot.

Reason:
    Keeps the graph independent of SQL parsing.
    Allows the parser and graph builder to evolve independently.
    Provides a clean boundary between schema extraction and graph construction.

ADR-005
    NetworkX is used for the initial schema graph implementation.

Reason:
    Simple Python API.
    Supports graph traversal required by the retrieval layer.
    Mature graph algorithms.
    Easy to inspect and test.
    Avoids introducing a graph database before it is necessary.

### Training Schema Context Strategy

Training examples use the complete database schema whenever the
formatted example fits within the configured sequence length.

For oversized examples, the schema is pruned using tables referenced
by the gold SQL. This is restricted to supervised training-data
preparation.

Inference-time schema selection continues to use the schema retriever
and never has access to gold SQL.

This hybrid approach preserves full schema information for most
examples while preventing truncation of large-schema training records.

ADR-006
BIRD schemas are converted into the existing DatabaseSchema domain
model.

Reason:
Avoids maintaining a second schema representation for training.
Allows parsing, graph construction, prompt generation, and training
to share the same domain objects.
Keeps BIRD-specific logic at the dataset boundary.

ADR-007
Training uses full schemas when they fit within the token budget and
gold-SQL-based pruning only for oversized examples.

Reason:
Preserves maximum schema information for most training records.
Prevents sequence truncation on large BIRD databases.
Gold SQL is available during supervised data preparation.
Gold SQL must never be used for inference-time schema selection.

ADR-008
Training and validation are split deterministically using seed 42.

Reason:
Makes experiments reproducible.
Allows the exact 942-example validation set to be reconstructed from
the original BIRD dataset.
Prevents accidental changes to the held-out evaluation population.

ADR-009
SQL response cleanup is shared between generic LLM inference and
adapter inference.

Reason:
Prevents different inference backends from applying different output
post-processing.
Makes baseline and fine-tuned evaluation more comparable.

ADR-010
BIRD execution evaluation resolves the SQLite database from db_id for
each example.

Reason:
BIRD contains multiple independent databases.
Execution accuracy is meaningful only when the prediction and gold
SQL execute against the correct database.
Keeping db_id in evaluation records makes this dependency explicit.

ADR-011
Held-out BIRD evaluation does not use gold-SQL schema pruning.

Reason:
Gold SQL is unavailable in a real NL2SQL request.
Using gold SQL to select evaluation schema would leak information
from the expected answer.
The initial held-out evaluation therefore uses the full BIRD schema.

ADR-012
The first QLoRA experiment is evaluated after one epoch before
additional epochs are run.

Reason:
Training loss alone does not establish NL2SQL generalization.
Additional epochs may increase overfitting without improving
execution accuracy.
Held-out execution accuracy determines whether further training is
justified.