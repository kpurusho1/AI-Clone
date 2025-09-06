-- Create organization table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_name TEXT NOT NULL UNIQUE,
    location TEXT
);

-- Create clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name TEXT NOT NULL UNIQUE,
    client_data TEXT,
    client_data_jsonb JSONB
);

-- Alter vector_stores table to add new columns
ALTER TABLE vector_stores 
ADD COLUMN IF NOT EXISTS org_id UUID,
ADD COLUMN IF NOT EXISTS org_name TEXT,
ADD COLUMN IF NOT EXISTS domain_id UUID,
ADD COLUMN IF NOT EXISTS client_id UUID,
ADD COLUMN IF NOT EXISTS expert_id UUID;

-- Add foreign key constraints
ALTER TABLE vector_stores
ADD CONSTRAINT fk_org
    FOREIGN KEY (org_id)
    REFERENCES organizations (id)
    ON DELETE SET NULL;

ALTER TABLE vector_stores
ADD CONSTRAINT fk_domain_id
    FOREIGN KEY (domain_id)
    REFERENCES domains (id)
    ON DELETE SET NULL;

ALTER TABLE vector_stores
ADD CONSTRAINT fk_expert_id
    FOREIGN KEY (expert_id)
    REFERENCES experts (id)
    ON DELETE SET NULL;

ALTER TABLE vector_stores
ADD CONSTRAINT fk_client_id
    FOREIGN KEY (client_id)
    REFERENCES clients (id)
    ON DELETE SET NULL;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_vector_stores_org_id ON vector_stores (org_id);
CREATE INDEX IF NOT EXISTS idx_vector_stores_domain_id ON vector_stores (domain_id);
CREATE INDEX IF NOT EXISTS idx_vector_stores_expert_id ON vector_stores (expert_id);
CREATE INDEX IF NOT EXISTS idx_vector_stores_client_id ON vector_stores (client_id);
