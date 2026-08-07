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