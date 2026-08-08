from .models import DatabaseSchema, DatasetExample


class DatasetGenerator:
    """Generate natural-language-to-SQL training examples."""

    def generate(self, schema: DatabaseSchema) -> list[DatasetExample]:
        examples = []

        for table in schema:
            # Example 1: select all rows
            examples.append(
                DatasetExample(
                    question=f"Show all {table.name}",
                    sql=f"SELECT * FROM {table.name}",
                )
            )

            # Example 2: select each column
            for column in table.columns:
                examples.append(
                    DatasetExample(
                        question=f"Show {column.name} from {table.name}",
                        sql=f"SELECT {column.name} FROM {table.name}",
                    )
                )

            # Example 3: select adjacent pairs of columns
            for index in range(len(table.columns) - 1):
                first_column = table.columns[index]
                second_column = table.columns[index + 1]

                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {first_column.name} "
                            f"and {second_column.name} "
                            f"from {table.name}"
                        ),
                        sql=(
                            f"SELECT {first_column.name}, "
                            f"{second_column.name} "
                            f"FROM {table.name}"
                        ),
                    )
                )

            # Example 4: simple numeric filter
            for column in table.columns:
                if column.data_type.upper() in {
                    "INT",
                    "INTEGER",
                    "REAL",
                    "FLOAT",
                    "DOUBLE",
                }:
                    examples.append(
                        DatasetExample(
                            question=(
                                f"Show {table.name} "
                                f"where {column.name} "
                                f"is greater than 50000"
                            ),
                            sql=(
                                f"SELECT * FROM {table.name} "
                                f"WHERE {column.name} > 50000"
                            ),
                        )
                    )

        # Example 5: foreign-key joins
        for table in schema:
            for foreign_key in table.foreign_keys:
                source_table = table.name
                target_table = foreign_key.target_table

                source_columns = foreign_key.source_columns
                target_columns = foreign_key.target_columns

                source_table_model = schema.get_table(source_table)
                target_table_model = schema.get_table(target_table)

                if source_table_model is None or target_table_model is None:
                    continue

                # Choose the first non-FK column from each table
                source_column = next(
                    (
                        column
                        for column in source_table_model.columns
                        if  ( 
                            column.name not in source_columns
                            and not column.is_primary_key 
                        )
                    ),
                    None,
                )

                target_column = next(
                    (
                        column
                        for column in target_table_model.columns
                        if (
                            column.name not in target_columns
                            and not column.is_primary_key
                        )
                    ),
                    None,
                )

                # Cannot create a useful SELECT if there are no
                # non-FK columns available.
                if source_column is None or target_column is None:
                    continue

                join_conditions = " AND ".join(
                    f"{source_table}.{source_name} = "
                    f"{target_table}.{target_name}"
                    for source_name, target_name in zip(
                        source_columns,
                        target_columns,
                    )
                )

                examples.append(
                    DatasetExample(
                        question=(
                            f"Show {source_table} and "
                            f"{target_table} information"
                        ),
                        sql=(
                            f"SELECT {source_table}.{source_column.name}, "
                            f"{target_table}.{target_column.name} "
                            f"FROM {source_table} "
                            f"JOIN {target_table} "
                            f"ON {join_conditions}"
                        ),
                    )
                )

        return examples