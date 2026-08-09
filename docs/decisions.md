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