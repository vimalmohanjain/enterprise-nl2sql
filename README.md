# enterprise-nl2sql
A research framework for enterprise Text-to-SQL using QLoRA, schema graphs, and execution-guided learning

                    Presentation Layer
                           │
                           ▼
                 EnterpriseNL2SQLPipeline
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    SchemaParser     GraphBuilder      PromptBuilder
                           │
                           ▼
                    Domain Model
                ┌──────────────────┐
                │  DatabaseSchema  │
                ├──────────────────┤
                │ Table            │
                │ Column           │
                │ ForeignKey       │
                │ Relationship     │
                └──────────────────┘
                           ▲
                           │
                    Parser Context
                ┌────────────────────┐
                │ CreateTableContext │
                └────────────────────┘



            Infrastructure Layer
        ┌─────────────────────────────┐
        │ sqlglot AST                 │
        └─────────────────────────────┘
                    │
                    ▼
              Parsing Layer
        ┌─────────────────────────────┐
        │ SchemaParser                │
        │ CreateTableContext          │
        └─────────────────────────────┘
                    │
                    ▼
               Domain Layer
        ┌─────────────────────────────┐
        │ DatabaseSchema              │
        │ Table                       │
        │ Column                      │
        │ ForeignKey                  │
        │ Relationship                │
        └─────────────────────────────┘