-- GiHaNotis Database Schema
-- Crisis Resource Inventory Management System

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS activity_log CASCADE;
DROP TABLE IF EXISTS responses CASCADE;
DROP TABLE IF EXISTS requests CASCADE;

-- Table: requests
-- Stores admin-created requests for items needed during a crisis
CREATE TABLE requests (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    quantity_needed INTEGER NOT NULL CHECK (quantity_needed > 0),
    unit VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed'))
);

-- Table: responses
-- Stores user responses offering available resources
CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    responder_name VARCHAR(255),
    responder_contact VARCHAR(255),
    quantity_available INTEGER NOT NULL CHECK (quantity_available > 0),
    location VARCHAR(500) NOT NULL,
    notes TEXT,
    accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: activity_log
-- Stores audit trail of admin actions
CREATE TABLE activity_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    request_id INTEGER REFERENCES requests(id) ON DELETE CASCADE,
    response_id INTEGER REFERENCES responses(id) ON DELETE SET NULL,
    admin_username VARCHAR(255),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_responses_request_id ON responses(request_id);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX idx_activity_log_request_id ON activity_log(request_id);
CREATE INDEX idx_activity_log_created_at ON activity_log(created_at DESC);
CREATE INDEX idx_activity_log_action ON activity_log(action);

-- Comments for documentation
COMMENT ON TABLE requests IS 'Admin-created requests for resources needed during crisis';
COMMENT ON TABLE responses IS 'User responses offering available resources with location information';
COMMENT ON TABLE activity_log IS 'Audit trail of admin actions in the system';
COMMENT ON COLUMN requests.status IS 'Request status: open or closed';
COMMENT ON COLUMN responses.location IS 'Location where the resource is available';
COMMENT ON COLUMN responses.accepted IS 'Whether this response has been accepted by admin';
COMMENT ON COLUMN activity_log.action IS 'Type of action performed';
