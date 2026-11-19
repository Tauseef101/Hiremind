from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json, logging, uuid

from .database import init_db, row, rows, execq
from .schemas import (
    Register, Login, JobCreate, StatusUpdate, InterviewSubmit, CodingSubmit,
    ScheduleCreate, ProjectVerifySubmit, SkillAssessmentSubmit, SituationalSubmit, ChatMessage,
)
from .auth import hash_password, verify_password, create_token, current_user
from .services.resume_service import extract_text, score_resume
from .services.ai_service import (
    generate_questions, grade,
    generate_coding_problem, grade_code,
    verify_projects, generate_role_skill_assessment, grade_role_skill_assessment,
    generate_situational_scenarios, grade_situational_responses,
    explain_candidate_score, recruitment_analysis,
    chatbot_reply, generate_pipeline_recommendations, build_360_profile, match_jobs_to_candidate,
)
from .services.email_service import notify_vacancy
from .services.recording_service import save_recording, list_recordings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

init_db()
app = FastAPI(title="AI Recruiter API", version="3.5")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def public_user(u):
    return {k: u[k] for k in ["id", "name", "email", "role", "created_at"]}


def application_detail(aid, u):
    a = row(
        "SELECT a.*,u.name candidate_name,j.title job_title,j.description job_description,"
        "j.skills job_skills,j.experience job_experience,j.location,j.employment_type,"
        "j.salary,j.openings,j.deadline,j.recruiter_id "
        "FROM applications a "
        "JOIN jobs j ON a.job_id=j.id "
        "JOIN users u ON a.candidate_id=u.id "
        "WHERE a.id=?",
        (aid,),
    )
    if not a:
        raise HTTPException(404, "Application not found")
    if u["role"] == "candidate" and a["candidate_id"] != u["id"]:
        raise HTTPException(403, "Forbidden")
    if u["role"] == "recruiter" and a["recruiter_id"] != u["id"]:
        raise HTTPException(403, "Forbidden")

    a["matched_skills"] = json.loads(a["matched_skills"])
    a["missing_skills"]  = json.loads(a["missing_skills"])
    a["job_skills"]      = json.loads(a["job_skills"])

    # 1. Interview
    it = row("SELECT * FROM interviews WHERE application_id=?", (aid,))
    if it:
        it["questions"]   = json.loads(it["questions"])
        it["answers"]     = json.loads(it["answers"])
        it["evaluations"] = json.loads(it["evaluations"])
    a["interview"] = it

    # 2. Coding test
    ct = row("SELECT * FROM coding_tests WHERE application_id=?", (aid,))
    if ct:
        ct["test_cases"]       = json.loads(ct["test_cases"])
        ct["execution_result"] = json.loads(ct["execution_result"])
        ct["problem"]          = json.loads(ct["problem"]) if ct["problem"].startswith("{") else ct["problem"]
    a["coding_test"] = ct

    # 3. Project Verification
    pv = row("SELECT * FROM project_verifications WHERE application_id=?", (aid,))
    if pv:
        pv["projects"]   = json.loads(pv["projects"])
        pv["evaluation"] = json.loads(pv["evaluation"])
    a["project_verification"] = pv

    # 4. Role-Specific Skill Assessment
    sa = row("SELECT * FROM skill_assessments WHERE application_id=?", (aid,))
    if sa:
        sa["questions"]   = json.loads(sa["questions"])
        sa["answers"]     = json.loads(sa["answers"])
        sa["evaluations"] = json.loads(sa["evaluations"])
    a["skill_assessment"] = sa

    # 5. Communication & Situational Judgment
    sj = row("SELECT * FROM situational_tests WHERE application_id=?", (aid,))
    if sj:
        sj["scenarios"]   = json.loads(sj["scenarios"])
        sj["responses"]   = json.loads(sj["responses"])
        sj["evaluations"] = json.loads(sj["evaluations"])
    a["situational_test"] = sj

    # Schedules
    a["schedules"] = rows(
        "SELECT * FROM test_schedules WHERE application_id=? ORDER BY scheduled_at ASC",
        (aid,),
    )

    # Dynamic composite score across all completed assessment pillars
    weights = [("resume", a["resume_score"], 20)]
    if it and it["completed"]: weights.append(("it", it["score"], 20))
    if ct and ct["completed"]: weights.append(("ct", ct["score"], 20))
    if pv and pv["completed"]: weights.append(("pv", pv["score"], 15))
    if sa and sa["completed"]: weights.append(("sa", sa["score"], 15))
    if sj and sj["completed"]: weights.append(("sj", sj["score"], 10))

    total_weight = sum(w[2] for w in weights)
    final = round(sum(w[1] * (w[2] / total_weight) for w in weights), 2)
    a["final_score"] = final
    return a


