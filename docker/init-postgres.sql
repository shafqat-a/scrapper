-- Initialize PostgreSQL database for Web Scrapper CLI
-- This script sets up the basic schema and indexes for optimal performance

-- Create extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create scraped_data table with JSONB for flexible schema
CREATE TABLE IF NOT EXISTS scraped_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    step_id VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_scraped_data_workflow_id ON scraped_data(workflow_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_step_id ON scraped_data(step_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_url ON scraped_data(url);
CREATE INDEX IF NOT EXISTS idx_scraped_data_created_at ON scraped_data(created_at);

-- Create GIN index on JSONB data for fast queries
CREATE INDEX IF NOT EXISTS idx_scraped_data_data_gin ON scraped_data USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_scraped_data_metadata_gin ON scraped_data USING GIN (metadata);

-- Create workflow_executions table for tracking workflow runs
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(255) NOT NULL,
    workflow_version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_metadata JSONB DEFAULT '{}',
    total_items_scraped INTEGER DEFAULT 0
);

-- Create indexes for workflow executions
CREATE INDEX IF NOT EXISTS idx_workflow_executions_name ON workflow_executions(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_started_at ON workflow_executions(started_at);

-- Create sample data for testing
INSERT INTO scraped_data (workflow_id, step_id, url, data, metadata) VALUES
('sample-workflow', 'init', 'https://example.com',
 '{"title": "Sample Page", "content": "This is sample content"}',
 '{"scraped_by": "web-scrapper-cli", "version": "1.0.0"}')
ON CONFLICT DO NOTHING;

-- Create a view for easy data querying
CREATE OR REPLACE VIEW scraped_items_view AS
SELECT
    id,
    workflow_id,
    step_id,
    url,
    data->>'title' as title,
    data->>'content' as content,
    jsonb_array_length(COALESCE(data->'links', '[]'::jsonb)) as links_count,
    metadata->>'scraped_by' as scraped_by,
    created_at
FROM scraped_data
ORDER BY created_at DESC;
