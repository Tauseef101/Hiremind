import sqlite3, json
from contextlib import contextmanager
from .config import DB_PATH

@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
        c.commit()
    finally: c.close()

def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('candidate','recruiter')),created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,recruiter_id INTEGER NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,skills TEXT NOT NULL,experience INTEGER DEFAULT 0,location TEXT DEFAULT 'Remote',employment_type TEXT DEFAULT 'Full-time',salary TEXT DEFAULT '',openings INTEGER DEFAULT 1,deadline TEXT DEFAULT '',status TEXT DEFAULT 'open',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(recruiter_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT,candidate_id INTEGER NOT NULL,job_id INTEGER NOT NULL,resume_filename TEXT,resume_text TEXT,resume_score REAL DEFAULT 0,matched_skills TEXT DEFAULT '[]',missing_skills TEXT DEFAULT '[]',experience_score REAL DEFAULT 0,ai_summary TEXT DEFAULT '',status TEXT DEFAULT 'applied',created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(candidate_id,job_id),FOREIGN KEY(candidate_id) REFERENCES users(id),FOREIGN KEY(job_id) REFERENCES jobs(id));
        CREATE TABLE IF NOT EXISTS interviews(id INTEGER PRIMARY KEY AUTOINCREMENT,application_id INTEGER UNIQUE NOT NULL,questions TEXT DEFAULT '[]',answers TEXT DEFAULT '[]',evaluations TEXT DEFAULT '[]',score REAL DEFAULT 0,completed INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(application_id) REFERENCES applications(id));
        CREATE TABLE IF NOT EXISTS coding_tests(id INTEGER PRIMARY KEY AUTOINCREMENT,application_id INTEGER UNIQUE NOT NULL,problem TEXT DEFAULT '',test_cases TEXT DEFAULT '[]',submitted_code TEXT DEFAULT '',execution_result TEXT DEFAULT '{}',score REAL DEFAULT 0,feedback TEXT DEFAULT '',ai_explanation TEXT DEFAULT '',completed INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(application_id) REFERENCES applications(id));
        CREATE TABLE IF NOT EXISTS test_schedules(id INTEGER PRIMARY KEY AUTOINCREMENT,application_id INTEGER NOT NULL,recruiter_id INTEGER NOT NULL,test_type TEXT NOT NULL,scheduled_at TEXT NOT NULL,notes TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(application_id) REFERENCES applications(id),FOREIGN KEY(recruiter_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS project_verifications(id INTEGER PRIMARY KEY AUTOINCREMENT,application_id INTEGER UNIQUE NOT NULL,projects TEXT DEFAULT '[]',portfolio_url TEXT DEFAULT '',portfolio_summary TEXT DEFAULT '',score REAL DEFAULT 0,evaluation TEXT DEFAULT '{}',completed INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(application_id) REFERENCES applications(id));
        CREATE TABLE IF NOT EXISTS skill_assessments(id INTEGER PRIMARY KEY AUTOINCREMENT,application_id INTEGER UNIQUE NOT NULL,questions TEXT DEFAULT '[]',answers TEXT DEFAULT '[]',evaluations TEXT DEFAULT '[]',score REAL DEFAULT 0,completed INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(application_id) REFERENCES applications(id));
        CREATE TABLE IF NOT EXISTS situational_tests(id INTEGER PRIMARY KEY AUTOINCREMENT,application_id INTEGER UNIQUE NOT NULL,scenarios TEXT DEFAULT '[]',responses TEXT DEFAULT '[]',evaluations TEXT DEFAULT '[]',score REAL DEFAULT 0,completed INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(application_id) REFERENCES applications(id));
        CREATE TABLE IF NOT EXISTS chatbot_conversations(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,session_id TEXT NOT NULL,messages TEXT DEFAULT '[]',created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE UNIQUE INDEX IF NOT EXISTS idx_chatbot_session ON chatbot_conversations(user_id,session_id);
        ''')

def row(q,p=()):
    with conn() as c:
        r=c.execute(q,p).fetchone(); return dict(r) if r else None

def rows(q,p=()):
    with conn() as c: return [dict(x) for x in c.execute(q,p).fetchall()]

def execq(q,p=()):
    with conn() as c:
        cur=c.execute(q,p); return cur.lastrowid
