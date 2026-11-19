import json, re, requests, random, subprocess, sys, textwrap, time
from ..config import AI_PROVIDER, OLLAMA_URL, OLLAMA_MODEL

GENERIC = [
    "Walk me through a project on your resume that best matches this role.",
    "Describe a difficult problem you solved and how you approached it.",
    "How do you learn a new technology quickly?",
    "Tell me about a time you received critical feedback and what you did with it.",
    "How would you handle competing priorities with a tight deadline.",
    "Describe a disagreement with a teammate and how you resolved it.",
    "What trade-off did you make in a recent project?",
    "How do you test or validate your work?",
    "What would you improve in a project you have already completed?",
    "Why are you a strong fit for this role?",
]

# ─── Ollama helper ────────────────────────────────────────────────────────────

def ollama(prompt):
    try:
        r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=90)
        r.raise_for_status()
        return r.json().get("response", "")
    except Exception:
        return None

def parse_json(raw):
    if not raw: return None
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    try: return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        try: return json.loads(m.group()) if m else None
        except Exception: return None

def parse_json_array(raw):
    if not raw: return None
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    try: return json.loads(raw)
    except Exception:
        m = re.search(r"\[.*\]", raw, re.S)
        try: return json.loads(m.group()) if m else None
        except Exception: return None

# ─── Interview questions ──────────────────────────────────────────────────────

def generate_questions(job, candidate, matched, missing, n=10):
    if AI_PROVIDER == "ollama":
        p = f'''Create exactly {n} interview questions for {job["title"]}.
Job: {job["description"]}. Required skills: {job["skills"]}.
Candidate matched skills: {matched}. Missing skills: {missing}.
Candidate resume: {candidate[:5000]}.
Mix technical, behavioral and situational questions; make every question job-relevant.
Return JSON only: {{"questions":[...]}}'''
        d = parse_json(ollama(p))
        qs = d.get("questions", []) if d else []
        if len(qs) >= n:
            random.shuffle(qs)
            return qs[:n], "ollama"
    pool = []
    for s in matched[:6]: pool.append(f"Explain a real project where you used {s} and the key technical decision you made.")
    for s in missing[:2]: pool.append(f"What do you know about {s}, and how would you learn it well enough to use it on this job?")
    pool += GENERIC
    out = []
    for q in pool:
        if q not in out: out.append(q)
        if len(out) == n: break
    random.shuffle(out)
    return out[:n], "fallback"

def grade(question, answer):
    if not answer.strip():
        return {"score": 0, "feedback": "No answer provided.", "strengths": [], "improvements": ["Provide a complete response with an example or reasoning."]}
    if AI_PROVIDER == "ollama":
        p = f'''Evaluate this interview answer.
Question: {question}
Answer: {answer}
Score 0-10 using correctness, relevance, depth, clarity and evidence.
Return JSON only: {{"score":0,"feedback":"...","strengths":["..."],"improvements":["..."]}}'''
        d = parse_json(ollama(p))
        if d and "score" in d:
            d["score"] = max(0, min(10, float(d["score"])))
            return d
    words = re.findall(r"\w+", answer.lower())
    qwords = set(re.findall(r"\w+", question.lower()))
    overlap = len(qwords & set(words))
    score = min(10, round(min(len(words) / 25, 1) * 6 + min(overlap / 5, 1) * 4, 1))
    return {
        "score": score,
        "feedback": "Local fallback evaluation based on answer depth and relevance.",
        "strengths": ["Answered the question" if len(words) > 15 else "Started an answer"],
        "improvements": ["Add concrete examples, reasoning and measurable outcomes."],
    }

# ─── Coding test ──────────────────────────────────────────────────────────────

FALLBACK_PROBLEMS = [
    {
        "title": "Two Sum",
        "description": "Given a list of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`. You may assume exactly one solution exists. Do not use the same element twice.",
        "function_signature": "def two_sum(nums: list, target: int) -> list:",
        "examples": [
            {"input": "nums=[2,7,11,15], target=9", "output": "[0, 1]"},
            {"input": "nums=[3,2,4], target=6",     "output": "[1, 2]"},
        ],
        "test_cases": [
            {"code": "assert two_sum([2,7,11,15],9)==[0,1] or two_sum([2,7,11,15],9)==(0,1)"},
            {"code": "assert two_sum([3,2,4],6)==[1,2]   or two_sum([3,2,4],6)==(1,2)"},
            {"code": "assert two_sum([3,3],6)==[0,1]     or two_sum([3,3],6)==(0,1)"},
        ],
    },
    {
        "title": "Reverse Words",
        "description": "Write a function `reverse_words(s)` that takes a sentence string and returns it with the words in reverse order. Strip extra spaces.",
        "function_signature": "def reverse_words(s: str) -> str:",
        "examples": [
            {"input": "s='the sky is blue'",     "output": "'blue is sky the'"},
            {"input": "s='  hello world  '",      "output": "'world hello'"},
        ],
        "test_cases": [
            {"code": "assert reverse_words('the sky is blue')=='blue is sky the'"},
            {"code": "assert reverse_words('  hello world  ')=='world hello'"},
            {"code": "assert reverse_words('a good   example')=='example good a'"},
        ],
    },
    {
        "title": "Fibonacci",
        "description": "Write a function `fib(n)` that returns the nth Fibonacci number (0-indexed). fib(0)=0, fib(1)=1.",
        "function_signature": "def fib(n: int) -> int:",
        "examples": [
            {"input": "n=6",  "output": "8"},
            {"input": "n=10", "output": "55"},
        ],
        "test_cases": [
            {"code": "assert fib(0)==0"},
            {"code": "assert fib(1)==1"},
            {"code": "assert fib(6)==8"},
            {"code": "assert fib(10)==55"},
        ],
    },
]

def generate_coding_problem(job: dict, skills: list) -> dict:
    if AI_PROVIDER == "ollama":
        skill_str = ", ".join(skills[:5]) if skills else "general programming"
        p = f'''Create a Python coding challenge for a {job["title"]} role.
Required skills: {skill_str}.
The problem should test core programming ability (algorithms/data structures).
Make it solvable in 15-20 minutes. Return JSON only:
{{
  "title": "Problem title",
  "description": "Clear problem statement with constraints",
  "function_signature": "def solve(...) -> ...:",
  "examples": [{{"input": "...", "output": "..."}}],
  "test_cases": [{{"code": "assert solve(...)==..."}}]
}}
Include at least 3 test cases.'''
        d = parse_json(ollama(p))
        if d and "title" in d and "test_cases" in d:
            return d
    return random.choice(FALLBACK_PROBLEMS)

