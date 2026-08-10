import networkx as nx
from .models import DatabaseSchema, Relationship, RetrievalResult

class SchemaRetriever:
    """Retrieve schema information from a DatabaseSchema object."""

    def _normalize_identifier(self, value: str) -> str:
        return value.lower().replace("_", " ")


    def _identifier_tokens(self, value: str) -> list[str]:
        stopwords = {"in", "of", "the"}

        return [
            token
            for token in self._normalize_identifier(value).split()
            if token not in stopwords
        ]


    def _matches_identifier(
        self,
        identifier: str,
        question_lower: str,
        question_normalized: str,
    ) -> bool:
        identifier_lower = identifier.lower()
        identifier_normalized = self._normalize_identifier(identifier)

        if identifier_lower in question_lower:
            return True

        if identifier_normalized in question_normalized:
            return True

        tokens = self._identifier_tokens(identifier)

        return (
            len(tokens) > 1
            and all(token in question_normalized for token in tokens)
        )

    def _normalize_identifier(self, value: str) -> str:
        return value.lower().replace("_", " ")

    def retrieve(
        self,
        question: str,
        schema: DatabaseSchema,
        graph: nx.MultiDiGraph,
        max_hops: int = 1,
        extra_tables: set[str] | None = None,
    ) -> RetrievalResult:
        """Return table names and relationships relevant to the question."""
        if max_hops < 0:
            raise ValueError("max_hops must be non-negative")
        
        question_lower = question.lower()
        question_normalized = self._normalize_identifier(question)

        relevant_tables = set()
        relevant_columns = set()

        for table in schema:
            table_name = table.name.lower()
            table_normalized = self._normalize_identifier(table.name)

            table_matches = (
                self._matches_identifier(
                    table.name,
                    question_lower,
                    question_normalized,
                )
                or (
                    table.name.lower().endswith("s")
                    and table.name.lower()[:-1] in question_lower
                )
            )

            column_matches = any(
                self._matches_identifier(
                    column.name,
                    question_lower,
                    question_normalized,
                )
                for column in table.columns
            )

            if table_matches or column_matches:
                relevant_tables.add(table.name)

            for column in table.columns:
                if self._matches_identifier(
                    column.name,
                    question_lower,
                    question_normalized,
                ):
                    relevant_tables.add(table.name)
                    relevant_columns.add(
                        f"{table.name}.{column.name}"
                    )
        # Additional semantic seeds.
        if extra_tables:
            relevant_tables.update(extra_tables)

        # Include bridge tables on shortest FK paths between
        # independently matched tables.
        seed_tables = set(relevant_tables)

        if len(seed_tables) > 1:
            fk_graph = nx.Graph()

            for source, target, edge_data in graph.edges(data=True):
                if edge_data.get("relationship") == "FOREIGN_KEY":
                    fk_graph.add_edge(source, target)

            seed_list = list(seed_tables)

            for index, source in enumerate(seed_list):
                for target in seed_list[index + 1:]:
                    try:
                        path = nx.shortest_path(
                            fk_graph,
                            source=source,
                            target=target,
                        )
                    except (
                        nx.NetworkXNoPath,
                        nx.NodeNotFound,
                    ):
                        continue

                    relevant_tables.update(path)

        tables_to_visit = set(relevant_tables)
        for _ in range(max_hops):
            next_tables = set()
            for table in tables_to_visit:
                for _, target, edge_data in graph.out_edges(
                    table,
                    data=True,
                ):
                    if edge_data.get("relationship") == "FOREIGN_KEY":
                        next_tables.add(target)
                # Also follow incoming FK edges.
                for source, _, edge_data in graph.in_edges(
                    table,
                    data=True,
                ):
                    if edge_data.get("relationship") == "FOREIGN_KEY":
                        next_tables.add(source)

            next_tables.difference_update(relevant_tables)
            relevant_tables.update(next_tables)
            tables_to_visit = next_tables

            if not tables_to_visit:
                break

        relationships: list[Relationship] = []
        for source_table in relevant_tables:
            for target_table in graph.successors(source_table):
                if target_table not in relevant_tables:
                    continue
                edge_data = graph.get_edge_data(source_table, target_table)

                for edge in edge_data.values():
                    if edge.get("relationship") != "FOREIGN_KEY":
                        continue

                    relationships.append(
                        Relationship(
                            source_table=source_table,
                            target_table=target_table,
                            source_columns=edge["source_columns"],
                            target_columns=edge["target_columns"],
                        )
                    )

                    for source_column in edge["source_columns"]:
                        relevant_columns.add(
                            f"{source_table}.{source_column}"
                        )

                    for target_column in edge["target_columns"]:
                        relevant_columns.add(
                            f"{target_table}.{target_column}"
                        )
                
        return RetrievalResult(
            tables=relevant_tables,
            columns=relevant_columns,
            relationships=relationships,
        )