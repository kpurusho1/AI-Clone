-- Create organization table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_name TEXT NOT NULL UNIQUE,
    org_location TEXT,
    org_data TEXT,
    org_data_jsonb JSONB
);

-- Create Domain table with TEXT domain_name instead of enum
CREATE TABLE IF NOT EXISTS domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_name TEXT NOT NULL,
    expert_names TEXT[] DEFAULT '{}'::TEXT[],
    org_id UUID,
    CONSTRAINT fk_org
        FOREIGN KEY (org_id)
        REFERENCES organizations (id)
        ON DELETE SET NULL
);

-- Create Expert table
CREATE TABLE IF NOT EXISTS experts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domains TEXT [] DEFAULT '{}'::TEXT[],
    org_id UUID,
    context TEXT NOT NULL,
    CONSTRAINT fk_org
        FOREIGN KEY (org_id)
        REFERENCES organizations (id)
        ON DELETE SET NULL
);

-- Create Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    document_link TEXT NOT NULL,
    owner_id UUID NOT NULL,
    openai_file_id TEXT,
    storage_path TEXT
);

-- Create clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name TEXT NOT NULL,
    client_data TEXT,
    org_id UUID,
    expert_id UUID,
    org_client_id int,
    client_data_jsonb JSONB,
    CONSTRAINT fk_org
        FOREIGN KEY (org_id)
        REFERENCES organizations (id)
        ON DELETE SET NULL,
    CONSTRAINT fk_expert
        FOREIGN KEY (expert_id)
        REFERENCES experts (id)
        ON DELETE SET NULL
);

-- Create Vector Stores table to track vector stores and their associated files
CREATE TABLE IF NOT EXISTS vector_stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vector_id TEXT NOT NULL UNIQUE,
    vector_name TEXT,
    org_id UUID,
    org_name TEXT,
    domain_id UUID,
    domain_name TEXT,
    expert_id UUID,
    expert_name TEXT,
    client_id UUID,
    client_name TEXT,
    file_ids TEXT[] DEFAULT '{}'::TEXT[],
    batch_ids TEXT[] DEFAULT '{}'::TEXT[],
    latest_batch_id TEXT,
    owner TEXT,  -- 'organization', 'domain', 'expert', or 'client'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create helper functions for array operations
-- Function to concatenate two arrays
CREATE OR REPLACE FUNCTION array_concat(arr1 anyarray, arr2 anyarray)
RETURNS anyarray AS $$
BEGIN
    RETURN arr1 || arr2;
END;
$$ LANGUAGE plpgsql;

-- Function to append an element to an array
CREATE OR REPLACE FUNCTION array_append(arr anyarray, element anyelement)
RETURNS anyarray AS $$
BEGIN
    RETURN array_append(arr, element);
END;
$$ LANGUAGE plpgsql;

-- Note: After running this SQL script, create a storage bucket named 'documents'
-- using the Supabase dashboard Storage section. This cannot be done via SQL.

-- Create Assistants table to track OpenAI assistants
CREATE TABLE IF NOT EXISTS assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assistant_id TEXT NOT NULL UNIQUE,
    expert_id UUID,
    memory_type TEXT NOT NULL,
    vector_name TEXT,
    org_id UUID,
    domain_name TEXT,
    client_id UUID,
    vector_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance on vector_stores table
CREATE INDEX IF NOT EXISTS idx_vector_stores_org_id ON vector_stores (org_id);
CREATE INDEX IF NOT EXISTS idx_vector_stores_domain_id ON vector_stores (domain_id);
CREATE INDEX IF NOT EXISTS idx_vector_stores_expert_id ON vector_stores (expert_id);
CREATE INDEX IF NOT EXISTS idx_vector_stores_client_id ON vector_stores (client_id);
