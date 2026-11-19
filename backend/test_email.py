import sys
sys.path.insert(0, '.')

from app.database import rows

candidates = rows("SELECT id, name, email FROM users WHERE role='candidate'")
recruiters = rows("SELECT id, name, email FROM users WHERE role='recruiter'")

print("=== CANDIDATES IN DB ===")
for c in candidates:
    print(f"  id={c['id']}  name={c['name']}  email={c['email']}")

print(f"\n=== RECRUITERS IN DB ===")
for r in recruiters:
    print(f"  id={r['id']}  name={r['name']}  email={r['email']}")

print(f"\nTotal candidates: {len(candidates)}")
print(f"Total recruiters: {len(recruiters)}")

if not candidates:
    print("\n[!] No candidates registered — email has nobody to send to!")

# Now test notify_vacancy end-to-end
if candidates:
    print("\n=== TESTING notify_vacancy ===")
    from app.services.email_service import notify_vacancy
    job = {
        "title": "Test Job",
        "description": "This is a test vacancy notification.",
        "location": "Remote",
        "employment_type": "Full-time",
        "experience": 2,
        "salary": "6-10 LPA",
        "skills": ["python", "sql"],
        "deadline": "2024-12-31",
    }
    emails = [c["email"] for c in candidates]
    print(f"Sending to: {emails}")
    result = notify_vacancy(job, emails, recruiters[0]["name"] if recruiters else "Recruiter", recruiters[0]["email"] if recruiters else "")
    print(f"Result: {'SUCCESS' if result else 'FAILED'}")