def _run_code_safely(user_code: str, test_cases: list, timeout: int = 8) -> dict:
    tests_code = "\n".join(
        f"try:\n    {tc['code']}\n    results.append({{'n':{i+1},'passed':True,'msg':''}})\nexcept Exception as e:\n    results.append({{'n':{i+1},'passed':False,'msg':str(e)}})"
        for i, tc in enumerate(test_cases)
    )
    runner = textwrap.dedent(f"""
import json, sys
results = []
{user_code}
{tests_code}
passed = sum(1 for r in results if r['passed'])
print(json.dumps({{'passed': passed, 'total': len(results), 'results': results}}))
""")
    try:
        proc = subprocess.run([sys.executable, "-c", runner], capture_output=True, text=True, timeout=timeout)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if stdout:
            data = json.loads(stdout)
            data["error"] = stderr[:500] if stderr else ""
            return data
        return {"passed": 0, "total": len(test_cases), "results": [], "error": stderr[:500]}
    except subprocess.TimeoutExpired:
        return {"passed": 0, "total": len(test_cases), "results": [], "error": "Time limit exceeded (8s)"}
    except Exception as e:
        return {"passed": 0, "total": len(test_cases), "results": [], "error": str(e)}

def grade_code(problem: dict, code: str) -> dict:
    test_cases = problem.get("test_cases", [])
    if not code.strip():
        return {
            "score": 0,
            "feedback": "No code submitted.",
            "ai_explanation": "The candidate did not submit any code.",
            "execution_result": {"passed": 0, "total": len(test_cases), "results": [], "error": "Empty submission"},
        }

    exec_result = _run_code_safely(code, test_cases)
    passed = exec_result.get("passed", 0)
    total  = exec_result.get("total", len(test_cases)) or 1
    base_score = round((passed / total) * 100, 1)

    ai_explanation = ""
    if AI_PROVIDER == "ollama":
        p = f'''Review this Python code submission for the problem: "{problem.get('title', '')}".
Code:
```python
{code[:3000]}
```
Test results: {passed}/{total} test cases passed. Error: {exec_result.get('error','none')}.
Evaluate: correctness, code quality, edge-case handling, time/space complexity, readability.
Return JSON only:
{{
  "code_quality": 0-10,
  "complexity_analysis": "O(...)",
  "strengths": ["..."],
  "improvements": ["..."],
  "summary": "One paragraph explanation"
}}'''
        d = parse_json(ollama(p))
        if d:
            quality_bonus = min(10, float(d.get("code_quality", 5)))
            final_score = round(base_score * 0.8 + quality_bonus * 2, 1)
            ai_explanation = json.dumps(d)
            return {
                "score": min(100, final_score),
                "feedback": d.get("summary", ""),
                "ai_explanation": ai_explanation,
                "execution_result": exec_result,
            }

    feedback = f"{passed}/{total} test cases passed."
    if exec_result.get("error"): feedback += f" Error: {exec_result['error']}"
    lines = [l for l in code.strip().splitlines() if l.strip()]
    has_docstring = '"""' in code or "'''" in code
    has_comments  = any(l.strip().startswith("#") for l in lines)
    quality = 5 + (1 if has_docstring else 0) + (1 if has_comments else 0)
    final_score = round(base_score * 0.8 + quality * 2, 1)
    fallback_explanation = json.dumps({
        "code_quality": quality,
        "complexity_analysis": "Basic analysis (fallback)",
        "strengths": ["Code submitted and evaluated"],
        "improvements": ["Add docstrings", "Handle boundary conditions"],
        "summary": feedback,
    })
    return {
        "score": min(100, final_score),
        "feedback": feedback,
        "ai_explanation": fallback_explanation,
        "execution_result": exec_result,
    }


# ─── 1. Project & Portfolio Verification ──────────────────────────────────────

def verify_projects(job: dict, projects: list, portfolio_url: str = "", portfolio_summary: str = "") -> dict:
    """
    Evaluates candidate project evidence, relevance to role, github/live links, stack depth.
    """
    job_skills = set(s.lower() for s in job.get("skills", []))
    
    if AI_PROVIDER == "ollama":
        p = f'''Verify and assess candidate project portfolio for {job.get("title")}.
Required job skills: {job.get("skills")}.
Job description: {job.get("description")}.
Portfolio link: {portfolio_url}
Portfolio summary: {portfolio_summary}
Projects: {json.dumps(projects)}

Evaluate:
1. Relevance of projects to job requirements (0-100)
2. Technical complexity, architecture, evidence of genuine production skills
3. Authenticity verification (GitHub repo links, demo URLs, tech stack credibility)
4. Overall project score (0-100)
5. Strengths and key missing areas

Return JSON only:
{{
  "score": 0-100,
  "status": "verified" | "partially_verified" | "needs_more_evidence",
  "summary": "...",
  "strengths": ["...", "..."],
  "gaps": ["...", "..."],
  "project_evaluations": [
    {{"title": "...", "relevance_score": 0-100, "verdict": "...", "notes": "..."}}
  ]
}}'''
        d = parse_json(ollama(p))
        if d and "score" in d:
            d["score"] = max(0, min(100, float(d["score"])))
            return d

    # Heuristic verification fallback
    if not projects and not portfolio_url and not portfolio_summary:
        return {
            "score": 0,
            "status": "unverified",
            "summary": "No project evidence or portfolio submitted.",
            "strengths": [],
            "gaps": ["Candidate has not provided project or portfolio information."],
            "project_evaluations": [],
        }

    total_project_score = 0
    proj_evals = []
    matched_all = set()

    for prj in projects:
        title = prj.get("title", "Project")
        desc = prj.get("description", "")
        tech = set(t.lower() for t in prj.get("technologies", []))
        github = (prj.get("github_url") or "").strip()
        live = (prj.get("live_url") or "").strip()

        matched = tech & job_skills
        matched_all.update(matched)

        p_score = 30  # base
        if len(desc) > 80: p_score += 20
        elif len(desc) > 30: p_score += 10

        if "github.com" in github.lower(): p_score += 25
        elif github: p_score += 15

        if live: p_score += 15

        if matched: p_score += min(20, len(matched) * 8)

        p_score = min(100, p_score)
        total_project_score += p_score

        verdict = "Strong Evidence" if p_score >= 75 else ("Satisfactory" if p_score >= 50 else "Limited Details")
        proj_evals.append({
            "title": title,
            "relevance_score": p_score,
            "verdict": verdict,
            "notes": f"Matched skills: {', '.join(matched) if matched else 'General engineering'}. {'Repo linked.' if github else ''}",
        })

    avg_p_score = total_project_score / max(len(projects), 1)
    if portfolio_url and ("github.com" in portfolio_url or "http" in portfolio_url):
        avg_p_score = min(100, avg_p_score + 10)
    if portfolio_summary and len(portfolio_summary) > 50:
        avg_p_score = min(100, avg_p_score + 5)

    final_score = round(min(100, avg_p_score), 1)
    status = "verified" if final_score >= 70 else ("partially_verified" if final_score >= 45 else "needs_more_evidence")

    strengths = []
    if any("github.com" in (p.get("github_url") or "") for p in projects):
        strengths.append("Verified public code repository links provided")
    if matched_all:
        strengths.append(f"Demonstrated practical experience with: {', '.join(list(matched_all)[:4])}")
    if any(p.get("live_url") for p in projects):
        strengths.append("Live deployment / production demo link available")
    if not strengths:
        strengths.append("Project descriptions submitted for evaluation")

    gaps = []
    unmatched_skills = job_skills - matched_all
    if unmatched_skills:
        gaps.append(f"Few or no projects demonstrating: {', '.join(list(unmatched_skills)[:3])}")
    if not any((p.get("github_url") or "").strip() for p in projects):
        gaps.append("Missing GitHub source code links to verify code architecture")

    return {
        "score": final_score,
        "status": status,
        "summary": f"Verified {len(projects)} candidate projects. The portfolio demonstrates {status.replace('_', ' ')} capabilities aligned with role expectations.",
        "strengths": strengths,
        "gaps": gaps,
        "project_evaluations": proj_evals,
    }


