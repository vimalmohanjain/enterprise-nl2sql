import re

import networkx as nx

from .models import DatabaseSchema, Relationship, RetrievalResult


class SchemaRetriever:
    """Retrieve schema information from a DatabaseSchema object."""

    def retrieve(
        self,
        question: str,
        schema: DatabaseSchema,
        graph: nx.MultiDiGraph,
        max_hops: int = 1,
        extra_tables: set[str] | None = None,
    ) -> RetrievalResult:
        result, _ = self.retrieve_with_diagnostics(
            question=question,
            schema=schema,
            graph=graph,
            max_hops=max_hops,
            extra_tables=extra_tables,
        )

        return result

    def retrieve_with_diagnostics(
        self,
        question: str,
        schema: DatabaseSchema,
        graph: nx.MultiDiGraph,
        max_hops: int = 1,
        extra_tables: set[str] | None = None,
    ) -> tuple[RetrievalResult, dict]:
        """Return retrieval result together with intermediate diagnostics."""

        if max_hops < 0:
            raise ValueError("max_hops must be non-negative")

        question_lower = question.lower()
        question_normalized = self._normalize_identifier(question)

        relevant_tables: set[str] = set()
        relevant_columns: set[str] = set()

        # ------------------------------------------------------------
        # 1. Lexical table / column matching
        # ------------------------------------------------------------
        for table in schema:
            table_name = table.name.lower()

            table_matches = (
                self._matches_identifier(
                    table.name,
                    question_lower,
                    question_normalized,
                )
                or (
                    table_name.endswith("s")
                    and self._matches_word(
                        table_name[:-1],
                        question_normalized,
                    )
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

        # Capture raw lexical matches before semantic seeds,
        # bridge expansion, or hop expansion.
        lexical_tables = set(relevant_tables)
        lexical_columns = set(relevant_columns)

        # ------------------------------------------------------------
        # 2. Add externally supplied semantic seed tables
        # ------------------------------------------------------------
        if extra_tables:
            for table_name in extra_tables:
                if schema.get_table(table_name) is not None:
                    relevant_tables.add(table_name)

        # ------------------------------------------------------------
        # 3. Include bridge tables on shortest FK paths
        #    between independently selected tables.
        # ------------------------------------------------------------
        seed_tables = set(relevant_tables)

        if len(seed_tables) > 1:
            fk_graph = nx.Graph()

            for source, target, edge_data in graph.edges(data=True):
                if edge_data.get("relationship") == "FOREIGN_KEY":
                    fk_graph.add_edge(source, target)

            seed_list = list(seed_tables)

            for index, source in enumerate(seed_list):
                for target in seed_list[index + 1 :]:
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

        # ------------------------------------------------------------
        # 4. Optional neighbourhood expansion
        # ------------------------------------------------------------
        tables_to_visit = set(relevant_tables)

        for _ in range(max_hops):
            next_tables: set[str] = set()

            for table in tables_to_visit:
                # Follow outgoing FK edges.
                for _, target, edge_data in graph.out_edges(
                    table,
                    data=True,
                ):
                    if edge_data.get("relationship") == "FOREIGN_KEY":
                        next_tables.add(target)

                # Follow incoming FK edges.
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

        # ------------------------------------------------------------
        # 5. Collect FK relationships between selected tables
        # ------------------------------------------------------------
        relationships: list[Relationship] = []

        for source_table in relevant_tables:
            for target_table in graph.successors(source_table):
                if target_table not in relevant_tables:
                    continue

                edge_data = graph.get_edge_data(
                    source_table,
                    target_table,
                )

                if not edge_data:
                    continue

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

        # ------------------------------------------------------------
        # 6. Build final result + diagnostics
        # ------------------------------------------------------------
        result = RetrievalResult(
            tables=relevant_tables,
            columns=relevant_columns,
            relationships=relationships,
        )

        diagnostics = {
            "lexical_tables": sorted(lexical_tables),
            "lexical_columns": sorted(lexical_columns),
            "extra_tables": sorted(extra_tables or set()),
            "final_tables": sorted(result.tables),
        }

        return result, diagnostics

    def _normalize_identifier(
        self,
        value: str,
    ) -> str:
        """Normalize schema identifiers and natural-language text."""
        normalized = value.lower().replace("_", " ")

        # Collapse repeated whitespace.
        return " ".join(normalized.split())

    def _identifier_tokens(
        self,
        value: str,
    ) -> list[str]:
        """Return meaningful tokens from a schema identifier."""

        stopwords = {
            "in",
            "of",
            "the",
        }

        return [
            token
            for token in self._normalize_identifier(value).split()
            if token not in stopwords
        ]

    def _matches_word(
        self,
        word: str,
        text: str,
    ) -> bool:
        """
        Match a schema word as a whole word.

        Supports simple singular/plural variation while deliberately
        rejecting tiny identifiers such as G, W, L, T and A.
        """

        word = word.lower()

        if len(word) < 3:
            return False

        # Exact whole-word match.
        if re.search(
            rf"\b{re.escape(word)}\b",
            text,
        ):
            return True

        # Simple singular -> plural:
        # name -> names
        # customer -> customers
        if not word.endswith("s"):
            if re.search(
                rf"\b{re.escape(word)}s\b",
                text,
            ):
                return True

        # Simple plural -> singular:
        # customers -> customer
        if word.endswith("s") and len(word) > 3:
            singular = word[:-1]

            if re.search(
                rf"\b{re.escape(singular)}\b",
                text,
            ):
                return True

        return False

    def _matches_identifier(
        self,
        identifier: str,
        question_lower: str,
        question_normalized: str,
    ) -> bool:
        """
        Match a schema identifier against natural-language text.

        Examples:
        - name -> "name" or "names"
        - opening_time -> "opening time"
        - sales_in_weather -> question containing both "sales" and "weather"

        Tiny identifiers such as G, W, L, T and A are intentionally
        ignored to prevent arbitrary substring matches.
        """

        del question_lower  # retained in signature for API compatibility

        identifier_normalized = self._normalize_identifier(
            identifier
        )

        if len(identifier_normalized) < 3:
            return False

        tokens = self._identifier_tokens(identifier)

        if not tokens:
            return False

        # Simple identifier.
        if len(tokens) == 1:
            return self._matches_word(
                tokens[0],
                question_normalized,
            )

        # Compound identifier.
        # Require every meaningful component to appear as a whole word.
        return all(
            self._matches_word(
                token,
                question_normalized,
            )
            for token in tokens
        )