-- Stored Procedure
CREATE OR REPLACE PROCEDURE sp_CalculateCandidateScore (p_application_id IN NUMBER)
IS
  v_candidate_id NUMBER := NULL;
  v_job_id NUMBER := NULL;
  v_job_skill_count NUMBER := 0;
  v_matched_count NUMBER := 0;
  v_skill_pct NUMBER(10,4) := 0;
  v_exp_score NUMBER(10,4) := 0;
  v_edu_score NUMBER(10,4) := 0;
  v_cand_years NUMBER := 0;
  v_job_min_years NUMBER := 0;
  v_final NUMBER(10,4) := 0;
BEGIN
  BEGIN
    SELECT candidate_id, job_id INTO v_candidate_id, v_job_id
    FROM Applications
    WHERE id = p_application_id;
  EXCEPTION WHEN NO_DATA_FOUND THEN
    RAISE_APPLICATION_ERROR(-20001, 'Application not found');
  END;

  SELECT COUNT(*) INTO v_job_skill_count FROM JobSkills WHERE job_id = v_job_id;

  IF v_job_skill_count = 0 THEN
    v_skill_pct := 100;
  ELSE
    SELECT COUNT(DISTINCT js.skill_id) INTO v_matched_count
    FROM JobSkills js
    INNER JOIN CandidateSkills cs
      ON cs.skill_id = js.skill_id AND cs.candidate_id = v_candidate_id
    WHERE js.job_id = v_job_id;
    v_skill_pct := (v_matched_count * 100.0) / v_job_skill_count;
  END IF;

  SELECT c.years_experience, j.min_years_experience
  INTO v_cand_years, v_job_min_years
  FROM Candidates c
  CROSS JOIN Jobs j
  WHERE c.id = v_candidate_id AND j.id = v_job_id;

  IF v_job_min_years IS NULL OR v_job_min_years = 0 THEN
    v_exp_score := 100;
  ELSE
    v_exp_score := LEAST(100, (v_cand_years * 100.0) / v_job_min_years);
  END IF;

  BEGIN
    SELECT el.score_weight INTO v_edu_score
    FROM Candidates c
    INNER JOIN EducationLevels el ON el.id = c.education_level_id
    WHERE c.id = v_candidate_id;
  EXCEPTION WHEN NO_DATA_FOUND THEN
    v_edu_score := 0;
  END;

  v_final := (0.50 * v_skill_pct) + (0.30 * v_exp_score) + (0.20 * v_edu_score);

  UPDATE Applications SET score = ROUND(v_final, 2) WHERE id = p_application_id;
END;
/

-- View: vw_RankedCandidates
CREATE OR REPLACE VIEW vw_RankedCandidates AS
SELECT
  a.id AS application_id,
  a.job_id,
  a.candidate_id,
  a.score,
  a.status AS application_status,
  u.full_name AS candidate_name,
  RANK() OVER (PARTITION BY a.job_id ORDER BY a.score DESC, a.id ASC) AS rank_position
FROM Applications a
INNER JOIN Candidates c ON c.id = a.candidate_id
INNER JOIN Users u ON u.id = c.user_id
/

-- View: vw_JobSummary
CREATE OR REPLACE VIEW vw_JobSummary AS
SELECT
  j.id AS job_id,
  j.title,
  j.recruiter_user_id,
  j.status AS job_status,
  COUNT(a.id) AS application_count,
  ROUND(NVL(AVG(a.score), 0), 2) AS average_score
FROM Jobs j
LEFT JOIN Applications a ON a.job_id = j.id
GROUP BY j.id, j.title, j.recruiter_user_id, j.status
/

-- View: vw_SkillGap
CREATE OR REPLACE VIEW vw_SkillGap AS
SELECT
  j.id AS job_id,
  js.skill_id,
  s.name AS skill_name,
  COUNT(DISTINCT CASE WHEN cs.skill_id IS NOT NULL THEN a.id END) AS applicants_with_skill,
  COUNT(DISTINCT a.id) AS total_applicants_for_job
FROM Jobs j
INNER JOIN JobSkills js ON js.job_id = j.id
INNER JOIN Skills s ON s.id = js.skill_id
LEFT JOIN Applications a ON a.job_id = j.id AND a.status = 'submitted'
LEFT JOIN CandidateSkills cs
  ON cs.candidate_id = a.candidate_id AND cs.skill_id = js.skill_id
GROUP BY j.id, js.skill_id, s.name
/

-- Trigger: tr_applications_status_audit
CREATE OR REPLACE TRIGGER tr_applications_status_audit
AFTER UPDATE OF status ON Applications
FOR EACH ROW
BEGIN
  IF :OLD.status <> :NEW.status THEN
    INSERT INTO ApplicationAuditLog (application_id, old_status, new_status)
    VALUES (:NEW.id, :OLD.status, :NEW.status);
  END IF;
END;
/
