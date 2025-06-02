-- Database schema for GenAI Daily Digest Bot

-- Team Members Table
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    github_username VARCHAR(50),
    jira_username VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily Digest Records
CREATE TABLE IF NOT EXISTS digest_records (
    id SERIAL PRIMARY KEY,
    digest_date DATE NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    summary_text TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE
);

-- GitHub Activity
CREATE TABLE IF NOT EXISTS github_activities (
    id SERIAL PRIMARY KEY,
    digest_id INTEGER REFERENCES digest_records(id),
    pr_count INTEGER DEFAULT 0,
    commit_count INTEGER DEFAULT 0,
    activity_data JSONB,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jira Activity
CREATE TABLE IF NOT EXISTS jira_activities (
    id SERIAL PRIMARY KEY,
    digest_id INTEGER REFERENCES digest_records(id),
    ticket_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    activity_data JSONB,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scrum Meetings
CREATE TABLE IF NOT EXISTS scrum_meetings (
    id SERIAL PRIMARY KEY,
    meeting_date TIMESTAMP NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    attendance_count INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
