"""Make ``Embedding.vector`` a real pgvector column on PostgreSQL.

0002 created the column as JSON on every database (it was generated on
SQLite). On PostgreSQL the vector store relies on pgvector operators and an
index, so convert the column, enable the extension and add an HNSW index for
cosine search. A no-op on other databases (SQLite keeps the JSON list and the
in-memory store).
"""
from django.conf import settings
from django.db import migrations


def _forwards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    dim = int(getattr(settings, "AI_CONFIG", {}).get("embedding_dim", 1536))
    table = schema_editor.quote_name("ai_embedding")
    cursor = schema_editor.connection.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cursor.execute(
        f"ALTER TABLE {table} ALTER COLUMN vector TYPE vector({dim}) "
        "USING (vector::text)::vector"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ai_embedding_vector_hnsw "
        f"ON {table} USING hnsw (vector vector_cosine_ops)"
    )


def _backwards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    table = schema_editor.quote_name("ai_embedding")
    cursor = schema_editor.connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS ai_embedding_vector_hnsw")
    cursor.execute(
        f"ALTER TABLE {table} ALTER COLUMN vector TYPE jsonb "
        "USING (vector::text)::jsonb"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0002_embeddings"),
    ]

    operations = [
        migrations.RunPython(_forwards, _backwards),
    ]
