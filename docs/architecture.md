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