# ─── 2. Role-Specific Skill Assessment ────────────────────────────────────────

FALLBACK_SKILL_QUESTION_BANKS = {
    "python": [
        {
            "id": "py_1",
            "skill": "Python",
            "question": "In Python, which built-in module is best suited for concurrent I/O-bound tasks without thread switching overhead?",
            "options": ["asyncio", "multiprocessing", "ctypes", "marshal"],
            "correct_option": 0,
            "explanation": "asyncio provides single-threaded asynchronous execution using an event loop, ideal for I/O bound tasks.",
        },
        {
            "id": "py_2",
            "skill": "Python",
            "question": "What is the primary difference between a generator function and a standard return function in Python?",
            "options": [
                "Generators yield values lazily one at a time saving memory",
                "Generators execute in a separate C process",
                "Generators can only yield numeric values",
                "Generators cannot take arguments",
            ],
            "correct_option": 0,
            "explanation": "Generators maintain internal state across yields and lazily stream items, avoiding loading entire collections in memory.",
        },
    ],
    "sql": [
        {
            "id": "sql_1",
            "skill": "SQL",
            "question": "Which window function assigns unique consecutive rankings even when duplicate values exist?",
            "options": ["ROW_NUMBER()", "RANK()", "DENSE_RANK()", "NTILE()"],
            "correct_option": 0,
            "explanation": "ROW_NUMBER() guarantees unique consecutive integers (1, 2, 3...) regardless of ties.",
        },
        {
            "id": "sql_2",
            "skill": "SQL",
            "question": "What does an INNER JOIN return when there is no matching key in the joined table?",
            "options": ["The row is omitted from the result set", "NULL values for the joined columns", "A synthetic default row", "A runtime SQL error"],
            "correct_option": 0,
            "explanation": "INNER JOIN only retains records where the join predicate evaluates to true on both sides.",
        },
    ],
    "machine learning": [
        {
            "id": "ml_1",
            "skill": "Machine Learning",
            "question": "Which technique is most effective to mitigate overfitting in complex deep neural networks?",
            "options": ["Dropout and L2 weight decay regularization", "Increasing training epochs arbitrarily", "Removing the validation set", "Using 100% learning rate"],
            "correct_option": 0,
            "explanation": "Dropout randomly deactivates neurons during training to prevent co-adaptation, while L2 regularization penalizes extreme weight magnitudes.",
        },
        {
            "id": "ml_2",
            "skill": "Machine Learning",
            "question": "When evaluating an imbalanced binary classifier (e.g., fraud 0.1%), which metric is most reliable?",
            "options": ["PR-AUC (Precision-Recall AUC) or F1 Score", "Raw Accuracy", "Mean Squared Error", "R-squared"],
            "correct_option": 0,
            "explanation": "Accuracy is misleading with extreme imbalance (a naive 99.9% null model); PR-AUC and F1 isolate true positives against false alarms.",
        },
    ],
    "react": [
        {
            "id": "react_1",
            "skill": "React",
            "question": "In React 18, what is the primary purpose of the useMemo hook?",
            "options": [
                "Cache computationally heavy calculations across re-renders",
                "Trigger direct DOM mutations outside the lifecycle",
                "Persist data to browser LocalStorage automatically",
                "Replace the Context API",
            ],
            "correct_option": 0,
            "explanation": "useMemo memoizes pure function computations so they only re-run when specific dependencies mutate.",
        },
    ],
}

def generate_role_skill_assessment(job: dict, skills: list, n: int = 5) -> list:
    """
    Generates role-specific skill assessment questions.
    """
    if AI_PROVIDER == "ollama":
        p = f'''Create exactly {n} role-specific technical multiple-choice questions for {job.get("title")}.
Required skills: {skills}.
Job description: {job.get("description")}.
Make them intermediate-to-advanced, testing practical engineering knowledge.
Return JSON only:
{{
  "questions": [
    {{
      "id": "q1",
      "skill": "...",
      "question": "...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_option": 0,
      "explanation": "..."
    }}
  ]
}}'''
        d = parse_json(ollama(p))
        if d and "questions" in d and len(d["questions"]) >= 3:
            return d["questions"][:n]

    # Curate questions from bank based on job skills
    selected = []
    found_keys = set()
    job_skills_lower = [s.lower() for s in skills]

    for bank_key, bank_qs in FALLBACK_SKILL_QUESTION_BANKS.items():
        if any(bank_key in s for s in job_skills_lower) or any(s in bank_key for s in job_skills_lower):
            selected.extend(bank_qs)
            found_keys.add(bank_key)

    # If still short, add standard core engineering questions
    if len(selected) < n:
        for b_qs in FALLBACK_SKILL_QUESTION_BANKS.values():
            for q in b_qs:
                if q not in selected:
                    selected.append(q)
                if len(selected) >= n: break
            if len(selected) >= n: break

    random.shuffle(selected)
    return selected[:n]

