"""PostgreSQL connection and schema management."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql

from src.common.config import PostgresConfig


class PostgresClient:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def connect(self, register_vector_type: bool = True) -> psycopg.Connection:
        password = os.environ.get(self.config.password_env, "proyecto02")
        connection = psycopg.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.user,
            password=password,
            autocommit=False,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SET search_path TO {}").format(
                    sql.Identifier(self.config.schema_name)
                )
            )
        if register_vector_type:
            register_vector(connection)
        return connection

    def apply_sql_directory(self, sql_dir: str | Path) -> None:
        paths = sorted(Path(sql_dir).glob("*.sql"))
        if not paths:
            raise FileNotFoundError(f"No SQL files found in: {sql_dir}")
        with self.connect(register_vector_type=False) as connection:
            with connection.cursor() as cursor:
                for path in paths:
                    cursor.execute(path.read_text(encoding="utf-8"))
            connection.commit()

    def fetch_counts(self, tables: Sequence[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        with self.connect() as connection:
            with connection.cursor() as cursor:
                for table in tables:
                    cursor.execute(
                        sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
                    )
                    counts[table] = int(cursor.fetchone()[0])
        return counts

    @staticmethod
    def execute_many(
        connection: psycopg.Connection,
        statement: str,
        rows: Iterable[Sequence[Any]],
    ) -> None:
        with connection.cursor() as cursor:
            cursor.executemany(statement, rows)
