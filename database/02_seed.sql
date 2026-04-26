-- Lookup seeds only (never via frontend)

INSERT ALL
  INTO EducationLevels (code, label, score_weight) VALUES ('HS', 'High School', 45.00)
  INTO EducationLevels (code, label, score_weight) VALUES ('DIP', 'Diploma', 55.00)
  INTO EducationLevels (code, label, score_weight) VALUES ('BS', 'Bachelor', 72.00)
  INTO EducationLevels (code, label, score_weight) VALUES ('MS', 'Master', 88.00)
  INTO EducationLevels (code, label, score_weight) VALUES ('PHD', 'Doctorate', 100.00)
SELECT 1 FROM DUAL;

INSERT ALL
  INTO Skills (name) VALUES ('Python')
  INTO Skills (name) VALUES ('Java')
  INTO Skills (name) VALUES ('JavaScript')
  INTO Skills (name) VALUES ('SQL')
  INTO Skills (name) VALUES ('MySQL')
  INTO Skills (name) VALUES ('Flask')
  INTO Skills (name) VALUES ('React')
  INTO Skills (name) VALUES ('Machine Learning')
  INTO Skills (name) VALUES ('Data Analysis')
  INTO Skills (name) VALUES ('Project Management')
  INTO Skills (name) VALUES ('Communication')
  INTO Skills (name) VALUES ('Docker')
  INTO Skills (name) VALUES ('Git')
  INTO Skills (name) VALUES ('REST APIs')
  INTO Skills (name) VALUES ('HTML')
  INTO Skills (name) VALUES ('CSS')
  INTO Skills (name) VALUES ('TensorFlow')
  INTO Skills (name) VALUES ('PyTorch')
  INTO Skills (name) VALUES ('NLP')
  INTO Skills (name) VALUES ('Cloud Computing')
SELECT 1 FROM DUAL;