def grade_role_skill_assessment(questions: list, user_answers: list) -> dict:
    """
    Grades user answers to role-specific skill assessment questions.
    """
    total = len(questions)
    if total == 0:
        return {"score": 0, "total": 0, "correct": 0, "breakdown": []}

    correct_count = 0
    breakdown = []

    for i, q in enumerate(questions):
        correct_idx = q.get("correct_option", 0)
        user_ans = str(user_answers[i] if i < len(user_answers) else "").strip()
        
        # Check if user passed integer index or option text
        is_correct = False
        try:
            if int(user_ans) == correct_idx:
                is_correct = True
        except ValueError:
            options = q.get("options", [])
            if correct_idx < len(options) and user_ans.lower() == options[correct_idx].lower():
                is_correct = True

        if is_correct:
            correct_count += 1

        breakdown.append({
            "id": q.get("id", f"q_{i+1}"),
            "skill": q.get("skill", "Core"),
            "question": q.get("question", ""),
            "user_answer": user_ans,
            "correct_option": correct_idx,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    score = round((correct_count / total) * 100, 1)
    return {
        "score": score,
        "total": total,
        "correct": correct_count,
        "percentage": score,
        "proficiency_level": "Expert" if score >= 85 else ("Proficient" if score >= 65 else ("Developing" if score >= 40 else "Needs Improvement")),
        "breakdown": breakdown,
    }


# ─── 3. Communication & Situational Judgment ──────────────────────────────────

FALLBACK_SITUATIONAL_SCENARIOS = [
    {
        "id": "sjt_1",
        "title": "Critical Production Incident Under Deadline",
        "scenario": "A critical defect is detected in production 45 minutes before a key company presentation. A senior engineer proposes pushing an untested direct patch to production database to save face. How do you assess this, what do you communicate to stakeholders, and what action do you take?",
        "competencies": ["Risk Management", "Technical Ethics", "Crisis Communication"],
    },
    {
        "id": "sjt_2",
        "title": "Conflicting Cross-Functional Priorities",
        "scenario": "Your Product Manager requests immediate release of an unfinished feature for an urgent sales lead, while your Engineering Lead insists on addressing architectural vulnerabilities that could cause data inconsistency. How do you facilitate alignment and communicate trade-offs?",
        "competencies": ["Stakeholder Negotiation", "Strategic Alignment", "Clarity in Communication"],
    },
    {
        "id": "sjt_3",
        "title": "Team Collaboration & Mentorship Dilemma",
        "scenario": "A teammate is struggling to meet deliverables on a shared critical module and their pull requests contain recurring bugs, putting the team sprint at risk. How do you handle this situation constructively without escalating hostility?",
        "competencies": ["Peer Leadership", "Constructive Feedback", "Ownership"],
    },
]

def generate_situational_scenarios(job: dict, n: int = 3) -> list:
    """
    Generates situational judgment scenarios tailored to workplace communication and ethics.
    """
    if AI_PROVIDER == "ollama":
        p = f'''Create {n} realistic situational judgment scenarios for a {job.get("title")} role.
Scenarios should test:
1. Crisis and production incident communication
2. Cross-functional negotiation and conflicting trade-offs
3. Peer collaboration, feedback, and leadership
Return JSON only:
{{
  "scenarios": [
    {{
      "id": "sjt_1",
      "title": "...",
      "scenario": "...",
      "competencies": ["Communication", "Decision Making", "..."]
    }}
  ]
}}'''
        d = parse_json(ollama(p))
        if d and "scenarios" in d and len(d["scenarios"]) >= 2:
            return d["scenarios"][:n]

    return FALLBACK_SITUATIONAL_SCENARIOS[:n]

def grade_situational_responses(scenarios: list, responses: list) -> dict:
    """
    Evaluates candidate's written situational responses for judgment, communication clarity, ethics, and leadership.
    """
    if not any((r or "").strip() for r in responses):
        return {
            "score": 0,
            "feedback": "No situational responses provided.",
            "dimension_scores": {
                "communication_clarity": 0,
                "leadership_ownership": 0,
                "conflict_resolution": 0,
                "judgment_ethics": 0,
            },
            "evaluations": [],
        }

    if AI_PROVIDER == "ollama":
        p = f'''Evaluate these candidate responses to situational judgment workplace scenarios.
Scenarios and responses:
{json.dumps([{"scenario": s.get("scenario"), "response": responses[i] if i < len(responses) else ""} for i, s in enumerate(scenarios)])}

Score 0-100.
Evaluate:
1. Professional communication clarity and constructive tone
2. Sound decision-making under ambiguity or pressure
3. Stakeholder empathy and ethical integrity
4. Pragmatic resolution vs reactive behavior

Return JSON only:
{{
  "score": 0-100,
  "summary": "...",
  "dimension_scores": {{
    "communication_clarity": 0-10,
    "leadership_ownership": 0-10,
    "conflict_resolution": 0-10,
    "judgment_ethics": 0-10
  }},
  "evaluations": [
    {{"scenario_id": "...", "score": 0-10, "feedback": "...", "key_strength": "..."}}
  ]
}}'''
        d = parse_json(ollama(p))
        if d and "score" in d:
            d["score"] = max(0, min(100, float(d["score"])))
            return d

    # Heuristic scoring fallback
    evals = []
    total_score = 0
    words_total = 0

    for i, sc in enumerate(scenarios):
        ans = (responses[i] if i < len(responses) else "").strip()
        words = len(re.findall(r"\w+", ans))
        words_total += words

        # Evaluation criteria
        s_score = 40  # base
        if words >= 40: s_score += 30
        elif words >= 20: s_score += 15

        # Check for constructive judgment keywords
        constructive_terms = ["collaborate", "transparent", "stakeholder", "root cause", "mitigate", "priority", "test", "feedback", "discuss", "solution", "timeline", "document"]
        matched_terms = [t for t in constructive_terms if t in ans.lower()]
        s_score += min(30, len(matched_terms) * 6)

        s_score = min(100, s_score)
        total_score += s_score

        evals.append({
            "scenario_id": sc.get("id", f"sjt_{i+1}"),
            "title": sc.get("title", ""),
            "score": round(s_score / 10, 1),
            "feedback": f"Demonstrated {'strong structured reasoning' if s_score >= 75 else ('adequate situational response' if s_score >= 50 else 'brief answer lacking detail')}. Incorporated {len(matched_terms)} professional resolution considerations.",
        })

    avg_score = round(total_score / max(len(scenarios), 1), 1)
    comm_clarity = min(10, round(avg_score / 10, 1))

    return {
        "score": avg_score,
        "summary": f"Candidate demonstrated {('mature, balanced situational judgment with clear communication' if avg_score >= 70 else 'moderate situational problem-solving capabilities')}.",
        "dimension_scores": {
            "communication_clarity": comm_clarity,
            "leadership_ownership": min(10, round((avg_score * 0.95) / 10, 1)),
            "conflict_resolution": min(10, round((avg_score * 0.9) / 10, 1)),
            "judgment_ethics": min(10, round((avg_score * 1.05) / 10, 1)),
        },
        "evaluations": evals,
    }


# ─── 4. Explainable AI Scoring ────────────────────────────────────────────────

def explain_candidate_score(application: dict) -> dict:
    """
    Generate an explainable AI breakdown covering all completed assessment pillars.
    """
    resume_score = application.get("resume_score", 0)
    
    it = application.get("interview") or {}
    ct = application.get("coding_test") or {}
    pv = application.get("project_verification") or {}
    sa = application.get("skill_assessment") or {}
    sj = application.get("situational_test") or {}

    interview_score = it.get("score", 0) if it.get("completed") else 0
    coding_score    = ct.get("score", 0) if ct.get("completed") else 0
    project_score   = pv.get("score", 0) if pv.get("completed") else 0
    skill_score     = sa.get("score", 0) if sa.get("completed") else 0
    situational_score = sj.get("score", 0) if sj.get("completed") else 0

    has_it = bool(it.get("completed"))
    has_ct = bool(ct.get("completed"))
    has_pv = bool(pv.get("completed"))
    has_sa = bool(sa.get("completed"))
    has_sj = bool(sj.get("completed"))

    matched   = application.get("matched_skills", [])
    missing   = application.get("missing_skills", [])
    exp_score = application.get("experience_score", 0)

    # Dynamic weights based on what the candidate has completed
    components = [{"key": "resume", "score": resume_score, "base_w": 20, "label": "Resume & Profile", "color": "#667eea"}]
    if has_it: components.append({"key": "interview", "score": interview_score, "base_w": 20, "label": "AI Interview", "color": "#764ba2"})
    if has_ct: components.append({"key": "coding", "score": coding_score, "base_w": 20, "label": "Python Coding", "color": "#f093fb"})
    if has_pv: components.append({"key": "project", "score": project_score, "base_w": 15, "label": "Project Verification", "color": "#10b981"})
    if has_sa: components.append({"key": "skill", "score": skill_score, "base_w": 15, "label": "Role-Specific Skills", "color": "#3b82f6"})
    if has_sj: components.append({"key": "situational", "score": situational_score, "base_w": 10, "label": "Situational Judgment", "color": "#f59e0b"})

    total_w = sum(c["base_w"] for c in components)
    weighted_sum = sum(c["score"] * (c["base_w"] / total_w) for c in components)
    final = round(weighted_sum, 1)

    breakdown = [
        {
            "label": c["label"],
            "score": round(c["score"], 1),
            "weight": round((c["base_w"] / total_w) * 100),
            "max": 100,
            "color": c["color"],
        }
        for c in components
    ]

    skill_coverage = round(len(matched) / max(len(matched) + len(missing), 1) * 100, 1)
    radar = [
        {"dimension": "Resume Fit",      "score": round(resume_score, 1)},
        {"dimension": "Interview",       "score": round(interview_score, 1) if has_it else 0},
        {"dimension": "Python Coding",   "score": round(coding_score, 1) if has_ct else 0},
        {"dimension": "Projects",        "score": round(project_score, 1) if has_pv else 0},
        {"dimension": "Role Skills",     "score": round(skill_score, 1) if has_sa else 0},
        {"dimension": "Situational SJT", "score": round(situational_score, 1) if has_sj else 0},
        {"dimension": "Skill Coverage",  "score": skill_coverage},
    ]

    # AI narrative explanation
    explanation = ""
    recommendation = "consider"
    if AI_PROVIDER == "ollama":
        p = f'''Generate a comprehensive Explainable AI hiring assessment.
Candidate scores:
- Resume Fit: {resume_score}/100
- AI Interview: {interview_score}/100
- Python Coding: {coding_score}/100
- Project Verification: {project_score}/100
- Role Skills: {skill_score}/100
- Situational Judgment & Communication: {situational_score}/100
Composite Score: {final}/100.
Matched skills: {matched}. Missing: {missing}.

Provide:
1. Executive Assessment (3-4 sentences explaining hiring readiness)
2. 3 Key Strengths
3. 3 Risk Considerations
4. Recommendation: "strongly_recommend" | "recommend" | "consider" | "not_recommend"
Return JSON only:
{{
  "assessment": "...",
  "strengths": ["...", "...", "..."],
  "risks": ["...", "...", "..."],
  "recommendation": "recommend"
}}'''
        d = parse_json(ollama(p))
        if d:
            explanation = d.get("assessment", "")
            recommendation = d.get("recommendation", "consider")
            strengths = d.get("strengths", [])
            risks = d.get("risks", [])

    if final >= 80:
        recommendation = "strongly_recommend"
    elif final >= 65:
        recommendation = "recommend"
    elif final >= 45:
        recommendation = "consider"
    else:
        recommendation = "not_recommend"

    if not explanation:
        strengths, risks = _fallback_insights_all(resume_score, interview_score, coding_score, project_score, skill_score, situational_score, matched, missing)
        explanation = (
            f"Candidate achieved an overall composite score of {final}/100 across verified stages. "
            f"Resume analysis indicates {len(matched)} matching competencies. "
            f"{'Demonstrated solid coding test execution. ' if coding_score >= 60 else ''}"
            f"{'Project verification validated genuine engineering experience. ' if project_score >= 60 else ''}"
            f"{'Situational judgment showed sound workplace communication and maturity.' if situational_score >= 60 else ''}"
        )

    return {
        "final_score": final,
        "breakdown": breakdown,
        "radar": radar,
        "assessment": explanation,
        "strengths": strengths if "strengths" in dir() and strengths else ["Multi-faceted evaluation completed"],
        "risks": risks if "risks" in dir() and risks else ["Monitor skill progression"],
        "recommendation": recommendation,
        "recommendation_label": {
            "strongly_recommend": "Strongly Recommend",
            "recommend": "Recommend",
            "consider": "Consider",
            "not_recommend": "Do Not Recommend",
        }.get(recommendation, "Consider"),
        "recommendation_color": {
            "strongly_recommend": "#22c55e",
            "recommend": "#3b82f6",
            "consider": "#f59e0b",
            "not_recommend": "#ef4444",
        }.get(recommendation, "#f59e0b"),
    }

def _fallback_insights_all(resume, interview, coding, project, skills, situational, matched, missing):
    strengths, risks = [], []
    if resume >= 70: strengths.append(f"Strong resume profile with {len(matched)} matched core skills")
    if interview >= 70: strengths.append("High quality responses in AI adaptive interview")
    if coding >= 70: strengths.append("Solid problem-solving demonstrated in Python coding test")
    if project >= 70: strengths.append("Verified project portfolio with concrete code evidence")
    if skills >= 70: strengths.append("High accuracy in role-specific technical assessment")
    if situational >= 70: strengths.append("Mature communication, ethics, and situational judgment")

    if resume < 50: risks.append("Resume shows gaps against job specification")
    if interview > 0 and interview < 50: risks.append("Interview answers lacked depth or reasoning")
    if coding > 0 and coding < 50: risks.append("Coding test revealed algorithmic/syntax challenges")
    if project > 0 and project < 50: risks.append("Project evidence requires additional validation or live demos")
    if skills > 0 and skills < 50: risks.append("Lower score on core domain technical questions")
    if situational > 0 and situational < 50: risks.append("Workplace conflict and incident responses need improvement")
    if missing: risks.append(f"Skill gaps noted in: {', '.join(missing[:3])}")

    return (strengths or ["Assessment completed"])[:4], (risks or ["No critical red flags observed"])[:4]


# ─── 5. Recruitment Analysis ──────────────────────────────────────────────────

def recruitment_analysis(job: dict, all_applications: list) -> dict:
    """
    Generate recruitment funnel & competency benchmark analysis for recruiter dashboard.
    """
    total = len(all_applications)
    if not total:
        return {"total": 0, "funnel": [], "avg_scores": {}, "skill_coverage": [], "top_candidates": []}

    scores       = [a.get("resume_score", 0) for a in all_applications]
    int_scores   = [a.get("interview", {}).get("score", 0) for a in all_applications if a.get("interview", {}).get("completed")]
    code_scores  = [a.get("coding_test", {}).get("score", 0) for a in all_applications if a.get("coding_test", {}).get("completed")]
    proj_scores  = [a.get("project_verification", {}).get("score", 0) for a in all_applications if a.get("project_verification", {}).get("completed")]
    skill_scores = [a.get("skill_assessment", {}).get("score", 0) for a in all_applications if a.get("skill_assessment", {}).get("completed")]
    sit_scores   = [a.get("situational_test", {}).get("score", 0) for a in all_applications if a.get("situational_test", {}).get("completed")]

    statuses = {}
    for a in all_applications:
        s = a.get("status", "applied")
        statuses[s] = statuses.get(s, 0) + 1

    funnel = [
        {"stage": "Applied",     "count": total},
        {"stage": "In Review",   "count": statuses.get("in_review", 0)},
        {"stage": "Shortlisted", "count": statuses.get("shortlisted", 0)},
        {"stage": "Rejected",    "count": statuses.get("rejected", 0)},
    ]

    job_skills = job.get("skills", [])
    skill_coverage = []
    for s in job_skills:
        matched_count = sum(1 for a in all_applications if s in a.get("matched_skills", []))
        skill_coverage.append({
            "skill": s,
            "candidates_with_skill": matched_count,
            "coverage_pct": round(matched_count / total * 100, 1),
        })

    top = sorted(all_applications, key=lambda a: a.get("final_score", 0), reverse=True)[:5]
    top_candidates = [{"name": a.get("candidate_name", "—"), "score": a.get("final_score", 0)} for a in top]

    return {
        "total": total,
        "funnel": funnel,
        "avg_scores": {
            "resume":      round(sum(scores) / len(scores), 1) if scores else 0,
            "interview":   round(sum(int_scores) / len(int_scores), 1) if int_scores else 0,
            "coding":      round(sum(code_scores) / len(code_scores), 1) if code_scores else 0,
            "projects":    round(sum(proj_scores) / len(proj_scores), 1) if proj_scores else 0,
            "role_skills": round(sum(skill_scores) / len(skill_scores), 1) if skill_scores else 0,
            "situational": round(sum(sit_scores) / len(sit_scores), 1) if sit_scores else 0,
        },
        "interviews_completed": len(int_scores),
        "coding_completed": len(code_scores),
        "projects_verified": len(proj_scores),
        "skills_assessed": len(skill_scores),
        "situational_completed": len(sit_scores),
        "skill_coverage": skill_coverage,
        "top_candidates": top_candidates,
    }


# ─── Chatbot ──────────────────────────────────────────────────────────────────

_CHATBOT_FAQ = [
    {
        "keywords": ["apply", "how to apply", "start applying", "get started"],
        "answer": "To apply for a job:\n1. Click **Find Jobs** in the sidebar\n2. Browse open roles and click 'Analyze my resume'\n3. Upload your PDF or DOCX resume — AI scores your fit instantly\n4. Then complete 5 more assessment stages: Interview → Coding → Projects → Role Skills → Situational Judgment\n\nEach completed stage strengthens your composite fit score!"
    },
    {
        "keywords": ["score", "scoring", "fit score", "how scored", "composite", "percentage"],
        "answer": "Your **Composite Fit Score** is calculated across 6 evidence pillars:\n• Resume & Profile — 20%\n• AI Interview — 20%\n• Python Coding Test — 20%\n• Project Verification — 15%\n• Role-Specific Skills — 15%\n• Situational Judgment — 10%\n\nThe weights normalize dynamically — completing more stages gives a more accurate (and usually higher) score."
    },
    {
        "keywords": ["interview", "ai interview", "interview questions", "interview tips"],
        "answer": "The AI Interview has **10 adaptive questions** tailored to your resume and the job's skill requirements.\n\n💡 Tips for a great interview:\n• Use the **STAR method** (Situation, Task, Action, Result) for behavioral questions\n• Be specific — mention technologies, metrics, and outcomes\n• Answer concisely but with depth\n• The AI evaluates clarity, relevance, and depth"
    },
    {
        "keywords": ["coding", "python", "code test", "programming", "coding test"],
        "answer": "The **Python Coding Test** gives you a real programming problem to solve in about 20 minutes.\n\n💡 Coding tips:\n• Read the problem carefully — understand inputs/outputs first\n• Start with a working solution, then optimize\n• Handle edge cases (empty input, large numbers, etc.)\n• Add comments to explain your approach\n• The AI evaluates correctness, logic, and code quality"
    },
    {
        "keywords": ["portfolio", "project", "github", "verification", "projects"],
        "answer": "**Project Verification** evaluates your real-world experience:\n• Add 2–3 strong projects with clear descriptions\n• Include GitHub links so the AI can verify the tech stack\n• Add live demo links when available\n• List technologies used for each project\n\nThe AI checks how your projects align with the job's required skills."
    },
    {
        "keywords": ["skill", "role skill", "technical", "mcq", "multiple choice", "assessment"],
        "answer": "The **Role-Specific Skill Assessment** tests your domain knowledge with multiple-choice questions targeting the job's exact tech stack. Each question comes with a detailed AI explanation after submission. Aim to read questions carefully — some are scenario-based, not just definitions."
    },
    {
        "keywords": ["situational", "sjt", "judgment", "scenario", "communication", "behavioral"],
        "answer": "The **Situational Judgment Test (SJT)** presents 3 realistic workplace dilemmas.\n\nEvaluation focuses on:\n• How clearly you communicate your reasoning\n• Conflict resolution and empathy\n• Ethical decision-making\n• Leadership ownership and accountability\n\n💡 Write detailed, structured responses — explain your thinking, not just your answer."
    },
    {
        "keywords": ["status", "application status", "shortlisted", "rejected", "in review", "where am i"],
        "answer": "**Application Statuses:**\n• 🔵 **Applied** — Received and awaiting recruiter review\n• 🟡 **In Review** — Recruiter is actively evaluating your profile\n• 🟢 **Shortlisted** — You're a strong candidate! Expect contact soon\n• 🔴 **Rejected** — Not selected for this role — keep applying!\n\nComplete more assessments to improve your chances of being shortlisted."
    },
    {
        "keywords": ["email", "notification", "notify", "alert", "receive email"],
        "answer": "You'll receive email notifications at your registered address for:\n• New job vacancies posted by recruiters\n• Status changes on your applications\n\nCheck your spam/promotions folder if emails aren't appearing in your inbox."
    },
    {
        "keywords": ["recording", "video", "camera", "record"],
        "answer": "During the AI Interview, you can optionally **record your video session** using your webcam.\n• The recording is saved securely on the server\n• Recruiters can review it as part of your evaluation\n• Recording is optional — you can complete interviews without it\n• Use Chrome or Firefox for best webcam support"
    },
    {
        "keywords": ["recommend", "recommendation", "strongly recommend", "hire", "decision"],
        "answer": "**AI Hiring Recommendations** by score:\n• 🌟 **Strongly Recommend** — 80–100\n• ✅ **Recommend** — 65–79\n• 🔶 **Consider** — 45–64\n• ❌ **Do Not Recommend** — below 45\n\nComplete all 6 assessment pillars to maximize your score accuracy and recommendation level."
    },
    {
        "keywords": ["improve", "boost score", "increase score", "better score", "tips"],
        "answer": "**Ways to improve your fit score:**\n1. Complete all 6 assessment pillars — each adds to your composite score\n2. For interviews: use STAR method with specific examples\n3. For coding: handle edge cases and add explanatory comments\n4. For projects: add GitHub links and align technologies with job requirements\n5. For skills: study the job's tech stack before taking the MCQ test\n6. For SJT: write detailed, structured reasoning"
    },
    {
        "keywords": ["job match", "matching", "matched jobs", "recommended jobs", "best fit"],
        "answer": "**Multi-Job Matching** recommends the best-fit open positions based on your resume profile and skill set. Visit your **Dashboard** and scroll down to see 'Recommended Jobs' — each shows a match score, which skills align, and what you'd need to grow in."
    },
    {
        "keywords": ["pipeline", "stages", "stage", "recruiter", "process"],
        "answer": "The recruitment process has 6 stages:\n1. **Resume Upload** — AI scans your resume and scores skill match\n2. **AI Interview** — 10 adaptive questions recorded and evaluated\n3. **Python Coding** — Real programming challenge\n4. **Project Verification** — Portfolio and GitHub review\n5. **Role Skills MCQ** — Domain knowledge test\n6. **Situational Judgment** — Workplace decision-making scenarios\n\nComplete all stages to get the most thorough and favorable evaluation."
    },
    {
        "keywords": ["hello", "hi", "hey", "greet", "help"],
        "answer": "👋 Hi there! I'm **HireMind Assistant**, your AI career guide.\n\nI can help you with:\n• How to apply and navigate the platform\n• Understanding your fit score and assessments\n• Interview, coding, and project tips\n• Application status explanations\n• Improving your overall score\n\nWhat would you like to know?"
    },
]

def chatbot_reply(message: str, user_role: str = "candidate", history: list = None) -> dict:
    """
    AI-powered candidate support chatbot.
    Uses keyword FAQ matching with Ollama enhancement fallback.
    """
    msg_lower = message.lower().strip()
    history = history or []

    # Try FAQ keyword matching first (instant, no AI needed)
    for faq in _CHATBOT_FAQ:
        if any(kw in msg_lower for kw in faq["keywords"]):
            return {
                "reply": faq["answer"],
                "source": "faq",
                "quick_replies": _get_quick_replies(faq["keywords"][0])
            }

    # Try Ollama for dynamic contextual response
    if AI_PROVIDER == "ollama":
        hist_str = ""
        if history:
            recent = history[-6:]  # last 3 exchanges
            hist_str = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)

        p = f'''You are HireMind Assistant, a friendly AI career coach embedded in an AI recruitment platform called HireMind.

The platform has 6 assessment pillars: Resume (20%), AI Interview (20%), Python Coding (20%), Project Verification (15%), Role Skills MCQ (15%), Situational Judgment (10%).

{f"Recent conversation:{chr(10)}{hist_str}{chr(10)}" if hist_str else ""}
User ({user_role}) asks: {message}

Reply helpfully and concisely (2-4 sentences). Focus on actionable advice for their recruitment journey. Plain text only.'''

        reply = ollama(p)
        if reply and len(reply.strip()) > 15:
            return {
                "reply": reply.strip(),
                "source": "ai",
                "quick_replies": ["How is scoring done?", "Interview tips", "Coding test help", "My application status"]
            }

    # Fallback generic responses
    fallbacks = [
        "I'm here to support your HireMind journey! Try asking me about:\n• How to apply for jobs\n• How your fit score is calculated\n• Interview or coding test tips\n• Understanding your application status\n• Ways to boost your composite score",
        "Great question! I can help with:\n• The 6-stage assessment process\n• Tips for each assessment pillar\n• What recruiters look for\n• Platform navigation\n\nWhat specifically can I help you with?",
    ]
    return {
        "reply": random.choice(fallbacks),
        "source": "fallback",
        "quick_replies": ["How to apply?", "How is scoring done?", "Interview tips", "Coding test tips"]
    }

def _get_quick_replies(topic: str) -> list:
    mapping = {
        "apply": ["How is scoring done?", "Interview tips", "Coding test tips"],
        "score": ["How to improve my score?", "Interview tips", "What does shortlisted mean?"],
        "interview": ["Coding test tips", "How is scoring done?", "What is SJT?"],
        "coding": ["Interview tips", "Project verification tips", "How is scoring done?"],
        "portfolio": ["Role skill assessment tips", "Interview tips", "How is scoring done?"],
        "skill": ["Interview tips", "Coding test tips", "How to improve my score?"],
        "situational": ["Interview tips", "How is scoring done?", "What does shortlisted mean?"],
        "status": ["How to improve my score?", "How to apply?", "Interview tips"],
        "hello": ["How to apply?", "How is scoring done?", "Interview tips", "Coding test tips"],
        "improve": ["Interview tips", "Coding test tips", "Project verification tips"],
        "recommend": ["How is scoring done?", "How to improve my score?", "Interview tips"],
    }
    for k, v in mapping.items():
        if k in topic:
            return v
    return ["How to apply?", "How is scoring done?", "Interview tips"]


# ─── Pipeline Recommendations ─────────────────────────────────────────────────

def generate_pipeline_recommendations(candidates: list) -> list:
    """
    Analyze candidate pipeline and generate AI-powered next-action recommendations.
    Returns list sorted by priority (high → normal → low).
    """
    recommendations = []
    for c in candidates:
        score = c.get("final_score", 0) or 0
        status = c.get("status", "applied")
        has_interview = c.get("interview_score") is not None
        has_coding = c.get("coding_score") is not None
        has_projects = c.get("projects_score") is not None
        assessments_done = sum([has_interview, has_coding, has_projects])

        action = ""
        priority = "normal"
        reason = ""
        color = "#667eea"

        if status == "applied":
            if score >= 80:
                action = "Fast-track to Shortlist"
                priority = "high"
                reason = f"Outstanding fit score ({score:.0f}/100). Strong all-round candidate."
                color = "#22c55e"
            elif score >= 65:
                action = "Move to In Review"
                priority = "normal"
                reason = f"Good resume match ({score:.0f}/100). Worth a closer look."
                color = "#3b82f6"
            elif not has_interview:
                action = "Prompt Interview"
                priority = "normal"
                reason = "Candidate hasn't started the AI Interview yet."
                color = "#f59e0b"
            else:
                action = "Review & Decide"
                priority = "low"
                reason = f"Lower initial fit ({score:.0f}/100). Consider rejection or further testing."
                color = "#94a3b8"

        elif status == "in_review":
            if not has_interview:
                action = "Schedule AI Interview"
                priority = "high"
                reason = "In review but interview not started. Send a prompt."
                color = "#f59e0b"
            elif not has_coding:
                action = "Prompt Coding Test"
                priority = "normal"
                reason = "Interview complete. Coding test needed for full evaluation."
                color = "#8b5cf6"
            elif score >= 72:
                action = "Move to Shortlist"
                priority = "high"
                reason = f"Well-rounded candidate ({score:.0f}/100). Ready for shortlisting."
                color = "#22c55e"
            elif assessments_done < 2:
                action = "Request More Assessments"
                priority = "normal"
                reason = f"Only {assessments_done}/5 assessments complete. Incomplete picture."
                color = "#f59e0b"
            else:
                action = "Hold or Reject"
                priority = "low"
                reason = f"Low composite score ({score:.0f}/100) despite multiple assessments."
                color = "#ef4444"

        elif status == "shortlisted":
            action = "Schedule Final Interview"
            priority = "normal"
            reason = "Candidate is shortlisted. Coordinate final interview round."
            color = "#10b981"

        if action:
            recommendations.append({
                "candidate_id": c.get("candidate_id"),
                "candidate_name": c.get("candidate_name", "Unknown"),
                "application_id": c.get("id"),
                "action": action,
                "priority": priority,
                "reason": reason,
                "color": color,
                "current_score": round(score, 1),
                "status": status,
            })

    priority_order = {"high": 0, "normal": 1, "low": 2}
    return sorted(recommendations, key=lambda x: priority_order.get(x["priority"], 1))


# ─── 360° Profile Builder ─────────────────────────────────────────────────────

def build_360_profile(app: dict) -> dict:
    """
    Aggregate all assessment data into a comprehensive 360° candidate profile.
    """
    iv = app.get("interview") or {}
    ct = app.get("coding_test") or {}
    pv = app.get("project_verification") or {}
    sa = app.get("skill_assessment") or {}
    st = app.get("situational_test") or {}

    # Activity timeline (most recent first)
    timeline = []
    if app.get("created_at"):
        timeline.append({"event": "Resume Submitted & Analyzed", "icon": "resume",
                          "score": app.get("resume_score", 0), "date": app.get("created_at", ""),
                          "color": "#667eea", "completed": True})
    if iv.get("completed"):
        timeline.append({"event": "AI Interview Completed", "icon": "interview",
                          "score": iv.get("score", 0), "date": iv.get("created_at", ""),
                          "color": "#764ba2", "completed": True})
    if ct.get("completed"):
        timeline.append({"event": "Python Coding Test Completed", "icon": "coding",
                          "score": ct.get("score", 0), "date": ct.get("created_at", ""),
                          "color": "#10b981", "completed": True})
    if pv.get("completed"):
        timeline.append({"event": "Project Portfolio Verified", "icon": "projects",
                          "score": pv.get("score", 0), "date": pv.get("created_at", ""),
                          "color": "#059669", "completed": True})
    if sa.get("completed"):
        timeline.append({"event": "Role Skills Assessment Completed", "icon": "skills",
                          "score": sa.get("score", 0), "date": sa.get("created_at", ""),
                          "color": "#3b82f6", "completed": True})
    if st.get("completed"):
        timeline.append({"event": "Situational Judgment Test Completed", "icon": "sjt",
                          "score": st.get("score", 0), "date": st.get("created_at", ""),
                          "color": "#f59e0b", "completed": True})

    # Pillars summary
    pillars = [
        {"name": "Resume & Profile",   "score": app.get("resume_score", 0), "weight": 20, "completed": True,                    "color": "#667eea"},
        {"name": "AI Interview",        "score": iv.get("score", 0),         "weight": 20, "completed": bool(iv.get("completed")), "color": "#764ba2"},
        {"name": "Python Coding",       "score": ct.get("score", 0),         "weight": 20, "completed": bool(ct.get("completed")), "color": "#10b981"},
        {"name": "Project Verification","score": pv.get("score", 0),         "weight": 15, "completed": bool(pv.get("completed")), "color": "#059669"},
        {"name": "Role-Specific Skills","score": sa.get("score", 0),         "weight": 15, "completed": bool(sa.get("completed")), "color": "#3b82f6"},
        {"name": "Situational Judgment","score": st.get("score", 0),         "weight": 10, "completed": bool(st.get("completed")), "color": "#f59e0b"},
    ]

    # Skill heatmap
    job_skills  = app.get("job_skills", [])
    matched     = set(s.lower() for s in (app.get("matched_skills") or []))
    missing_set = set(s.lower() for s in (app.get("missing_skills") or []))
    skill_heatmap = []
    for skill in job_skills:
        sl = skill.lower()
        if sl in matched:
            skill_heatmap.append({"skill": skill, "status": "strong",  "color": "#22c55e", "bg": "#dcfce7"})
        elif sl in missing_set:
            skill_heatmap.append({"skill": skill, "status": "gap",     "color": "#ef4444", "bg": "#fee2e2"})
        else:
            skill_heatmap.append({"skill": skill, "status": "partial", "color": "#f59e0b", "bg": "#fef3c7"})

    completions = sum(1 for p in pillars if p["completed"])
    return {
        "candidate_name":   app.get("candidate_name", ""),
        "candidate_email":  app.get("candidate_email", ""),
        "job_title":        app.get("job_title", ""),
        "job_company":      app.get("job_location", ""),
        "status":           app.get("status", "applied"),
        "application_date": app.get("created_at", ""),
        "final_score":      app.get("final_score", 0),
        "resume_score":     app.get("resume_score", 0),
        "ai_summary":       app.get("ai_summary", ""),
        "matched_skills":   app.get("matched_skills") or [],
        "missing_skills":   app.get("missing_skills") or [],
        "skill_heatmap":    skill_heatmap,
        "pillars":          pillars,
        "timeline":         timeline,
        "assessments_completed": completions,
        "assessments_total":     len(pillars),
        "interview":        iv,
        "coding_test":      ct,
        "project_verification": pv,
        "skill_assessment": sa,
        "situational_test": st,
    }


# ─── Multi-Job Matching ───────────────────────────────────────────────────────

def match_jobs_to_candidate(candidate_profile: dict, jobs: list, applied_job_ids: set = None) -> list:
    """
    Score and rank open jobs against a candidate's resume skills.
    Returns sorted list (best match first) with match_score, matched_skills, missing_skills, reason.
    """
    applied_job_ids = applied_job_ids or set()
    resume_text   = (candidate_profile.get("resume_text") or "").lower()
    resume_skills = set(s.lower() for s in (candidate_profile.get("matched_skills") or []))
    resume_words  = set(re.findall(r"\b\w+\b", resume_text))

    matches = []
    for job in jobs:
        raw_skills = job.get("skills", [])
        if isinstance(raw_skills, str):
            try: raw_skills = json.loads(raw_skills)
            except: raw_skills = []
        job_skills = set(s.lower() for s in raw_skills)

        if not job_skills:
            continue

        # Direct skill-set overlap
        matched  = job_skills & (resume_skills | resume_words)
        missing  = job_skills - matched

        # Weighted score: 70% skill overlap ratio + 30% keyword density bonus
        overlap_ratio   = len(matched) / len(job_skills)
        keyword_hits    = sum(1 for s in job_skills if s in resume_text)
        keyword_bonus   = min(0.3, keyword_hits / max(len(job_skills), 1) * 0.3)
        match_score     = round(min(100, (overlap_ratio * 70) + (keyword_bonus * 100)), 1)

        # Build reason text
        if matched:
            top_matched = list(matched)[:3]
            reason = f"Your skills in {', '.join(top_matched)} align with this role."
        else:
            reason = "This role offers new growth opportunities based on your profile."
        if missing:
            top_missing = list(missing)[:2]
            reason += f" You'd grow in {', '.join(top_missing)}."

        matches.append({
            "job":             job,
            "match_score":     match_score,
            "matched_skills":  [s for s in raw_skills if s.lower() in matched],
            "missing_skills":  [s for s in raw_skills if s.lower() in missing],
            "match_reason":    reason.strip(),
            "already_applied": job["id"] in applied_job_ids,
        })

    return sorted(matches, key=lambda x: x["match_score"], reverse=True)