# ─── health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    from .config import AI_PROVIDER
    return {"status": "ok", "ai_provider": AI_PROVIDER, "version": "3.5"}


# ─── auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(x: Register):
    if x.role not in ("candidate", "recruiter"):
        raise HTTPException(400, "Invalid role")
    if row("SELECT id FROM users WHERE email=?", (x.email.lower().strip(),)):
        raise HTTPException(409, "Email already registered")
    uid = execq(
        "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
        (x.name.strip(), x.email.lower().strip(), hash_password(x.password), x.role),
    )
    u = row("SELECT id,name,email,role,created_at FROM users WHERE id=?", (uid,))
    return {"token": create_token(u), "user": public_user(u)}


@app.post("/api/auth/login")
def login(x: Login):
    u = row("SELECT * FROM users WHERE email=?", (x.email.lower().strip(),))
    if not u or not verify_password(x.password, u["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_token(u), "user": public_user(u)}


@app.get("/api/me")
def me(u=Depends(current_user)):
    return u


# ─── jobs ─────────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def all_jobs(u=Depends(current_user)):
    js = rows('SELECT j.*,u.name recruiter_name FROM jobs j JOIN users u ON j.recruiter_id=u.id WHERE j.status="open" ORDER BY j.created_at DESC')
    for j in js:
        j["skills"] = json.loads(j["skills"])
    return js


@app.post("/api/jobs")
def create_job(x: JobCreate, bg: BackgroundTasks, u=Depends(current_user)):
    if u["role"] != "recruiter":
        raise HTTPException(403, "Recruiters only")
    jid = execq(
        "INSERT INTO jobs(recruiter_id,title,description,skills,experience,location,employment_type,salary,openings,deadline) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (u["id"], x.title, x.description, json.dumps([s.strip().lower() for s in x.skills if s.strip()]),
         x.experience, x.location, x.employment_type, x.salary, x.openings, x.deadline),
    )
    job = row("SELECT * FROM jobs WHERE id=?", (jid,))
    job["skills"] = json.loads(job["skills"])
    candidate_emails = [r["email"] for r in rows("SELECT email FROM users WHERE role='candidate'")]
    print(f"[JOB] '{job['title']}' by {u['name']} — notifying {len(candidate_emails)} candidate(s).")
    if candidate_emails:
        bg.add_task(notify_vacancy, job, candidate_emails, u["name"], u["email"])
    return job


@app.get("/api/jobs/mine")
def my_jobs(u=Depends(current_user)):
    if u["role"] != "recruiter":
        raise HTTPException(403, "Recruiters only")
    js = rows("SELECT * FROM jobs WHERE recruiter_id=? ORDER BY created_at DESC", (u["id"],))
    for j in js:
        j["skills"] = json.loads(j["skills"])
        j["applications"] = row("SELECT COUNT(*) c FROM applications WHERE job_id=?", (j["id"],))["c"]
    return js


# ─── applications ─────────────────────────────────────────────────────────────

@app.post("/api/applications/{job_id}/resume")
async def apply(job_id: int, resume: UploadFile = File(...), u=Depends(current_user)):
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")
    job = row("SELECT * FROM jobs WHERE id=?", (job_id,))
    if not job:
        raise HTTPException(404, "Job not found")
    data = await resume.read()
    try:
        text = extract_text(data, resume.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    score, matched, missing, exp_score = score_resume(text, {**job, "skills": json.loads(job["skills"])})
    existing = row("SELECT id FROM applications WHERE candidate_id=? AND job_id=?", (u["id"], job_id))
    if existing:
        aid = existing["id"]
        execq(
            'UPDATE applications SET resume_filename=?,resume_text=?,resume_score=?,matched_skills=?,missing_skills=?,experience_score=?,status="applied" WHERE id=?',
            (resume.filename, text, score, json.dumps(matched), json.dumps(missing), exp_score, aid),
        )
    else:
        aid = execq(
            "INSERT INTO applications(candidate_id,job_id,resume_filename,resume_text,resume_score,matched_skills,missing_skills,experience_score) VALUES(?,?,?,?,?,?,?,?)",
            (u["id"], job_id, resume.filename, text, score, json.dumps(matched), json.dumps(missing), exp_score),
        )
    return application_detail(aid, u)


@app.get("/api/candidate/applications")
def candidate_apps(u=Depends(current_user)):
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")
    return [application_detail(a["id"], u) for a in rows("SELECT id FROM applications WHERE candidate_id=? ORDER BY created_at DESC", (u["id"],))]


@app.get("/api/applications/{aid}")
def get_app(aid: int, u=Depends(current_user)):
    return application_detail(aid, u)


# ─── 1. Interview ─────────────────────────────────────────────────────────────

@app.post("/api/applications/{aid}/interview/start")
def start_interview(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    job = {"title": a["job_title"], "description": a["job_description"], "skills": a["job_skills"]}
    qs, engine = generate_questions(job, u["name"], a["matched_skills"], a["missing_skills"])
    execq(
        'INSERT INTO interviews(application_id,questions,completed) VALUES(?,?,0) ON CONFLICT(application_id) DO UPDATE SET questions=excluded.questions,answers="[]",evaluations="[]",score=0,completed=0',
        (aid, json.dumps(qs)),
    )
    return {"questions": qs, "engine": engine}


@app.post("/api/applications/{aid}/interview/submit")
def submit_interview(aid: int, x: InterviewSubmit, u=Depends(current_user)):
    a = application_detail(aid, u)
    it = a["interview"]
    if not it:
        raise HTTPException(400, "Start interview first")
    if len(x.answers) != len(it["questions"]):
        raise HTTPException(400, "Answer every question")
    evals = [grade(q, ans) for q, ans in zip(it["questions"], x.answers)]
    score = round(sum(float(e["score"]) for e in evals) / (len(evals) * 10) * 100, 2)
    execq(
        "UPDATE interviews SET answers=?,evaluations=?,score=?,completed=1 WHERE application_id=?",
        (json.dumps(x.answers), json.dumps(evals), score, aid),
    )
    return application_detail(aid, u)


# ─── 2. Coding test ───────────────────────────────────────────────────────────

@app.post("/api/applications/{aid}/coding/start")
def start_coding(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")
    job = {"title": a["job_title"], "description": a["job_description"], "skills": a["job_skills"]}
    problem = generate_coding_problem(job, a["job_skills"])
    execq(
        "INSERT INTO coding_tests(application_id,problem,test_cases,completed) VALUES(?,?,?,0) "
        "ON CONFLICT(application_id) DO UPDATE SET problem=excluded.problem,test_cases=excluded.test_cases,"
        "submitted_code='',execution_result='{}',score=0,feedback='',ai_explanation='',completed=0",
        (aid, json.dumps(problem), json.dumps(problem.get("test_cases", []))),
    )
    safe = {k: v for k, v in problem.items() if k != "test_cases"}
    return {"problem": safe}


@app.post("/api/applications/{aid}/coding/submit")
def submit_coding(aid: int, x: CodingSubmit, u=Depends(current_user)):
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")
    ct = row("SELECT * FROM coding_tests WHERE application_id=?", (aid,))
    if not ct:
        raise HTTPException(400, "Start the coding test first")
    try:
        problem = json.loads(ct["problem"])
    except Exception:
        raise HTTPException(400, "Invalid coding test state")

    result = grade_code(problem, x.code)
    execq(
        "UPDATE coding_tests SET submitted_code=?,execution_result=?,score=?,feedback=?,ai_explanation=?,completed=1 WHERE application_id=?",
        (
            x.code,
            json.dumps(result["execution_result"]),
            result["score"],
            result["feedback"],
            result["ai_explanation"],
            aid,
        ),
    )
    return application_detail(aid, u)


@app.get("/api/applications/{aid}/coding")
def get_coding(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    ct = a.get("coding_test")
    if not ct:
        return {"coding_test": None}
    if u["role"] == "candidate" and not ct.get("completed"):
        try:
            p = json.loads(ct["problem"]) if isinstance(ct["problem"], str) else ct["problem"]
            safe = {k: v for k, v in p.items() if k != "test_cases"}
            ct["problem"] = safe
        except Exception:
            pass
        ct.pop("test_cases", None)
    return {"coding_test": ct}


# ─── 3. Project and Portfolio Verification ────────────────────────────────────

@app.post("/api/applications/{aid}/projects/verify")
def submit_projects_for_verification(aid: int, x: ProjectVerifySubmit, u=Depends(current_user)):
    a = application_detail(aid, u)
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")

    job = {"title": a["job_title"], "description": a["job_description"], "skills": a["job_skills"]}
    projects_dict = [p.dict() for p in x.projects]
    eval_result = verify_projects(job, projects_dict, x.portfolio_url or "", x.portfolio_summary or "")
    score = eval_result.get("score", 0)

    execq(
        "INSERT INTO project_verifications(application_id,projects,portfolio_url,portfolio_summary,score,evaluation,completed) "
        "VALUES(?,?,?,?,?,?,1) "
        "ON CONFLICT(application_id) DO UPDATE SET "
        "projects=excluded.projects,portfolio_url=excluded.portfolio_url,portfolio_summary=excluded.portfolio_summary,"
        "score=excluded.score,evaluation=excluded.evaluation,completed=1",
        (
            aid,
            json.dumps(projects_dict),
            x.portfolio_url or "",
            x.portfolio_summary or "",
            score,
            json.dumps(eval_result),
        ),
    )
    return application_detail(aid, u)


@app.get("/api/applications/{aid}/projects")
def get_projects(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    return {"project_verification": a.get("project_verification")}


# ─── 4. Role-Specific Skill Assessment ────────────────────────────────────────

@app.post("/api/applications/{aid}/skills/start")
def start_skill_assessment(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")

    job = {"title": a["job_title"], "description": a["job_description"], "skills": a["job_skills"]}
    questions = generate_role_skill_assessment(job, a["job_skills"])

    execq(
        "INSERT INTO skill_assessments(application_id,questions,answers,evaluations,score,completed) "
        "VALUES(?,?,'[]','[]',0,0) "
        "ON CONFLICT(application_id) DO UPDATE SET "
        "questions=excluded.questions,answers='[]',evaluations='[]',score=0,completed=0",
        (aid, json.dumps(questions)),
    )
    # Hide correct answers from candidate while taking test
    safe_questions = [
        {"id": q.get("id"), "skill": q.get("skill"), "question": q.get("question"), "options": q.get("options")}
        for q in questions
    ]
    return {"questions": safe_questions}


@app.post("/api/applications/{aid}/skills/submit")
def submit_skill_assessment(aid: int, x: SkillAssessmentSubmit, u=Depends(current_user)):
    a = application_detail(aid, u)
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")

    sa = a.get("skill_assessment")
    if not sa or not sa.get("questions"):
        raise HTTPException(400, "Start skill assessment first")

    questions = sa["questions"]
    graded = grade_role_skill_assessment(questions, x.answers)
    score = graded.get("score", 0)

    execq(
        "UPDATE skill_assessments SET answers=?,evaluations=?,score=?,completed=1 WHERE application_id=?",
        (json.dumps(x.answers), json.dumps(graded), score, aid),
    )
    return application_detail(aid, u)


@app.get("/api/applications/{aid}/skills")
def get_skills_assessment(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    sa = a.get("skill_assessment")
    if sa and not sa.get("completed") and u["role"] == "candidate":
        # Keep correct_option hidden
        safe_q = [
            {"id": q.get("id"), "skill": q.get("skill"), "question": q.get("question"), "options": q.get("options")}
            for q in sa.get("questions", [])
        ]
        sa["questions"] = safe_q
    return {"skill_assessment": sa}


# ─── 5. Communication & Situational Judgment ──────────────────────────────────

@app.post("/api/applications/{aid}/situational/start")
def start_situational_test(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")

    job = {"title": a["job_title"], "description": a["job_description"], "skills": a["job_skills"]}
    scenarios = generate_situational_scenarios(job)

    execq(
        "INSERT INTO situational_tests(application_id,scenarios,responses,evaluations,score,completed) "
        "VALUES(?,?,'[]','[]',0,0) "
        "ON CONFLICT(application_id) DO UPDATE SET "
        "scenarios=excluded.scenarios,responses='[]',evaluations='[]',score=0,completed=0",
        (aid, json.dumps(scenarios)),
    )
    return {"scenarios": scenarios}


@app.post("/api/applications/{aid}/situational/submit")
def submit_situational_test(aid: int, x: SituationalSubmit, u=Depends(current_user)):
    a = application_detail(aid, u)
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")

    sj = a.get("situational_test")
    if not sj or not sj.get("scenarios"):
        raise HTTPException(400, "Start situational judgment test first")

    scenarios = sj["scenarios"]
    graded = grade_situational_responses(scenarios, x.responses)
    score = graded.get("score", 0)

    execq(
        "UPDATE situational_tests SET responses=?,evaluations=?,score=?,completed=1 WHERE application_id=?",
        (json.dumps(x.responses), json.dumps(graded), score, aid),
    )
    return application_detail(aid, u)


@app.get("/api/applications/{aid}/situational")
def get_situational_test(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    return {"situational_test": a.get("situational_test")}


# ─── explainable AI + analysis ────────────────────────────────────────────────

@app.get("/api/applications/{aid}/explain")
def explain_score(aid: int, u=Depends(current_user)):
    a = application_detail(aid, u)
    return explain_candidate_score(a)


@app.get("/api/recruiter/jobs/{job_id}/analysis")
def job_analysis(job_id: int, u=Depends(current_user)):
    if u["role"] != "recruiter":
        raise HTTPException(403, "Recruiters only")
    j = row("SELECT * FROM jobs WHERE id=? AND recruiter_id=?", (job_id, u["id"]))
    if not j:
        raise HTTPException(404, "Job not found")
    j["skills"] = json.loads(j["skills"])

    app_rows = rows(
        "SELECT a.id, a.resume_score, a.status, a.matched_skills, u.name candidate_name "
        "FROM applications a JOIN users u ON a.candidate_id=u.id WHERE a.job_id=?",
        (job_id,),
    )
    enriched = []
    for ar in app_rows:
        it = row("SELECT score,completed FROM interviews WHERE application_id=?", (ar["id"],))
        ct = row("SELECT score,completed FROM coding_tests WHERE application_id=?", (ar["id"],))
        pv = row("SELECT score,completed FROM project_verifications WHERE application_id=?", (ar["id"],))
        sa = row("SELECT score,completed FROM skill_assessments WHERE application_id=?", (ar["id"],))
        sj = row("SELECT score,completed FROM situational_tests WHERE application_id=?", (ar["id"],))

        iv = it["score"] if it and it["completed"] else 0
        cv = ct["score"] if ct and ct["completed"] else 0
        pv_val = pv["score"] if pv and pv["completed"] else 0
        sa_val = sa["score"] if sa and sa["completed"] else 0
        sj_val = sj["score"] if sj and sj["completed"] else 0

        weights = [("resume", ar["resume_score"], 20)]
        if it and it["completed"]: weights.append(("it", iv, 20))
        if ct and ct["completed"]: weights.append(("ct", cv, 20))
        if pv and pv["completed"]: weights.append(("pv", pv_val, 15))
        if sa and sa["completed"]: weights.append(("sa", sa_val, 15))
        if sj and sj["completed"]: weights.append(("sj", sj_val, 10))

        tot_w = sum(w[2] for w in weights)
        fs = round(sum(w[1] * (w[2] / tot_w) for w in weights), 2)

        enriched.append({
            **ar,
            "matched_skills":       json.loads(ar["matched_skills"]),
            "interview":            {"score": iv, "completed": bool(it and it["completed"])},
            "coding_test":          {"score": cv, "completed": bool(ct and ct["completed"])},
            "project_verification": {"score": pv_val, "completed": bool(pv and pv["completed"])},
            "skill_assessment":     {"score": sa_val, "completed": bool(sa and sa["completed"])},
            "situational_test":     {"score": sj_val, "completed": bool(sj and sj["completed"])},
            "final_score":          fs,
        })
    return recruitment_analysis(j, enriched)


# ─── test scheduling ──────────────────────────────────────────────────────────

@app.post("/api/applications/{aid}/schedule")
def schedule_test(aid: int, x: ScheduleCreate, u=Depends(current_user)):
    if u["role"] != "recruiter":
        raise HTTPException(403, "Recruiters only")
    valid_types = ("interview", "coding", "final", "project", "skills", "situational")
    if x.test_type not in valid_types:
        raise HTTPException(400, f"test_type must be one of {valid_types}")
    application_detail(aid, u)
    sid = execq(
        "INSERT INTO test_schedules(application_id,recruiter_id,test_type,scheduled_at,notes) VALUES(?,?,?,?,?)",
        (aid, u["id"], x.test_type, x.scheduled_at, x.notes or ""),
    )
    return row("SELECT * FROM test_schedules WHERE id=?", (sid,))


@app.get("/api/applications/{aid}/schedules")
def get_schedules(aid: int, u=Depends(current_user)):
    application_detail(aid, u)
    return rows("SELECT * FROM test_schedules WHERE application_id=? ORDER BY scheduled_at ASC", (aid,))


@app.delete("/api/schedules/{sid}")
def delete_schedule(sid: int, u=Depends(current_user)):
    s = row("SELECT * FROM test_schedules WHERE id=?", (sid,))
    if not s:
        raise HTTPException(404, "Schedule not found")
    if s["recruiter_id"] != u["id"]:
        raise HTTPException(403, "Forbidden")
    execq("DELETE FROM test_schedules WHERE id=?", (sid,))
    return {"ok": True}


# ─── recording ────────────────────────────────────────────────────────────────

@app.post("/api/applications/{aid}/recording")
async def upload_recording(aid: int, recording: UploadFile = File(...), u=Depends(current_user)):
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidates only")
    a = row("SELECT candidate_id FROM applications WHERE id=?", (aid,))
    if not a:
        raise HTTPException(404, "Application not found")
    if a["candidate_id"] != u["id"]:
        raise HTTPException(403, "Forbidden")
    data = await recording.read()
    if not data:
        raise HTTPException(400, "Empty recording file")
    try:
        saved = save_recording(data, recording.filename or "recording.webm", aid, u["name"])
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "filename": saved.name, "size_mb": round(len(data) / 1_048_576, 2)}


@app.get("/api/applications/{aid}/recordings")
def get_recordings(aid: int, u=Depends(current_user)):
    a = row("SELECT app.candidate_id, j.recruiter_id FROM applications app JOIN jobs j ON app.job_id=j.id WHERE app.id=?", (aid,))
    if not a:
        raise HTTPException(404, "Application not found")
    if u["role"] == "candidate" and a["candidate_id"] != u["id"]:
        raise HTTPException(403, "Forbidden")
    if u["role"] == "recruiter" and a["recruiter_id"] != u["id"]:
        raise HTTPException(403, "Forbidden")
    return list_recordings(aid)


# ─── recruiter candidates leaderboard ────────────────────────────────────────

@app.get("/api/recruiter/jobs/{job_id}/candidates")
def job_candidates(job_id: int, u=Depends(current_user)):
    if u["role"] != "recruiter":
        raise HTTPException(403, "Recruiters only")
    j = row("SELECT recruiter_id FROM jobs WHERE id=?", (job_id,))
    if not j or j["recruiter_id"] != u["id"]:
        raise HTTPException(404, "Job not found")
    out = []
    for a in rows(
        "SELECT a.id,u.name,u.email,a.resume_score,a.status,a.matched_skills,a.missing_skills "
        "FROM applications a JOIN users u ON a.candidate_id=u.id WHERE a.job_id=?",
        (job_id,),
    ):
        it = row("SELECT score,completed FROM interviews WHERE application_id=?", (a["id"],))
        ct = row("SELECT score,completed FROM coding_tests WHERE application_id=?", (a["id"],))
        pv = row("SELECT score,completed FROM project_verifications WHERE application_id=?", (a["id"],))
        sa = row("SELECT score,completed FROM skill_assessments WHERE application_id=?", (a["id"],))
        sj = row("SELECT score,completed FROM situational_tests WHERE application_id=?", (a["id"],))

        iv = it["score"] if it and it["completed"] else None
        cv = ct["score"] if ct and ct["completed"] else None
        pv_val = pv["score"] if pv and pv["completed"] else None
        sa_val = sa["score"] if sa and sa["completed"] else None
        sj_val = sj["score"] if sj and sj["completed"] else None

        weights = [("resume", a["resume_score"], 20)]
        if iv is not None: weights.append(("it", iv, 20))
        if cv is not None: weights.append(("ct", cv, 20))
        if pv_val is not None: weights.append(("pv", pv_val, 15))
        if sa_val is not None: weights.append(("sa", sa_val, 15))
        if sj_val is not None: weights.append(("sj", sj_val, 10))

        tot_w = sum(w[2] for w in weights)
        fs = round(sum(w[1] * (w[2] / tot_w) for w in weights), 2)

        out.append({
            "id": a["id"], "name": a["name"], "email": a["email"],
            "resume_score": a["resume_score"],
            "interview_score": iv,
            "coding_score": cv,
            "project_score": pv_val,
            "skills_score": sa_val,
            "situational_score": sj_val,
            "final_score": fs,
            "status": a["status"],
            "matched_skills": json.loads(a["matched_skills"]),
            "missing_skills": json.loads(a["missing_skills"]),
        })
    return sorted(out, key=lambda x: x["final_score"], reverse=True)


@app.patch("/api/applications/{aid}/status")
def update_status(aid: int, x: StatusUpdate, u=Depends(current_user)):
    if x.status not in ("applied", "in_review", "shortlisted", "rejected"):
        raise HTTPException(400, "Invalid status")
    application_detail(aid, u)
    execq("UPDATE applications SET status=? WHERE id=?", (x.status, aid))
    return {"ok": True}


# ─── Candidate Support Chatbot ────────────────────────────────────────────────

@app.post("/api/chatbot/message")
def chatbot_message(x: ChatMessage, u=Depends(current_user)):
    """Send a message to the AI chatbot and get a response."""
    session_id = x.session_id or str(uuid.uuid4())

    # Load existing conversation for this session
    conv = row(
        "SELECT * FROM chatbot_conversations WHERE user_id=? AND session_id=?",
        (u["id"], session_id)
    )

    history = []
    if conv:
        try:
            history = json.loads(conv["messages"])
        except Exception:
            history = []

    # Get AI reply
    result = chatbot_reply(x.message, user_role=u["role"], history=history)

    # Append user message + bot reply to history
    history.append({"role": "user",      "content": x.message})
    history.append({"role": "assistant", "content": result["reply"]})

    # Keep last 40 messages (20 exchanges)
    history = history[-40:]
    history_json = json.dumps(history)

    if conv:
        execq(
            "UPDATE chatbot_conversations SET messages=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND session_id=?",
            (history_json, u["id"], session_id)
        )
    else:
        execq(
            "INSERT INTO chatbot_conversations(user_id, session_id, messages) VALUES(?,?,?)",
            (u["id"], session_id, history_json)
        )

    return {
        "reply":        result["reply"],
        "source":       result.get("source", "faq"),
        "quick_replies": result.get("quick_replies", []),
        "session_id":   session_id,
    }


@app.get("/api/chatbot/history")
def chatbot_history(session_id: str, u=Depends(current_user)):
    """Get chat history for a session."""
    conv = row(
        "SELECT * FROM chatbot_conversations WHERE user_id=? AND session_id=?",
        (u["id"], session_id)
    )
    if not conv:
        return {"messages": [], "session_id": session_id}
    try:
        messages = json.loads(conv["messages"])
    except Exception:
        messages = []
    return {"messages": messages, "session_id": session_id}


# ─── Smart Candidate Pipeline ─────────────────────────────────────────────────

@app.get("/api/recruiter/jobs/{job_id}/pipeline")
def get_pipeline(job_id: int, u=Depends(current_user)):
    """
    Returns candidates for a job grouped by status (Kanban-style pipeline),
    with AI-powered next-action recommendations.
    """
    if u["role"] != "recruiter":
        raise HTTPException(403, "Recruiter only")
    job = row("SELECT * FROM jobs WHERE id=? AND recruiter_id=?", (job_id, u["id"]))
    if not job:
        raise HTTPException(404, "Job not found")

    # Load all candidates for this job (same logic as candidates list)
    apps = rows(
        """SELECT a.id, a.status, a.resume_score, a.matched_skills, a.missing_skills,
                  a.candidate_id, u.name AS candidate_name, u.email AS candidate_email,
                  a.created_at
           FROM applications a JOIN users u ON u.id=a.candidate_id
           WHERE a.job_id=?""",
        (job_id,)
    )

    enriched = []
    for a in apps:
        iv   = row("SELECT score, completed FROM interviews      WHERE application_id=?", (a["id"],))
        ct   = row("SELECT score, completed FROM coding_tests     WHERE application_id=?", (a["id"],))
        pv   = row("SELECT score, completed FROM project_verifications WHERE application_id=?", (a["id"],))
        sa   = row("SELECT score, completed FROM skill_assessments WHERE application_id=?", (a["id"],))
        sj   = row("SELECT score, completed FROM situational_tests WHERE application_id=?", (a["id"],))

        iv_val  = iv["score"]  if iv and iv["completed"]  else None
        cv_val  = ct["score"]  if ct and ct["completed"]  else None
        pv_val  = pv["score"]  if pv and pv["completed"]  else None
        sa_val  = sa["score"]  if sa and sa["completed"]  else None
        sj_val  = sj["score"]  if sj and sj["completed"]  else None

        weights = [("resume", a["resume_score"], 20)]
        if iv_val  is not None: weights.append(("iv", iv_val, 20))
        if cv_val  is not None: weights.append(("cv", cv_val, 20))
        if pv_val  is not None: weights.append(("pv", pv_val, 15))
        if sa_val  is not None: weights.append(("sa", sa_val, 15))
        if sj_val  is not None: weights.append(("sj", sj_val, 10))

        tot_w = sum(w[2] for w in weights)
        fs = round(sum(w[1] * (w[2] / tot_w) for w in weights), 2)

        enriched.append({
            "id": a["id"], "candidate_id": a["candidate_id"],
            "candidate_name": a["candidate_name"], "candidate_email": a["candidate_email"],
            "status": a["status"], "resume_score": a["resume_score"],
            "interview_score": iv_val, "coding_score": cv_val,
            "projects_score": pv_val,  "skills_score": sa_val, "situational_score": sj_val,
            "final_score": fs,
            "matched_skills": json.loads(a["matched_skills"]),
            "created_at": a["created_at"],
        })

    # Group by status
    pipeline = {"applied": [], "in_review": [], "shortlisted": [], "rejected": []}
    for c in enriched:
        s = c["status"]
        if s in pipeline:
            pipeline[s].append(c)
        else:
            pipeline["applied"].append(c)

    # AI recommendations
    non_rejected = [c for c in enriched if c["status"] != "rejected"]
    recommendations = generate_pipeline_recommendations(non_rejected)

    return {
        "job": {"id": job["id"], "title": job["title"]},
        "pipeline": pipeline,
        "recommendations": recommendations,
        "total": len(enriched),
    }


# ─── Candidate 360° Profile ───────────────────────────────────────────────────

@app.get("/api/applications/{aid}/profile360")
def profile_360(aid: int, u=Depends(current_user)):
    """
    Returns a comprehensive 360° profile for a candidate application.
    Accessible by both the candidate (own application) and the recruiter (any application for their jobs).
    """
    app_r = application_detail(aid, u)  # reuse existing detail helper (handles auth)

    # Enrich with job skills
    job = row("SELECT skills FROM jobs WHERE id=?", (app_r.get("job_id"),))
    job_skills = []
    if job:
        try: job_skills = json.loads(job["skills"])
        except: job_skills = []
    app_r["job_skills"] = job_skills

    # Enrich with recruiter info
    recruiter = row("SELECT name, email FROM users WHERE id=(SELECT recruiter_id FROM jobs WHERE id=?)", (app_r.get("job_id"),))
    app_r["recruiter_name"]  = recruiter["name"]  if recruiter else ""
    app_r["recruiter_email"] = recruiter["email"] if recruiter else ""

    return build_360_profile(app_r)


# ─── Multi-Job Candidate Matching ─────────────────────────────────────────────

@app.get("/api/candidate/job-matches")
def job_matches(u=Depends(current_user)):
    """
    For candidates: scores all open jobs against the candidate's best resume profile,
    returns top ranked matches with reasoning.
    """
    if u["role"] != "candidate":
        raise HTTPException(403, "Candidate only")

    # Get candidate's best application for resume skills
    best_app = row(
        """SELECT a.resume_text, a.matched_skills, a.resume_score
           FROM applications a
           WHERE a.candidate_id=?
           ORDER BY a.resume_score DESC LIMIT 1""",
        (u["id"],)
    )
    if not best_app:
        return {"matches": [], "message": "Apply to at least one job so we can build your profile."}

    candidate_profile = {
        "resume_text":    best_app.get("resume_text", ""),
        "matched_skills": json.loads(best_app.get("matched_skills", "[]")),
    }

    # Get all applied job IDs for this candidate
    applied = rows("SELECT job_id FROM applications WHERE candidate_id=?", (u["id"],))
    applied_job_ids = {a["job_id"] for a in applied}

    # Get all open jobs
    open_jobs = rows("SELECT id, title, description, skills, location, employment_type, salary, experience FROM jobs WHERE status='open' ORDER BY created_at DESC")
    for j in open_jobs:
        try: j["skills"] = json.loads(j["skills"])
        except: j["skills"] = []

    matches = match_jobs_to_candidate(candidate_profile, open_jobs, applied_job_ids)

    # Return top 10
    return {"matches": matches[:10]}
