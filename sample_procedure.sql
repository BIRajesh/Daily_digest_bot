-- Sample procedure to record a new digest entry and return its ID

CREATE OR REPLACE PROCEDURE record_new_digest(
    p_team_name VARCHAR(100),
    p_summary_text TEXT,
    OUT p_digest_id INTEGER
)
LANGUAGE plpgsql
AS $$BEGIN
    -- Insert the new digest record
    INSERT INTO digest_records (digest_date, team_name, summary_text)
    VALUES (CURRENT_DATE, p_team_name, p_summary_text)
    RETURNING id INTO p_digest_id;
    
    -- Log the creation
    RAISE NOTICE 'Created new digest record with ID: %', p_digest_id;
END;$$;

-- Example procedure to update meeting attendance
CREATE OR REPLACE PROCEDURE update_meeting_attendance(
    p_meeting_id INTEGER,
    p_attendance_count INTEGER
)
LANGUAGE plpgsql
AS $$BEGIN
    UPDATE scrum_meetings
    SET attendance_count = p_attendance_count
    WHERE id = p_meeting_id;
    
    RAISE NOTICE 'Updated attendance for meeting ID: %', p_meeting_id;
END;$$;
