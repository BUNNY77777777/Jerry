-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'executive',
    google_tokens JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Context Threads Table
CREATE TABLE IF NOT EXISTS context_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Jerry Memory Table (with pgvector embedding - 768 dims for Gemini text-embedding-004 / embedding-001)
CREATE TABLE IF NOT EXISTS jerry_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    thread_id UUID REFERENCES context_threads(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL, -- e.g., 'fact', 'preference', 'decision', 'conversation'
    embedding VECTOR(768), -- 768 dimensions for Gemini embeddings
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Index for semantic vector search
CREATE INDEX IF NOT EXISTS jerry_memory_embedding_idx 
ON jerry_memory 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Stored procedure for cosine similarity vector search
CREATE OR REPLACE FUNCTION match_memories (
  query_embedding VECTOR(768),
  match_count INT DEFAULT 5,
  filter_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  thread_id UUID,
  content TEXT,
  memory_type TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    jm.id,
    jm.user_id,
    jm.thread_id,
    jm.content,
    jm.memory_type,
    jm.metadata,
    1 - (jm.embedding <=> query_embedding) AS similarity
  FROM jerry_memory jm
  WHERE (filter_user_id IS NULL OR jm.user_id = filter_user_id)
  ORDER BY jm.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 4. Commitments Table
CREATE TABLE IF NOT EXISTS commitments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
    priority TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    due_date TIMESTAMPTZ,
    assigned_to TEXT,
    source TEXT, -- e.g., 'email', 'meeting_notes', 'chat'
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 5. Approval Queue Table
CREATE TABLE IF NOT EXISTS approval_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL, -- e.g., 'send_email', 'schedule_calendar', 'execute_transaction'
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 6. Execution Audit Logs Table
CREATE TABLE IF NOT EXISTS execution_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approval_id UUID REFERENCES approval_queue(id) ON DELETE SET NULL,
    tool_name TEXT NOT NULL,
    input_parameters JSONB DEFAULT '{}'::jsonb,
    execution_result JSONB DEFAULT '{}'::jsonb,
    status TEXT NOT NULL, -- 'success', 'failure'
    error_message TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);
