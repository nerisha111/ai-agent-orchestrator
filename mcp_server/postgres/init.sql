-- create leads table
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    source VARCHAR(255),
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


--create support_tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(50) DEFAULT 'medium',
    assigned_to VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--create the interactions table
--this table stores the timeline of events per lead/ticket
CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, 
    entity_id INT NOT NULL, 
    action VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--create the decision_log table
CREATE TABLE IF NOT EXISTS decision_log (
    id SERIAL PRIMARY KEY,
    trigger_source VARCHAR(100),
    raw_payload JSONB,
    classified_intent VARCHAR(255),
    confidence_score NUMERIC(3, 2),
    routing_action VARCHAR(100),
    escalated BOOLEAN DEFAULT FALSE,
    mcp_tool_calls JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

