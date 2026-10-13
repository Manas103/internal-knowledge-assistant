-- One-time setup for the real pgvector path (assistant/vector_store.py).
-- Run once: sudo -u postgres psql -f scripts/pg_setup.sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'knowledge_app') THEN
    CREATE ROLE knowledge_app LOGIN PASSWORD 'knowledge_app';
  END IF;
END
$$;
