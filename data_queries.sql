-- Query to get the most recent digest for a team
SELECT 
    dr.id,
    dr.digest_date,
    dr.summary_text,
    ga.pr_count,
    ga.commit_count,
    ja.ticket_count,
    ja.completed_count
FROM 
    digest_records dr
LEFT JOIN 
    github_activities ga ON dr.id = ga.digest_id
LEFT JOIN 
    jira_activities ja ON dr.id = ja.digest_id
WHERE 
    dr.team_name = 'YOUR_TEAM_NAME'
ORDER BY 
    dr.digest_date DESC
LIMIT 1;

-- Query to get upcoming scrum meetings
SELECT 
    id,
    meeting_date,
    team_name
FROM 
    scrum_meetings
WHERE 
    meeting_date > NOW()
    AND team_name = 'YOUR_TEAM_NAME'
ORDER BY 
    meeting_date
LIMIT 5;

-- Query to get team activity stats for the past week
SELECT 
    COUNT(DISTINCT dr.id) AS digest_count,
    SUM(ga.pr_count) AS total_prs,
    SUM(ga.commit_count) AS total_commits,
    SUM(ja.ticket_count) AS total_tickets,
    SUM(ja.completed_count) AS completed_tickets
FROM 
    digest_records dr
LEFT JOIN 
    github_activities ga ON dr.id = ga.digest_id
LEFT JOIN 
    jira_activities ja ON dr.id = ja.digest_id
WHERE 
    dr.digest_date >= CURRENT_DATE - INTERVAL '7 days'
    AND dr.team_name = 'YOUR_TEAM_NAME';
