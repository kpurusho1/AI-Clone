-- Create Domain table with TEXT domain_name instead of enum
CREATE TABLE IF NOT EXISTS domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_name TEXT NOT NULL UNIQUE,
    expert_names TEXT[] DEFAULT '{}'::TEXT[]
);

-- Create Expert table
CREATE TABLE IF NOT EXISTS experts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    context TEXT NOT NULL,
    CONSTRAINT fk_domain
        FOREIGN KEY (domain)
        REFERENCES domains (domain_name)
        ON DELETE CASCADE
);

-- Create Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    document_link TEXT NOT NULL,
    created_by TEXT,
    domain TEXT NOT NULL,
    included_in_default BOOLEAN NOT NULL DEFAULT FALSE,
    client_name TEXT,
    openai_file_id TEXT,
    CONSTRAINT fk_domain
        FOREIGN KEY (domain)
        REFERENCES domains (domain_name)
        ON DELETE CASCADE
);

-- Insert default domain values
INSERT INTO domains (domain_name) VALUES
    ('AI education'),
    ('High School counseling'),
    ('Medical pediatrics');

-- Create Vector Stores table to track vector stores and their associated files
CREATE TABLE IF NOT EXISTS vector_stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vector_id TEXT NOT NULL UNIQUE,
    domain_name TEXT NOT NULL,
    expert_name TEXT,
    client_name TEXT,
    file_ids TEXT[] DEFAULT '{}'::TEXT[],
    batch_ids TEXT[] DEFAULT '{}'::TEXT[],
    latest_batch_id TEXT,
    owner TEXT NOT NULL,  -- 'domain', 'expert', or 'client'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_domain
        FOREIGN KEY (domain_name)
        REFERENCES domains (domain_name)
        ON DELETE CASCADE
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
    expert_name TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    client_name TEXT,
    vector_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_expert
        FOREIGN KEY (expert_name)
        REFERENCES experts (name)
        ON DELETE CASCADE
);
