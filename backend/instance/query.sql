-- SELECT * FROM problem_logs;

-- SELECT * FROM questions;


-- SELECT * FROM users;
-- SELECT * from synthesizers;
-- SELECT * FROM students;
-- SELECT * FROM problem_logs; 
-- SELECT * FROM skills;

-- Total number of logs
SELECT COUNT(*) AS log_count FROM problem_logs p
JOIN students s ON s.id = p.student_id
WHERE s.synthesizer_id IS NOT NULL;

-- Number of logs 
SELECT synth.model_name, COUNT(*) AS log_count FROM problem_logs p
JOIN students s ON s.id = p.student_id
JOIN synthesizers synth ON s.synthesizer_id = synth.id
WHERE s.synthesizer_id IS NOT NULL
Group By synth.model_name;

-- Number of synthesized students
SELECT COUNT(*) AS student_count FROM students s
WHERE s.synthesizer_id IS NOT NULL;

-- Synthesizer average answer accuracy
SELECT
    synth.model_name,
    AVG(pl.correct) AS accuracy
FROM problem_logs pl
JOIN students stu ON stu.id = pl.student_id
JOIN synthesizers synth ON synth.id = stu.synthesizer_id
GROUP BY synth.model_name;

-- Incorect questions per skill per synthesizer 
SELECT synth.model_name, sk.name, count(p.correct) as incorrect_count 
FROM problem_logs p 
JOIN questions q ON q.id = p.question_id
JOIN questions_skills qs ON qs.question_id = q.id
JOIN skills sk ON sk.id = qs.skill_id
JOIN students stu ON stu.id = p.student_id
JOIN synthesizers synth ON synth.id = stu.synthesizer_id
Where p.correct == False 
GROUP BY sk.name, synth.model_name;

-- Total number of incorrect questions per skill
SELECT sk.name, count(p.correct) as incorrect_count 
FROM problem_logs p 
JOIN questions q ON q.id = p.question_id
JOIN questions_skills qs ON qs.question_id = q.id
JOIN skills sk ON sk.id = qs.skill_id
Where p.correct == False 
GROUP BY sk.name;

-- Incorrect questions by skill per real user
SELECT sk.name, COUNT(p.correct) AS incorrect_count 
FROM problem_logs p 
JOIN questions q ON q.id = p.question_id
JOIN questions_skills qs ON qs.question_id = q.id
JOIN skills sk ON sk.id = qs.skill_id
JOIN students stu ON stu.id = p.student_id
JOIN users u ON u.id == stu.id
Where stu.synthesizer_id IS NULL AND p.correct == FALSE 
GROUP BY sk.name;

WITH qestion_correctness as (
    SELECT
        q.external_id,
        COUNT(CASE WHEN p.correct = False THEN 1 END) AS incorrect_count,
        COUNT(CASE WHEN p.correct = True THEN 1 END) AS correct_count,
        AVG(p.correct) as accuracy
    FROM problem_logs p
    JOIN questions q ON q.id = p.question_id
    JOIN questions_skills qs ON qs.question_id = q.id
    JOIN skills sk ON sk.id = qs.skill_id
    JOIN students stu ON stu.id = p.student_id
    where stu.synthesizer_id is Not NULL
    GROUP BY q.external_id
) SELECT * FROM qestion_correctness c
WHERE c.incorrect_count > 0
ORDER BY accuracy, incorrect_count DESC;