# Problem statement

**Project:** Skill Bridge - AI Resume Analyzer and Job Matcher
**Course:** Prompt Engineering (SCSE4041), Bennett University
**Problem source:** Problem Pool, ID **C9 - Resume Feedback Against a Job Description**

## What is happening
Students applying for internships and jobs usually write one general resume and send it everywhere. A job description asks for specific skills, and most students cannot tell quickly whether their resume shows those skills, where the gaps are, or what to change.

## Where and to whom
It happens mostly during placement season. It affects college students, fresh graduates, internship applicants and career switchers. Placement cells and career counsellors are affected too: they have to review a lot of resumes by hand with little time per student.

## Why it matters
Employers look for proof, not claims. In NACE's *Job Outlook 2025* survey, nearly 90% of responding employers said they look for evidence of problem-solving on student resumes and nearly 80% look for teamwork ([NACE](https://www.naceweb.org/talent-acquisition/candidate-selection/what-are-employers-looking-for-when-reviewing-college-students-resumes)). A skill that sits in a skills list with no project behind it is weak evidence, and students rarely get told that.

## Input and output
| | |
|---|---|
| **Input** | Resume text and one job description |
| **Output** | A 0-100 match score with a visible breakdown, matching skills (each with a quote from the resume), missing skills, skills that are only listed but not demonstrated, and suggestions grounded in the resume |

## Why prompt engineering
A language model can read two free-form documents and judge how well they fit, which a keyword matcher cannot do. But an unconstrained model also invents skills, gives scores that change from run to run, and flatters. So the real work is in the prompt: asking for evidence, fixing the output format, defining the score with a rubric, and telling the model what it must never do. We test each change on labelled examples instead of trusting how the answer "looks".

## Existing tools and the gap
Tools such as [Jobscan](https://www.jobscan.co/resume-scanner) and [Teal](https://help.tealhq.com/en/articles/12060992-using-the-job-matcher) already compare a resume with a job description and give a match score. Our focus is different:
1. **Explainable scoring**: every point in the score can be traced.
2. **"Listed" vs "demonstrated"**: we separate skills that are only named from skills that are shown in a project or role.
3. **Honest suggestions**: the tool never tells a student to claim a skill they do not have.
4. **A measured approach**: prompt versions are compared against labelled data, not just judged by eye.

## Scope (and what we do not do)
- Plain-text resumes only (no PDF parsing yet).
- Skill-based matching; we do not judge writing quality, formatting or ATS compatibility.
- The score is guidance for the student. It must not be used to reject candidates.
- We use synthetic resumes only. No real personal data goes into any AI tool.
