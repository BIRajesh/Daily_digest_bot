# Database Components for GenAI Daily Digest Bot

This directory contains SQL scripts for setting up and interacting with the database for the GenAI Daily Digest Bot.

## Files

- `schema.sql` - Defines the database tables and relationships
- `sample_procedure.sql` - Contains stored procedures for common operations
- `data_queries.sql` - Sample queries for retrieving digest and activity data

## Setup Instructions

1. Create a new database for the application
2. Run the `schema.sql` script to create the necessary tables
3. Run the `sample_procedure.sql` script to create stored procedures
4. Test with queries from `data_queries.sql`

## Integration with main.py

To integrate these database components with the main application:

1. Add a database connector in the `collectors` directory
2. Update `main.py` to call the database functions
3. Store database credentials securely in the `.env` file

## Database Schema Overview

- `team_members` - Information about team members
- `digest_records` - Record of each daily digest generated
- `github_activities` - GitHub data collected for each digest
- `jira_activities` - Jira data collected for each digest
- `scrum_meetings` - Schedule and attendance for scrum meetings
