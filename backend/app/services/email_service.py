"""
email_service.py – sends Gmail SMTP notifications.

Uses credentials from .env:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

The SMTP_USER is the Gmail account used to authenticate & send.
The recruiter's registered email is set as Reply-To so candidates
can reply directly to the recruiter who posted the vacancy.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from ..config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

logger = logging.getLogger(__name__)


def _send(
    to_list: list[str],
    subject: str,
    body_html: str,
    body_text: str,
    reply_to: str = "",
    reply_to_name: str = "",
) -> bool:
    """
    Internal helper – returns True on success, False on failure.

    :param to_list:       Recipient email addresses
    :param subject:       Email subject line
    :param body_html:     HTML body
    :param body_text:     Plain-text body (fallback)
    :param reply_to:      Reply-To email address (e.g. recruiter's registered email)
    :param reply_to_name: Display name for Reply-To header
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[EMAIL] SMTP credentials not configured in .env – skipping.")
        logger.warning("SMTP credentials not configured – skipping email send.")
        return False
    if not to_list:
        print("[EMAIL] No recipients – skipping.")
        return False
    try:
        print(f"[EMAIL] Connecting to {SMTP_HOST}:{SMTP_PORT} as {SMTP_USER} ...")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        # From: shown as "HireMind <smtp_user@gmail.com>"
        msg["From"] = formataddr(("HireMind", SMTP_FROM or SMTP_USER))
        msg["To"] = ", ".join(to_list)

        # Reply-To: recruiter's registered email — candidates reply directly to them
        if reply_to:
            msg["Reply-To"] = formataddr((reply_to_name, reply_to)) if reply_to_name else reply_to

        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM or SMTP_USER, to_list, msg.as_string())

        print(f"[EMAIL] Successfully sent to {len(to_list)} recipient(s): {to_list}")
        logger.info("Email sent to %s (reply-to: %s)", to_list, reply_to or "—")
        return True
    except Exception as exc:
        print(f"[EMAIL] FAILED to send email: {exc}")
        logger.error("Failed to send email: %s", exc)
        return False


def notify_vacancy(
    job: dict,
    candidate_emails: list[str],
    recruiter_name: str = "",
    recruiter_email: str = "",
) -> bool:
    """
    Send a new-vacancy notification to all registered candidates.

    The email is sent FROM the app's Gmail account (SMTP_USER) but
    Reply-To is set to the recruiter's registered email so candidates
    can contact them directly.

    :param job:              dict with title, description, location, employment_type,
                             experience, salary, skills (list), deadline
    :param candidate_emails: list of recipient email addresses
    :param recruiter_name:   recruiter's registered name (shown in email body + Reply-To)
    :param recruiter_email:  recruiter's registered email (set as Reply-To)
    :return:                 True if sent successfully
    """
    if not candidate_emails:
        return False

    skills_str    = ", ".join(job.get("skills", []) or [])
    deadline_str  = job.get("deadline") or "Open"
    salary_str    = job.get("salary") or "Not specified"
    poster_name   = recruiter_name  or "The Recruiter"
    poster_email  = recruiter_email or ""

    subject = f"New Vacancy: {job['title']} – HireMind"

    # ── Plain-text fallback ────────────────────────────────────────────────────
    body_text = f"""
New Job Opportunity on HireMind!
=================================
Role     : {job['title']}
Location : {job.get('location', 'Remote')}
Type     : {job.get('employment_type', 'Full-time')}
Exp      : {job.get('experience', 0)}+ years
Salary   : {salary_str}
Deadline : {deadline_str}
Skills   : {skills_str}

Posted by: {poster_name}{f' <{poster_email}>' if poster_email else ''}

Description:
{job.get('description', '')}

Log in to HireMind to apply now: http://localhost:5173/jobs

---
Reply to this email to contact the recruiter directly.
"""

    # ── HTML email ─────────────────────────────────────────────────────────────
    recruiter_block = f"""
        <tr><td style="padding:0 40px 24px">
          <table cellpadding="0" cellspacing="0" width="100%"
                 style="background:#f0f4ff;border-radius:10px;padding:16px 20px">
            <tr>
              <td>
                <p style="margin:0 0 4px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.5px">
                  Posted by
                </p>
                <p style="margin:0;font-weight:700;color:#1a1a2e;font-size:15px">{poster_name}</p>
                {'<a href="mailto:' + poster_email + '" style="color:#667eea;font-size:13px;text-decoration:none">' + poster_email + '</a>' if poster_email else ''}
              </td>
              {'<td align="right"><a href="mailto:' + poster_email + '" style="display:inline-block;background:#667eea;color:#fff;text-decoration:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600">Reply to recruiter</a></td>' if poster_email else ''}
            </tr>
          </table>
        </td></tr>
    """ if poster_name or poster_email else ""

    body_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f8;margin:0;padding:0">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:30px 10px">
      <table width="600" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)">

        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:32px 40px">
          <h1 style="color:#fff;margin:0;font-size:24px">HireMind</h1>
          <p style="color:rgba(255,255,255,.85);margin:6px 0 0">New Vacancy Alert</p>
        </td></tr>

        <!-- Job title & meta -->
        <tr><td style="padding:32px 40px 16px">
          <h2 style="color:#1a1a2e;margin:0 0 8px">{job['title']}</h2>
          <p style="color:#667eea;font-weight:600;margin:0 0 20px">
            {job.get('location','Remote')} &nbsp;·&nbsp;
            {job.get('employment_type','Full-time')} &nbsp;·&nbsp;
            {job.get('experience',0)}+ yrs
          </p>
          <table cellpadding="0" cellspacing="0" width="100%"
                 style="border-top:1px solid #f0f0f8;border-bottom:1px solid #f0f0f8;padding:16px 0;margin:0 0 20px">
            <tr>
              <td width="50%"><b>Salary</b><br><span style="color:#555">{salary_str}</span></td>
              <td width="50%"><b>Apply by</b><br><span style="color:#555">{deadline_str}</span></td>
            </tr>
          </table>
          <h3 style="color:#1a1a2e;margin:0 0 8px">Required skills</h3>
          <p style="margin:0 0 16px;color:#555">{skills_str or 'See description'}</p>
          <h3 style="color:#1a1a2e;margin:0 0 8px">About the role</h3>
          <p style="margin:0 0 24px;color:#555;line-height:1.6">
            {job.get('description','')[:600]}{'…' if len(job.get('description',''))>600 else ''}
          </p>
          <a href="http://localhost:5173/jobs"
             style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:600;margin-bottom:24px">
            Apply now →
          </a>
        </td></tr>

        <!-- Recruiter card (registered name + email) -->
        {recruiter_block}

        <!-- Footer -->
        <tr><td style="padding:20px 40px;background:#f9f9fc;color:#999;font-size:12px;text-align:center">
          You're receiving this because you're registered as a candidate on HireMind.<br>
          © 2025 HireMind – AI-powered recruitment
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _send(
        candidate_emails,
        subject,
        body_html,
        body_text,
        reply_to=recruiter_email,
        reply_to_name=recruiter_name,
    )
