import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Routes, Route, Navigate, useNavigate, useParams, Link, useLocation,
} from "react-router-dom";
import {
  LayoutDashboard, BriefcaseBusiness, FileText, Users, LogOut, Plus,
  ChevronRight, Sparkles, ShieldCheck, Video, StopCircle, RefreshCw,
  AlertCircle, Code2, Brain, BarChart3, Calendar, CheckCircle2,
  XCircle, Clock, Trophy, Target, Zap, FolderGit2, Compass, MessageSquareCode,
  Layers, ExternalLink, Send, Trash2, MessageCircle, X, Bot, Briefcase,
  Star, TrendingUp, User, Activity, GitBranch, Kanban, ChevronDown,
} from "lucide-react";
import { api } from "./lib/api";
import { motion } from "framer-motion";

// ─── useFetch ─────────────────────────────────────────────────────────────────
function useFetch(apiFn, deps = []) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");
  const fetch = useCallback(() => {
    setLoading(true); setError("");
    apiFn().then(d => { setData(d); setLoading(false); })
           .catch(e => { setError(e.message); setLoading(false); });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { fetch(); }, [fetch]);
  return { data, loading, error, refetch: fetch };
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
function Loader() {
  return (
    <div style={{ padding: "64px 0", textAlign: "center", color: "#10b981" }}>
      <div style={{
        width: 48, height: 48, margin: "0 auto", borderRadius: "50%",
        background: "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%)",
        display: "flex", alignItems: "center", justifyContent: "center",
        boxShadow: "0 4px 16px rgba(16, 185, 129, 0.2)"
      }}>
        <RefreshCw size={24} style={{ animation: "spin 1s linear infinite", color: "#10b981" }} />
      </div>
      <p style={{ marginTop: 14, color: "var(--ink-muted)", fontSize: "0.88rem", fontWeight: 600 }}>Loading workspace…</p>
      <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}

function ErrBanner({ message, onRetry }) {
  return (
    <div style={{ margin: "16px 0", padding: "14px 18px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, display: "flex", alignItems: "flex-start", gap: 12, color: "#ef4444", boxShadow: "0 2px 8px rgba(239, 68, 68, 0.06)" }}>
      <AlertCircle size={20} style={{ flexShrink: 0, marginTop: 1 }} />
      <div style={{ flex: 1 }}>
        <strong style={{ fontSize: "0.9rem", color: "#b91c1c" }}>Action needed</strong>
        <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#dc2626", lineHeight: 1.5 }}>{message}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} style={{ background: "#ef4444", color: "#fff", border: "none", borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontSize: "0.8rem", fontWeight: 700, boxShadow: "0 2px 8px rgba(239, 68, 68, 0.25)" }}>Retry</button>
      )}
    </div>
  );
}

function ScoreBar({ label, value, max = 100, color = "#10b981", weight }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", marginBottom: 6 }}>
        <span style={{ fontWeight: 600, color: "var(--ink)" }}>{label}</span>
        <span style={{ fontWeight: 700, color: color }}>
          {Math.round(value)}
          <span style={{ color: "var(--ink-faint)", fontWeight: 500, fontSize: "0.78rem" }}>/{max}{weight ? ` (${weight}%)` : ""}</span>
        </span>
      </div>
      <div style={{ height: 8, background: "#f1f5f9", borderRadius: 99, overflow: "hidden", border: "1px solid #e2e8f0" }}>
        <div style={{
          height: "100%", width: `${pct}%`,
          background: color.startsWith("#") ? `linear-gradient(90deg, ${color}, ${color}dd)` : color,
          borderRadius: 99,
          boxShadow: `0 0 10px ${color}40`,
          transition: "width 0.8s cubic-bezier(0.16, 1, 0.3, 1)"
        }} />
      </div>
    </div>
  );
}

function Badge({ label, color = "#10b981", bg = "#ecfdf5" }) {
  return (
    <span style={{
      background: bg,
      color: color,
      border: `1px solid ${color}30`,
      borderRadius: 99,
      padding: "3px 11px",
      fontSize: "0.76rem",
      fontWeight: 700,
      marginRight: 6,
      marginBottom: 4,
      display: "inline-flex",
      alignItems: "center",
      gap: 5,
      boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)"
    }}>
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: color, display: "inline-block" }} />
      {label}
    </span>
  );
}

// ─── Shell ────────────────────────────────────────────────────────────────────
function Shell({ children }) {
  const u = JSON.parse(localStorage.getItem("user") || "null");
  const nav = useNavigate(), loc = useLocation();
  if (!u) return <Navigate to="/login" />;
  const candidate = u.role === "candidate";
  const links = candidate
    ? [["/candidate","Dashboard",LayoutDashboard],["/jobs","Find Jobs",BriefcaseBusiness],["/applications","My Applications",FileText]]
    : [["/recruiter","Overview",LayoutDashboard],["/recruiter/jobs","Jobs",BriefcaseBusiness],["/recruiter/candidates","Candidates",Users]];
  return (
    <div className="app">
      <aside>
        <Link className="brand" to="/"><span className="logo"><Sparkles /></span>Hire<span>Mind</span></Link>
        <div className="role">{candidate ? "CANDIDATE WORKSPACE" : "RECRUITER WORKSPACE"}</div>
        {links.map(([p,n,I]) => <Link className={loc.pathname===p?"nav active":"nav"} to={p} key={p}><I size={18}/>{n}</Link>)}
        <div className="sideBottom">
          <div className="userMini"><div className="avatar">{u.name[0]}</div><div><b>{u.name}</b><small>{u.email}</small></div></div>
          <button className="ghost" onClick={() => { localStorage.clear(); nav("/login"); }}><LogOut size={17}/> Sign out</button>
        </div>
      </aside>
      <main>
        <div className="topbar"><div className="crumb">AI-powered recruitment workspace</div><div className="secure"><ShieldCheck size={15}/> Secure session</div></div>
        {children}
      </main>
      <ChatbotWidget user={u} />
    </div>
  );
}


// ─── Landing ──────────────────────────────────────────────────────────────────
function Landing() {
  return (
    <div className="landing">
      <nav>
        <Link className="brand" to="/"><span className="logo"><Sparkles /></span>Hire<span>Mind</span></Link>
        <div><Link to="/login" className="navLink">Sign in</Link><Link to="/register" className="btn small">Get started <ChevronRight size={16}/></Link></div>
      </nav>
      <section className="hero">
        <div className="heroCopy">
          <div className="eyebrow"><Sparkles size={15}/> AGENTIC AI RECRUITMENT</div>
          <h1>Hire with <em>evidence,</em><br/>not guesswork.</h1>
          <p>Resume intelligence, AI interviews, Python coding tests, Project verification, Role skill assessments, and Situational judgment.</p>
          <div className="heroBtns"><Link to="/register" className="btn">Build your shortlist <ChevronRight/></Link><Link to="/login" className="textBtn">Explore workspace →</Link></div>
        </div>
        <div className="heroVisual">
          <div className="orbit">
            <div className="orbitCore"><Sparkles/><b>AI</b><small>Recruitment Engine</small></div>
            <div className="float f1">Interview <strong>88%</strong></div>
            <div className="float f2">Projects <strong>94%</strong></div>
            <div className="float f3">Judgment <strong>91%</strong></div>
          </div>
        </div>
      </section>
      <section className="featureRow">
        <Feature n="01" t="Resume & AI Interview" d="Extract skills, conduct live video-recorded adaptive interviews." />
        <Feature n="02" t="Code & Project Verification" d="Real-time Python coding test and automated GitHub/live project verification." />
        <Feature n="03" t="Role Skills & Situational SJT" d="Domain technical assessment and workplace communication judgment tests." />
      </section>
    </div>
  );
}
function Feature({ n, t, d }) { return <div className="feature"><span>{n}</span><h3>{t}</h3><p>{d}</p></div>; }

// ─── Auth ─────────────────────────────────────────────────────────────────────
function Auth({ register = false }) {
  const nav = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "candidate" });
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault(); setBusy(true);
    try {
      const d = register ? await api.register(form) : await api.login({ email: form.email, password: form.password });
      localStorage.setItem("token", d.token); localStorage.setItem("user", JSON.stringify(d.user));
      nav(d.user.role === "candidate" ? "/candidate" : "/recruiter");
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  }
  return (
    <div className="authPage">
      <div className="authArt">
        <Link className="brand" to="/"><span className="logo"><Sparkles/></span>Hire<span>Mind</span></Link>
        <div><div className="eyebrow">SMARTER TALENT DECISIONS</div><h1>{register?"Build your professional profile.":"Welcome back."}</h1></div>
      </div>
      <div className="authCard">
        <div className="eyebrow">{register?"CREATE ACCOUNT":"SECURE SIGN IN"}</div>
        <h2>{register?"Start your journey":"Sign in to HireMind"}</h2>
        <form onSubmit={submit}>
          {register && <input placeholder="Full name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/>}
          <input type="email" placeholder="Email address" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
          <input type="password" placeholder="Password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
          {register && <div className="rolePick">
            <button type="button" className={form.role==="candidate"?"selected":""} onClick={()=>setForm({...form,role:"candidate"})}>🎓 Candidate</button>
            <button type="button" className={form.role==="recruiter"?"selected":""} onClick={()=>setForm({...form,role:"recruiter"})}>💼 Recruiter</button>
          </div>}
          {err && <div className="error">{err}</div>}
          <button className="btn full" disabled={busy}>{busy?"Please wait…":(register?"Create workspace":"Sign in")} <ChevronRight/></button>
        </form>
        <p className="switch">{register?"Already have an account? ":"New to HireMind? "}<Link to={register?"/login":"/register"}>{register?"Sign in":"Create an account"}</Link></p>
      </div>
    </div>
  );
}

// ─── Candidate Dashboard ──────────────────────────────────────────────────────
function Candidate() {
  const { data: apps, loading, error, refetch } = useFetch(() => api.applications());
  const { data: matchData } = useFetch(() => api.jobMatches());
  const list = apps || [];
  const matches = matchData?.matches || [];
  return (
    <Shell>
      <PageTitle eyebrow="CANDIDATE WORKSPACE" title="Your career cockpit." sub="Complete full assessments: Interview, Coding, Projects, Role Skills & Situational Judgment" />
      {loading && <Loader/>} {error && <ErrBanner message={error} onRetry={refetch}/>}
      {!loading && !error && <>
        <div className="stats">
          <Stat t="Applications" v={list.length}/>
          <Stat t="Interviews done" v={list.filter(a=>a.interview?.completed).length}/>
          <Stat t="Coding tests" v={list.filter(a=>a.coding_test?.completed).length}/>
          <Stat t="Top fit score" v={list.length?Math.max(...list.map(a=>a.final_score)):"—"}/>
        </div>
        <div className="sectionHead"><div><h2>Active applications</h2></div><Link to="/jobs" className="btn small">Find jobs <ChevronRight size={16}/></Link></div>
        <div className="cards">{list.map(a=><ApplicationCard key={a.id} a={a}/>)}</div>
        {!list.length && <Empty text="No applications yet. Start by exploring open roles."/>}
        {matches.length > 0 && <JobMatches matches={matches} />}
      </>}
    </Shell>
  );
}
function Stat({ t, v }) { return <div className="stat"><span>{t}</span><strong>{v}</strong></div>; }
function PageTitle({ eyebrow, title, sub }) {
  return <div className="pageTitle"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div></div>;
}
function ApplicationCard({ a }) {
  const nav = useNavigate();
  return (
    <motion.div whileHover={{ y: -4 }} className="card appCard">
      <div className="cardTop">
        <div><span className="status">{a.status.replace("_"," ")}</span><h3>{a.job_title}</h3><p>{a.location} · {a.employment_type}</p></div>
        <div className="scoreRing"><b>{Math.round(a.final_score)}</b><small>FIT</small></div>
      </div>
      <div className="barLabel"><span>Composite fit</span><b>{Math.round(a.final_score)}%</b></div>
      <div className="bar"><i style={{width:`${Math.min(100, a.final_score)}%`}}/></div>
      <div style={{display:"flex",gap:4,marginTop:8,flexWrap:"wrap"}}>
        <Badge label={a.interview?.completed?"✓ Interview":"Interview"} color={a.interview?.completed?"#22c55e":"#6b7280"} bg={a.interview?.completed?"#f0fdf4":"#f3f4f6"}/>
        <Badge label={a.coding_test?.completed?"✓ Code":"Code"} color={a.coding_test?.completed?"#22c55e":"#6b7280"} bg={a.coding_test?.completed?"#f0fdf4":"#f3f4f6"}/>
        <Badge label={a.project_verification?.completed?"✓ Projects":"Projects"} color={a.project_verification?.completed?"#22c55e":"#6b7280"} bg={a.project_verification?.completed?"#f0fdf4":"#f3f4f6"}/>
        <Badge label={a.skill_assessment?.completed?"✓ Skills":"Skills"} color={a.skill_assessment?.completed?"#22c55e":"#6b7280"} bg={a.skill_assessment?.completed?"#f0fdf4":"#f3f4f6"}/>
        <Badge label={a.situational_test?.completed?"✓ SJT":"SJT"} color={a.situational_test?.completed?"#22c55e":"#6b7280"} bg={a.situational_test?.completed?"#f0fdf4":"#f3f4f6"}/>
      </div>
      <div className="cardFoot">
        <span>{a.final_score > 0 ? `Overall Score: ${a.final_score}` : "In progress"}</span>
        <button className="textBtn" onClick={()=>nav("/application/"+a.id)}>Open <ChevronRight size={15}/></button>
      </div>
    </motion.div>
  );
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────
function Jobs() {
  const { data: jobs, loading, error, refetch } = useFetch(() => api.jobs());
  const list = jobs || [];
  return (
    <Shell>
      <PageTitle eyebrow="OPPORTUNITIES" title="Find your next role." sub="Comprehensive candidate evaluation: resume, interview, coding, projects, skills, and situational judgment."/>
      {loading && <Loader/>} {error && <ErrBanner message={error} onRetry={refetch}/>}
      {!loading && !error && <div className="jobGrid">
        {list.map(j=>(
          <motion.div whileHover={{y:-4}} className="card jobCard" key={j.id}>
            <div className="jobIcon"><BriefcaseBusiness/></div>
            <span className="status">OPEN · {j.employment_type}</span>
            <h3>{j.title}</h3>
            <p>{j.description.slice(0,150)}{j.description.length>150?"…":""}</p>
            <div className="chips">{j.skills.slice(0,5).map(s=><span key={s}>{s}</span>)}</div>
            <div className="jobMeta"><span>{j.location}</span><span>{j.experience}+ yrs</span></div>
            <Link className="btn full" to={"/apply/"+j.id}>Analyze my resume <ChevronRight/></Link>
          </motion.div>
        ))}
        {!list.length && <Empty text="No open roles at the moment."/>}
      </div>}
    </Shell>
  );
}

// ─── Apply ────────────────────────────────────────────────────────────────────
function Apply() {
  const { id } = useParams();
  const { data: jobs, loading, error, refetch } = useFetch(() => api.jobs(), [id]);
  const job = (jobs||[]).find(x=>String(x.id)===id);
  const [file,setFile]=useState(null); const [result,setResult]=useState(null);
  const [busy,setBusy]=useState(false); const [applyErr,setApplyErr]=useState("");
  async function go() {
    if(!file)return; setBusy(true); setApplyErr("");
    try { setResult(await api.upload(id,file)); } catch(e) { setApplyErr(e.message); } finally { setBusy(false); }
  }
  return (
    <Shell>
      {loading&&<Loader/>} {error&&<ErrBanner message={error} onRetry={refetch}/>}
      {!loading&&!error&&!job&&<Empty text="Job not found."/>}
      {!loading&&!error&&job&&<>
        <PageTitle eyebrow="APPLICATION" title={job.title} sub={`${job.location} · ${job.employment_type} · ${job.experience}+ yrs`}/>
        <div className="stage">
          <div className="stageRail">
            <Step n="01" t="Resume" active/>
            <Step n="02" t="Interview"/>
            <Step n="03" t="Coding"/>
            <Step n="04" t="Projects"/>
            <Step n="05" t="Skills"/>
            <Step n="06" t="SJT"/>
            <Step n="07" t="Results"/>
          </div>
          <div className="card uploadCard">
            <div className="eyebrow">STEP 01 · RESUME INTELLIGENCE</div><h2>Upload your resume.</h2>
            <label className="dropzone">
              <input type="file" accept=".pdf,.docx,.txt" onChange={e=>setFile(e.target.files[0])}/>
              <FileText size={34}/><b>{file?file.name:"Drop your resume here"}</b><span>PDF, DOCX or TXT</span>
            </label>
            {applyErr&&<ErrBanner message={applyErr}/>}
            <button disabled={!file||busy} onClick={go} className="btn full">{busy?"Analyzing…":"Analyze resume"} <Sparkles size={17}/></button>
            {result&&<div className="analysis">
              <div className="bigScore"><strong>{Math.round(result.resume_score)}</strong><span>/100 resume fit</span></div>
              <p><b>Matched:</b> {result.matched_skills.join(", ")||"None"}</p>
              <p><b>Missing:</b> {result.missing_skills.join(", ")||"None"}</p>
              <Link className="btn" to={"/application/"+result.id}>Start Assessment Journey <ChevronRight/></Link>
            </div>}
          </div>
        </div>
      </>}
    </Shell>
  );
}
function Step({ n, t, active }) { return <div className={active?"step active":"step"}><span>{n}</span>{t}</div>; }

// ─── VideoRecorder ────────────────────────────────────────────────────────────
function VideoRecorder({ applicationId }) {
  const videoRef=useRef(null); const mrRef=useRef(null); const chunksRef=useRef([]);
  const [recording,setRecording]=useState(false); const [uploading,setUploading]=useState(false);
  const [uploaded,setUploaded]=useState(false); const [err,setErr]=useState("");
  async function startRecording() {
    setErr(""); setUploaded(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({video:true,audio:true});
      if(videoRef.current){videoRef.current.srcObject=stream;videoRef.current.muted=true;videoRef.current.play();}
      chunksRef.current=[];
      const mr=new MediaRecorder(stream,{mimeType:"video/webm;codecs=vp9,opus"});
      mr.ondataavailable=e=>{if(e.data?.size>0)chunksRef.current.push(e.data);};
      mr.onstop=async()=>{
        const blob=new Blob(chunksRef.current,{type:"video/webm"});
        if(!blob.size)return; setUploading(true);
        try{await api.uploadRecording(applicationId,blob);setUploaded(true);}
        catch(e){setErr("Upload failed: "+e.message);}finally{setUploading(false);}
      };
      mr.start(1000); mrRef.current=mr; setRecording(true);
    } catch(e){setErr("Camera/mic denied: "+e.message);}
  }
  function stopRecording(){if(mrRef.current&&recording){mrRef.current.stop();mrRef.current.stream.getTracks().forEach(t=>t.stop());setRecording(false);}}
  return (
    <div style={{marginBottom:"1.5rem",padding:"16px",background:"#f8fafc",borderRadius:12,border:"1px solid #e2e8f0"}}>
      <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
        <Video size={16} style={{color:recording?"#ef4444":"var(--accent)"}}/><strong style={{fontSize:"0.88rem",color:"var(--ink)"}}>Record your interview session</strong>
        {recording&&<span style={{color:"#ef4444",fontSize:"0.78rem",fontWeight:700}}>● REC</span>}
      </div>
      <video ref={videoRef} width="240" height="135" style={{borderRadius:8,background:"#000",display:"block",marginBottom:8}}/>
      <div style={{display:"flex",gap:8}}>
        {!recording?<button className="btn small" onClick={startRecording} disabled={uploading||uploaded}><Video size={14}/> Start camera</button>
                   :<button className="btn small" style={{background:"#ef4444"}} onClick={stopRecording}><StopCircle size={14}/> Stop & save</button>}
      </div>
      {uploading&&<p style={{color:"var(--accent)",fontSize:"0.8rem",marginTop:6}}>Uploading…</p>}
      {uploaded&&<p style={{color:"#10b981",fontSize:"0.8rem",marginTop:6}}>✓ Video saved</p>}
      {err&&<p style={{color:"#ef4444",fontSize:"0.8rem",marginTop:6}}>{err}</p>}
    </div>
  );
}

// ─── CodingTest ───────────────────────────────────────────────────────────────
function CodingTest({ applicationId, codingTest, onComplete }) {
  const [problem, setProblem] = useState(codingTest?.problem || null);
  const [code, setCode]       = useState("# Write your Python solution here\n\n");
  const [busy, setBusy]       = useState(false);
  const [err, setErr]         = useState("");
  const [started, setStarted] = useState(!!codingTest?.problem);

  async function start() {
    setBusy(true); setErr("");
    try {
      const d = await api.startCoding(applicationId);
      setProblem(d.problem); setStarted(true);
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  }

  async function submit() {
    if (!code.trim() || code.trim() === "# Write your Python solution here") {
      return setErr("Please write some code before submitting.");
    }
    setBusy(true); setErr("");
    try {
      const result = await api.submitCoding(applicationId, code);
      onComplete(result);
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  }

  if (!started) return (
    <div className="card interviewIntro">
      <div className="iconBox"><Code2/></div>
      <div>
        <div className="eyebrow">STEP 03 · PYTHON CODING TEST</div>
        <h2>Ready for a coding challenge?</h2>
        <p>A Python programming task tailored to this role. Run and test against hidden validation cases.</p>
        {err && <ErrBanner message={err}/>}
        <button className="btn" onClick={start} disabled={busy}>
          {busy?"Generating problem…":"Start coding test"} <Code2 size={16}/>
        </button>
      </div>
    </div>
  );

  const prob = typeof problem === "string" ? JSON.parse(problem) : problem;
  return (
    <div className="card" style={{padding:0,overflow:"hidden"}}>
      <div style={{background:"linear-gradient(135deg, #061714 0%, #0a2420 100%)",padding:"22px 28px",color:"#fff",borderBottom:"1px solid rgba(16,185,129,0.15)"}}>
        <div style={{fontSize:"0.75rem",opacity:0.8,marginBottom:4,color:"#34d399",fontWeight:700}}>STEP 03 · PYTHON CODING TEST</div>
        <h2 style={{margin:0,fontSize:"1.3rem",color:"#fff"}}>{prob?.title || "Python Challenge"}</h2>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:0,minHeight:480}}>
        <div style={{padding:"24px",borderRight:"1px solid #e2e8f0",overflowY:"auto",maxHeight:600}}>
          <h3 style={{marginTop:0,color:"var(--ink)"}}>Problem Statement</h3>
          <p style={{lineHeight:1.7,color:"var(--ink-secondary)"}}>{prob?.description}</p>
          {prob?.function_signature && <>
            <h4 style={{color:"var(--accent)"}}>Function Signature</h4>
            <pre style={{background:"#f1f5f9",padding:"10px 14px",borderRadius:8,fontSize:"0.85rem",overflow:"auto",border:"1px solid #e2e8f0"}}>{prob.function_signature}</pre>
          </>}
          {prob?.examples?.length > 0 && <>
            <h4 style={{color:"var(--accent)"}}>Examples</h4>
            {prob.examples.map((ex,i)=>(
              <div key={i} style={{background:"#f8fafc",padding:"10px 14px",borderRadius:8,marginBottom:8,fontSize:"0.84rem",border:"1px solid #e2e8f0"}}>
                <div><b>Input:</b> <code>{ex.input}</code></div>
                <div><b>Output:</b> <code>{ex.output}</code></div>
              </div>
            ))}
          </>}
        </div>
        <div style={{display:"flex",flexDirection:"column",padding:"24px"}}>
          <h3 style={{marginTop:0,color:"#1a1a2e",display:"flex",alignItems:"center",gap:8}}><Code2 size={16}/> Your Solution (Python)</h3>
          <textarea
            value={code}
            onChange={e=>setCode(e.target.value)}
            style={{flex:1,minHeight:300,fontFamily:"'Fira Code','Courier New',monospace",fontSize:"0.9rem",lineHeight:1.6,padding:"14px",border:"2px solid #e0e0f8",borderRadius:10,resize:"vertical",outline:"none",background:"#1a1a2e",color:"#e8e8ff",tabSize:4}}
            onKeyDown={e=>{if(e.key==="Tab"){e.preventDefault();const s=e.target.selectionStart,end=e.target.selectionEnd;setCode(code.substring(0,s)+"    "+code.substring(end));setTimeout(()=>{e.target.selectionStart=e.target.selectionEnd=s+4},0);}}}
            spellCheck={false}
          />
          {err && <ErrBanner message={err}/>}
          <button className="btn full" onClick={submit} disabled={busy} style={{marginTop:12}}>
            {busy?"Running tests…":"Submit solution"} <CheckCircle2 size={16}/>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── ProjectVerification Component ───────────────────────────────────────────
function ProjectVerification({ applicationId, projectData, onComplete }) {
  const [projects, setProjects] = useState(
    projectData?.projects?.length ? projectData.projects : [
      { title: "", description: "", github_url: "", live_url: "", technologies: "" }
    ]
  );
  const [portfolioUrl, setPortfolioUrl] = useState(projectData?.portfolio_url || "");
  const [portfolioSummary, setPortfolioSummary] = useState(projectData?.portfolio_summary || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr]   = useState("");

  const addProject = () => {
    setProjects([...projects, { title: "", description: "", github_url: "", live_url: "", technologies: "" }]);
  };

  const removeProject = (index) => {
    if (projects.length <= 1) return;
    setProjects(projects.filter((_, i) => i !== index));
  };

  const updateProject = (index, field, value) => {
    const copy = [...projects];
    copy[index][field] = value;
    setProjects(copy);
  };

  async function submit(e) {
    e.preventDefault();
    const valid = projects.filter(p => p.title.trim() && p.description.trim());
    if (!valid.length) {
      return setErr("Please specify at least one project with a title and description.");
    }
    setBusy(true); setErr("");
    try {
      const payload = {
        projects: valid.map(p => ({
          ...p,
          technologies: typeof p.technologies === "string" ? p.technologies.split(",").map(t => t.trim()).filter(Boolean) : (p.technologies || []),
        })),
        portfolio_url: portfolioUrl,
        portfolio_summary: portfolioSummary,
      };
      const res = await api.verifyProjects(applicationId, payload);
      onComplete(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card" style={{padding:"28px 32px"}}>
      <div className="eyebrow">STEP 04 · PROJECT & PORTFOLIO VERIFICATION</div>
      <h2 style={{marginTop:4,display:"flex",alignItems:"center",gap:10}}>
        <FolderGit2 size={24} color="#10b981"/> Project & Evidence Verification
      </h2>
      <p style={{color:"#666",fontSize:"0.9rem",lineHeight:1.6}}>
        Provide real-world projects, GitHub repositories, and deployed links. Our AI verifies technical stack alignment, code authenticity, and architecture depth.
      </p>

      <form onSubmit={submit} style={{marginTop:20}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:24,background:"#f8fafc",padding:16,borderRadius:10}}>
          <label className="field"><span>Portfolio / Website Link (optional)</span>
            <input placeholder="https://yourportfolio.dev or GitHub profile" value={portfolioUrl} onChange={e=>setPortfolioUrl(e.target.value)}/>
          </label>
          <label className="field"><span>Portfolio Summary (optional)</span>
            <input placeholder="Brief overview of your engineering background & focus" value={portfolioSummary} onChange={e=>setPortfolioSummary(e.target.value)}/>
          </label>
        </div>

        {projects.map((p, idx) => (
          <div key={idx} style={{border:"1px solid #e2e8f0",borderRadius:12,padding:20,marginBottom:18,background:"#fff"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
              <strong style={{color:"#1e293b",fontSize:"0.95rem"}}>Project #{idx + 1}</strong>
              {projects.length > 1 && (
                <button type="button" onClick={()=>removeProject(idx)} style={{background:"none",border:"none",color:"#ef4444",cursor:"pointer",display:"flex",alignItems:"center",gap:4,fontSize:"0.8rem"}}>
                  <Trash2 size={14}/> Remove
                </button>
              )}
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:12}}>
              <label className="field"><span>Project Title *</span>
                <input required placeholder="e.g. Distributed Task Queue" value={p.title} onChange={e=>updateProject(idx,"title",e.target.value)}/>
              </label>
              <label className="field"><span>Technologies / Libraries (comma-separated)</span>
                <input placeholder="e.g. Python, Redis, FastAPI, Docker" value={p.technologies} onChange={e=>updateProject(idx,"technologies",e.target.value)}/>
              </label>
              <label className="field"><span>GitHub Repository URL</span>
                <input placeholder="https://github.com/username/repo" value={p.github_url} onChange={e=>updateProject(idx,"github_url",e.target.value)}/>
              </label>
              <label className="field"><span>Live Demo / Production URL</span>
                <input placeholder="https://demo.app" value={p.live_url} onChange={e=>updateProject(idx,"live_url",e.target.value)}/>
              </label>
            </div>

            <label className="field"><span>Project Description, Architecture & Your Role *</span>
              <textarea required rows={3} placeholder="Describe the problem, architectural choices, scale, and specific contributions..." value={p.description} onChange={e=>updateProject(idx,"description",e.target.value)}/>
            </label>
          </div>
        ))}

        <div style={{display:"flex",gap:12,alignItems:"center",marginTop:16}}>
          <button type="button" onClick={addProject} className="btn small" style={{background:"#f1f5f9",color:"#334155"}}>
            <Plus size={15}/> Add Another Project
          </button>
        </div>

        {err && <ErrBanner message={err}/>}

        <button type="submit" className="btn full" disabled={busy} style={{marginTop:20,background:"linear-gradient(135deg,#10b981,#059669)"}}>
          {busy ? "Verifying with AI Engine…" : "Submit & Verify Projects"} <Sparkles size={16}/>
        </button>
      </form>
    </div>
  );
}

function ProjectResults({ pv }) {
  const ev = pv.evaluation || {};
  return (
    <div className="card" style={{padding:"28px 32px",marginBottom:20}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16}}>
        <div>
          <div className="eyebrow">PROJECT & PORTFOLIO VERIFIED</div>
          <h2 style={{margin:"4px 0",display:"flex",alignItems:"center",gap:10}}>
            <FolderGit2 color="#10b981"/> Project Verification Results
          </h2>
          <p style={{color:"#64748b",fontSize:"0.88rem",marginTop:2}}>AI code authenticity and stack alignment evaluation</p>
        </div>
        <div style={{background:"#ecfdf5",border:"2px solid #10b981",borderRadius:12,padding:"10px 20px",textAlign:"center"}}>
          <div style={{fontSize:"2rem",fontWeight:900,color:"#10b981"}}>{Math.round(pv.score)}</div>
          <div style={{fontSize:"0.78rem",fontWeight:700,color:"#047857",textTransform:"uppercase"}}>{ev.status?.replace("_"," ") || "Verified"}</div>
        </div>
      </div>

      <div style={{background:"#f8fafc",borderRadius:10,padding:16,marginTop:16}}>
        <p style={{margin:0,lineHeight:1.7,color:"#334155",fontSize:"0.92rem"}}>{ev.summary || "Candidate submitted project portfolio."}</p>
      </div>

      {ev.project_evaluations?.length > 0 && (
        <div style={{marginTop:20}}>
          <h4 style={{color:"#1e293b",marginBottom:12}}>Project Breakdown</h4>
          <div style={{display:"grid",gap:12}}>
            {ev.project_evaluations.map((p, i) => (
              <div key={i} style={{border:"1px solid #e2e8f0",borderRadius:8,padding:14,background:"#fff"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <strong style={{color:"#0f172a"}}>{p.title}</strong>
                  <Badge label={`${Math.round(p.relevance_score || 0)}% fit`} color="#10b981" bg="#ecfdf5"/>
                </div>
                <p style={{margin:"6px 0 0",fontSize:"0.84rem",color:"#64748b"}}>{p.notes}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginTop:20}}>
        {ev.strengths?.length > 0 && (
          <div style={{background:"#f0fdf4",padding:14,borderRadius:8}}>
            <strong style={{color:"#166534",fontSize:"0.85rem",display:"block",marginBottom:6}}>Key Strengths</strong>
            {ev.strengths.map((s,i)=><div key={i} style={{fontSize:"0.82rem",color:"#15803d",marginBottom:4}}>✓ {s}</div>)}
          </div>
        )}
        {ev.gaps?.length > 0 && (
          <div style={{background:"#fffbeb",padding:14,borderRadius:8}}>
            <strong style={{color:"#92400e",fontSize:"0.85rem",display:"block",marginBottom:6}}>Identified Gaps</strong>
            {ev.gaps.map((g,i)=><div key={i} style={{fontSize:"0.82rem",color:"#b45309",marginBottom:4}}>• {g}</div>)}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── SkillAssessment Component ───────────────────────────────────────────────
function SkillAssessment({ applicationId, skillData, onComplete }) {
  const [questions, setQuestions] = useState(skillData?.questions || []);
  const [answers, setAnswers]     = useState([]);
  const [busy, setBusy]           = useState(false);
  const [err, setErr]             = useState("");

  async function start() {
    setBusy(true); setErr("");
    try {
      const res = await api.startSkills(applicationId);
      setQuestions(res.questions);
      setAnswers(Array(res.questions.length).fill(""));
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  }

  async function submit() {
    if (answers.some(a => a === "" || a === undefined)) {
      return setErr("Please answer all questions before submitting.");
    }
    setBusy(true); setErr("");
    try {
      const res = await api.submitSkills(applicationId, answers);
      onComplete(res);
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  }

  if (!questions.length) {
    return (
      <div className="card interviewIntro">
        <div className="iconBox"><Compass/></div>
        <div>
          <div className="eyebrow">STEP 05 · ROLE-SPECIFIC SKILL ASSESSMENT</div>
          <h2>Technical Domain Skill Assessment</h2>
          <p>Evaluate your specialized knowledge with targeted questions specific to this job's tech stack and engineering standards.</p>
          {err && <ErrBanner message={err}/>}
          <button className="btn" onClick={start} disabled={busy} style={{background:"var(--accent-gradient)"}}>
            {busy ? "Preparing Questions…" : "Start Skill Assessment"} <Compass size={16}/>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{padding:"28px 32px"}}>
      <div className="eyebrow">STEP 05 · ROLE-SPECIFIC SKILL ASSESSMENT</div>
      <h2 style={{marginTop:4,display:"flex",alignItems:"center",gap:8}}>
        <Compass color="var(--accent)"/> Technical Competency Assessment
      </h2>
      <p style={{color:"#666",fontSize:"0.88rem",marginBottom:20}}>Select the best response for each scenario or technical question.</p>

      {questions.map((q, qIdx) => (
        <div key={q.id || qIdx} style={{borderBottom:"1px solid #f1f5f9",paddingBottom:20,marginBottom:20}}>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:8}}>
            <span style={{background:"#ecfdf5",color:"#059669",fontWeight:700,fontSize:"0.8rem",padding:"2px 8px",borderRadius:4}}>
              Q{qIdx + 1}
            </span>
            {q.skill && <Badge label={q.skill} color="#059669" bg="#d1fae5"/>}
          </div>
          <h3 style={{fontSize:"1rem",color:"#1e293b",margin:"8px 0 14px",lineHeight:1.5}}>{q.question}</h3>
          
          <div style={{display:"grid",gap:8}}>
            {q.options?.map((opt, optIdx) => (
              <label
                key={optIdx}
                style={{
                  display:"flex",alignItems:"center",gap:12,padding:"10px 14px",
                  borderRadius:8,border:"1px solid",
                  borderColor: answers[qIdx] === String(optIdx) ? "var(--accent)" : "#e2e8f0",
                  background: answers[qIdx] === String(optIdx) ? "#ecfdf5" : "#fff",
                  cursor:"pointer",transition:"all 0.2s"
                }}
              >
                <input
                  type="radio"
                  name={`q_${qIdx}`}
                  checked={answers[qIdx] === String(optIdx)}
                  onChange={()=>{
                    const copy = [...answers];
                    copy[qIdx] = String(optIdx);
                    setAnswers(copy);
                  }}
                />
                <span style={{fontSize:"0.9rem",color:"#334155"}}>{opt}</span>
              </label>
            ))}
          </div>
        </div>
      ))}

      {err && <ErrBanner message={err}/>}

      <button className="btn full" onClick={submit} disabled={busy} style={{background:"var(--accent-gradient)"}}>
        {busy ? "Evaluating Answers…" : "Submit Technical Assessment"} <CheckCircle2 size={16}/>
      </button>
    </div>
  );
}

function SkillResults({ sa }) {
  const ev = sa.evaluations || {};
  return (
    <div className="card" style={{padding:"28px 32px",marginBottom:20}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16}}>
        <div>
          <div className="eyebrow">SKILL ASSESSMENT COMPLETED</div>
          <h2 style={{margin:"4px 0",display:"flex",alignItems:"center",gap:8}}>
            <Compass color="var(--accent)"/> Technical Domain Proficiency
          </h2>
          <p style={{color:"#64748b",fontSize:"0.88rem",marginTop:2}}>Role-specific competency validation report</p>
        </div>
        <div style={{background:"#ecfdf5",border:"2px solid var(--accent)",borderRadius:12,padding:"10px 20px",textAlign:"center"}}>
          <div style={{fontSize:"2rem",fontWeight:900,color:"var(--accent)"}}>{Math.round(sa.score)}</div>
          <div style={{fontSize:"0.78rem",fontWeight:700,color:"#047857"}}>{ev.proficiency_level || "Proficient"}</div>
        </div>
      </div>

      <div style={{marginTop:20}}>
        <h4 style={{color:"#1e293b",marginBottom:12}}>Question Breakdown & Explanations</h4>
        <div style={{display:"grid",gap:12}}>
          {ev.breakdown?.map((item, i) => (
            <div key={i} style={{border:"1px solid #e2e8f0",borderRadius:8,padding:14,background:item.is_correct?"#f8fafc":"#fff5f5"}}>
              <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                {item.is_correct ? <CheckCircle2 size={16} color="#22c55e"/> : <XCircle size={16} color="#ef4444"/>}
                <strong style={{fontSize:"0.9rem",color:"#0f172a"}}>{item.question}</strong>
              </div>
              <div style={{fontSize:"0.84rem",color:"#475569",lineHeight:1.6}}>
                <strong>Explanation:</strong> {item.explanation}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── SituationalTest Component ───────────────────────────────────────────────
function SituationalTest({ applicationId, situationalData, onComplete }) {
  const [scenarios, setScenarios] = useState(situationalData?.scenarios || []);
  const [responses, setResponses] = useState([]);
  const [busy, setBusy]           = useState(false);
  const [err, setErr]             = useState("");

  async function start() {
    setBusy(true); setErr("");
    try {
      const res = await api.startSituational(applicationId);
      setScenarios(res.scenarios);
      setResponses(Array(res.scenarios.length).fill(""));
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  }

  async function submit() {
    if (responses.some(r => !r || r.trim().length < 20)) {
      return setErr("Please provide a thoughtful response (at least 20 characters) for each scenario.");
    }
    setBusy(true); setErr("");
    try {
      const res = await api.submitSituational(applicationId, responses);
      onComplete(res);
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  }

  if (!scenarios.length) {
    return (
      <div className="card interviewIntro">
        <div className="iconBox"><MessageSquareCode/></div>
        <div>
          <div className="eyebrow">STEP 06 · COMMUNICATION & SITUATIONAL JUDGMENT</div>
          <h2>Workplace Situational Judgment (SJT)</h2>
          <p>Real-world dilemmas: incident handling under pressure, stakeholder trade-offs, and constructive team collaboration.</p>
          {err && <ErrBanner message={err}/>}
          <button className="btn" onClick={start} disabled={busy} style={{background:"linear-gradient(135deg,#f59e0b,#d97706)"}}>
            {busy ? "Loading Scenarios…" : "Start Situational Judgment"} <MessageSquareCode size={16}/>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{padding:"28px 32px"}}>
      <div className="eyebrow">STEP 06 · COMMUNICATION & SITUATIONAL JUDGMENT</div>
      <h2 style={{marginTop:4,display:"flex",alignItems:"center",gap:8}}>
        <MessageSquareCode color="#f59e0b"/> Situational Dilemmas & Communication
      </h2>
      <p style={{color:"#666",fontSize:"0.88rem",marginBottom:20}}>Explain your decision-making, stakeholder communication, and actionable steps for each scenario.</p>

      {scenarios.map((sc, i) => (
        <div key={sc.id || i} style={{borderBottom:"1px solid #f1f5f9",paddingBottom:22,marginBottom:22}}>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
            <span style={{background:"#fef3c7",color:"#b45309",fontWeight:700,fontSize:"0.8rem",padding:"2px 8px",borderRadius:4}}>
              Scenario {i + 1}
            </span>
            <strong style={{color:"#1e293b"}}>{sc.title}</strong>
          </div>
          <div style={{display:"flex",gap:4,marginBottom:10}}>
            {sc.competencies?.map((c,ci)=><Badge key={ci} label={c} color="#d97706" bg="#fef3c7"/>)}
          </div>
          <p style={{lineHeight:1.7,color:"#334155",fontSize:"0.92rem",background:"#f8fafc",padding:14,borderRadius:8}}>
            {sc.scenario}
          </p>

          <label className="field" style={{marginTop:12}}>
            <span>Your Response & Action Plan:</span>
            <textarea
              rows={4}
              placeholder="Outline your immediate communication, rationale, and preventive/corrective actions..."
              value={responses[i] || ""}
              onChange={e=>{
                const copy = [...responses];
                copy[i] = e.target.value;
                setResponses(copy);
              }}
            />
          </label>
        </div>
      ))}

      {err && <ErrBanner message={err}/>}

      <button className="btn full" onClick={submit} disabled={busy} style={{background:"linear-gradient(135deg,#f59e0b,#b45309)"}}>
        {busy ? "Evaluating Situational Judgment…" : "Submit Situational Responses"} <Send size={16}/>
      </button>
    </div>
  );
}

function SituationalResults({ sj }) {
  const ev = sj.evaluations || {};
  const dims = ev.dimension_scores || {};
  return (
    <div className="card" style={{padding:"28px 32px",marginBottom:20}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16}}>
        <div>
          <div className="eyebrow">SITUATIONAL JUDGMENT EVALUATED</div>
          <h2 style={{margin:"4px 0",display:"flex",alignItems:"center",gap:8}}>
            <MessageSquareCode color="#f59e0b"/> Workplace Judgment & Communication
          </h2>
          <p style={{color:"#64748b",fontSize:"0.88rem",marginTop:2}}>AI behavioral & communication audit</p>
        </div>
        <div style={{background:"#fffbeb",border:"2px solid #f59e0b",borderRadius:12,padding:"10px 20px",textAlign:"center"}}>
          <div style={{fontSize:"2rem",fontWeight:900,color:"#f59e0b"}}>{Math.round(sj.score)}</div>
          <div style={{fontSize:"0.78rem",fontWeight:700,color:"#b45309"}}>SJT SCORE</div>
        </div>
      </div>

      {ev.summary && (
        <div style={{background:"#f8fafc",borderRadius:10,padding:16,marginTop:16}}>
          <p style={{margin:0,lineHeight:1.7,color:"#334155",fontSize:"0.92rem"}}>{ev.summary}</p>
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:12,marginTop:18}}>
        <div style={{background:"#fefce8",padding:12,borderRadius:8,textAlign:"center"}}>
          <div style={{fontSize:"1.4rem",fontWeight:800,color:"#ca8a04"}}>{dims.communication_clarity ?? "—"}/10</div>
          <div style={{fontSize:"0.78rem",color:"#854d0e"}}>Communication Clarity</div>
        </div>
        <div style={{background:"#fefce8",padding:12,borderRadius:8,textAlign:"center"}}>
          <div style={{fontSize:"1.4rem",fontWeight:800,color:"#ca8a04"}}>{dims.leadership_ownership ?? "—"}/10</div>
          <div style={{fontSize:"0.78rem",color:"#854d0e"}}>Leadership & Ownership</div>
        </div>
        <div style={{background:"#fefce8",padding:12,borderRadius:8,textAlign:"center"}}>
          <div style={{fontSize:"1.4rem",fontWeight:800,color:"#ca8a04"}}>{dims.conflict_resolution ?? "—"}/10</div>
          <div style={{fontSize:"0.78rem",color:"#854d0e"}}>Conflict Resolution</div>
        </div>
        <div style={{background:"#fefce8",padding:12,borderRadius:8,textAlign:"center"}}>
          <div style={{fontSize:"1.4rem",fontWeight:800,color:"#ca8a04"}}>{dims.judgment_ethics ?? "—"}/10</div>
          <div style={{fontSize:"0.78rem",color:"#854d0e"}}>Judgment & Ethics</div>
        </div>
      </div>

      {ev.evaluations?.length > 0 && (
        <div style={{marginTop:20}}>
          <h4 style={{color:"#1e293b",marginBottom:10}}>Scenario Evaluations</h4>
          <div style={{display:"grid",gap:10}}>
            {ev.evaluations.map((item, i) => (
              <div key={i} style={{border:"1px solid #e2e8f0",borderRadius:8,padding:12,background:"#fff"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <strong style={{fontSize:"0.88rem",color:"#0f172a"}}>{item.title || `Scenario ${i+1}`}</strong>
                  <Badge label={`${item.score}/10`} color="#d97706" bg="#fef3c7"/>
                </div>
                <p style={{margin:"6px 0 0",fontSize:"0.84rem",color:"#475569"}}>{item.feedback}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── ExplainableScore Component ───────────────────────────────────────────────
function ExplainableScore({ applicationId }) {
  const { data: explain, loading, error, refetch } = useFetch(() => api.explain(applicationId), [applicationId]);
  if (loading) return <div style={{padding:"20px 0"}}><Loader/></div>;
  if (error)   return <ErrBanner message={error} onRetry={refetch}/>;
  if (!explain) return null;
  const recColor = explain.recommendation_color || "#f59e0b";
  return (
    <div className="card" style={{padding:"28px 32px",marginTop:24}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16,marginBottom:24}}>
        <div><div className="eyebrow">EXPLAINABLE AI SCORING</div><h2 style={{margin:"4px 0"}}>Comprehensive Candidate Intelligence Report</h2></div>
        <div style={{background:recColor+"15",border:`2px solid ${recColor}`,borderRadius:12,padding:"12px 20px",textAlign:"center",minWidth:160}}>
          <div style={{fontSize:"2.2rem",fontWeight:900,color:recColor}}>{Math.round(explain.final_score)}</div>
          <div style={{fontSize:"0.8rem",color:recColor,fontWeight:700}}>{explain.recommendation_label}</div>
        </div>
      </div>

      <h3 style={{color:"#1a1a2e",marginBottom:14,display:"flex",alignItems:"center",gap:8}}><BarChart3 size={18}/> Multi-Pillar Score Breakdown</h3>
      {explain.breakdown?.map(b=>(
        <ScoreBar key={b.label} label={b.label} value={b.score} weight={b.weight} color={b.color}/>
      ))}

      <h3 style={{color:"#1a1a2e",margin:"24px 0 14px",display:"flex",alignItems:"center",gap:8}}><Target size={18}/> Performance Dimensions</h3>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(140px,1fr))",gap:12,marginBottom:24}}>
        {explain.radar?.map(r=>(
          <div key={r.dimension} style={{background:"#f8f8ff",borderRadius:10,padding:"14px",textAlign:"center"}}>
            <div style={{fontSize:"1.6rem",fontWeight:800,color:"#667eea"}}>{Math.round(r.score)}</div>
            <div style={{fontSize:"0.75rem",color:"#888",marginTop:4}}>{r.dimension}</div>
          </div>
        ))}
      </div>

      {explain.assessment && <>
        <h3 style={{color:"#1a1a2e",display:"flex",alignItems:"center",gap:8}}><Brain size={18}/> Executive AI Assessment</h3>
        <p style={{lineHeight:1.8,color:"#444",background:"#f8f8ff",padding:"16px",borderRadius:10}}>{explain.assessment}</p>
      </>}

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20,marginTop:20}}>
        <div>
          <h4 style={{color:"#22c55e",marginBottom:10,display:"flex",alignItems:"center",gap:6}}><CheckCircle2 size={16}/> Strengths</h4>
          {explain.strengths?.map((s,i)=><div key={i} style={{padding:"6px 0",fontSize:"0.86rem",borderBottom:"1px solid #f0f9f0"}}>✓ {s}</div>)}
        </div>
        <div>
          <h4 style={{color:"#f59e0b",marginBottom:10,display:"flex",alignItems:"center",gap:6}}><AlertCircle size={16}/> Risk Considerations</h4>
          {explain.risks?.map((r,i)=><div key={i} style={{padding:"6px 0",fontSize:"0.86rem",borderBottom:"1px solid #fffbf0"}}>⚠ {r}</div>)}
        </div>
      </div>
    </div>
  );
}

// ─── TestScheduler (Recruiter) ────────────────────────────────────────────────
function TestScheduler({ applicationId, schedules = [], onScheduled }) {
  const [form, setForm] = useState({ test_type: "interview", scheduled_at: "", notes: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr]   = useState("");
  async function save(e) {
    e.preventDefault(); if(!form.scheduled_at) return setErr("Set a date/time.");
    setBusy(true); setErr("");
    try { await api.scheduleTest(applicationId, form); onScheduled(); setForm({test_type:"interview",scheduled_at:"",notes:""}); }
    catch(e) { setErr(e.message); } finally { setBusy(false); }
  }
  async function remove(sid) {
    try { await api.deleteSchedule(sid); onScheduled(); } catch(e) { setErr(e.message); }
  }
  return (
    <div className="card" style={{padding:"24px 28px",marginTop:16}}>
      <div className="eyebrow">TEST SCHEDULING</div>
      <h3 style={{marginTop:4,display:"flex",alignItems:"center",gap:8}}><Calendar size={18}/> Schedule Candidate Tests</h3>
      <form onSubmit={save} style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:16}}>
        <label className="field"><span>Test type</span>
          <select value={form.test_type} onChange={e=>setForm({...form,test_type:e.target.value})}>
            <option value="interview">AI Interview</option>
            <option value="coding">Python Coding Test</option>
            <option value="project">Project Verification</option>
            <option value="skills">Role Skill Assessment</option>
            <option value="situational">Situational Judgment</option>
            <option value="final">Final Round</option>
          </select>
        </label>
        <label className="field"><span>Date & Time</span>
          <input type="datetime-local" value={form.scheduled_at} onChange={e=>setForm({...form,scheduled_at:e.target.value})}/>
        </label>
        <label className="field" style={{gridColumn:"1/-1"}}><span>Notes (optional)</span>
          <input placeholder="Instructions, Zoom link, guidelines..." value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/>
        </label>
        {err && <div style={{gridColumn:"1/-1"}}><ErrBanner message={err}/></div>}
        <button className="btn small" type="submit" disabled={busy} style={{gridColumn:"1/-1",width:"fit-content"}}>
          {busy?"Saving…":"Add Schedule"} <Calendar size={14}/>
        </button>
      </form>
      {schedules.length > 0 && <>
        <h4 style={{color:"var(--accent)",marginTop:20,fontSize:"0.95rem"}}>Upcoming Test Schedules</h4>
        {schedules.map(s=>(
          <div key={s.id} style={{display:"flex",alignItems:"center",gap:12,padding:"10px 0",borderBottom:"1px solid #e2e8f0"}}>
            <Clock size={16} color="var(--accent)"/>
            <div style={{flex:1}}>
              <b style={{textTransform:"capitalize",color:"var(--ink)",fontSize:"0.88rem"}}>{s.test_type} Test</b>
              <div style={{fontSize:"0.82rem",color:"var(--ink-muted)"}}>{new Date(s.scheduled_at).toLocaleString()}{s.notes?" · "+s.notes:""}</div>
            </div>
            <button onClick={()=>remove(s.id)} style={{background:"#fef2f2",color:"#ef4444",border:"1px solid #fecaca",borderRadius:8,padding:"4px 12px",cursor:"pointer",fontSize:"0.76rem",fontWeight:700}}>Cancel</button>
          </div>
        ))}
      </>}
    </div>
  );
}

// ─── Application (full journey) ───────────────────────────────────────────────
function Application() {
  const { id } = useParams();
  const u = JSON.parse(localStorage.getItem("user") || "null");
  const { data: a, loading, error, refetch } = useFetch(() => api.application(id), [id]);
  const [questions, setQuestions] = useState([]);
  const [answers,   setAnswers]   = useState([]);
  const [busy,      setBusy]      = useState(false);
  const [intErr,    setIntErr]    = useState("");

  async function startInterview() {
    setBusy(true); setIntErr("");
    try { const d = await api.startInterview(id); setQuestions(d.questions); setAnswers(Array(d.questions.length).fill("")); }
    catch(e) { setIntErr(e.message); } finally { setBusy(false); }
  }
  async function submitInterview() {
    if(answers.some(x=>!x.trim())) return setIntErr("Please answer every question.");
    setBusy(true); setIntErr("");
    try { await api.submitInterview(id, answers); refetch(); setQuestions([]); }
    catch(e) { setIntErr(e.message); } finally { setBusy(false); }
  }

  if(loading) return <Shell><Loader/></Shell>;
  if(error)   return <Shell><ErrBanner message={error} onRetry={refetch}/></Shell>;
  if(!a)      return <Shell><Empty text="Application not found."/></Shell>;

  const isCandidate = u?.role === "candidate";
  const hasInterview = a.interview?.completed;
  const hasCoding    = a.coding_test?.completed;
  const hasProjects  = a.project_verification?.completed;
  const hasSkills    = a.skill_assessment?.completed;
  const hasSituational = a.situational_test?.completed;

  return (
    <Shell>
      <PageTitle eyebrow="APPLICATION JOURNEY" title={a.job_title} sub="Resume · AI Interview · Coding · Projects · Role Skills · Situational Judgment"/>
      <div className="stage">
        <div className="stageRail">
          <Step n="01" t="Resume"      active/>
          <Step n="02" t="Interview"   active={hasInterview}/>
          <Step n="03" t="Coding"      active={hasCoding}/>
          <Step n="04" t="Projects"    active={hasProjects}/>
          <Step n="05" t="Role Skills" active={hasSkills}/>
          <Step n="06" t="SJT"         active={hasSituational}/>
          <Step n="07" t="Results"     active={hasInterview && hasCoding && hasProjects}/>
        </div>
        <div>
          {/* ── STEP 02: AI INTERVIEW ── */}
          {!hasInterview && !questions.length && (
            <div className="card interviewIntro">
              <div className="iconBox"><Sparkles/></div>
              <div>
                <div className="eyebrow">STEP 02 · AI INTERVIEW</div>
                <h2>Ready for your AI interview?</h2>
                <p>10 tailored questions based on your resume and the role requirements. Your webcam session will be recorded.</p>
                {intErr && <ErrBanner message={intErr}/>}
                {isCandidate && <button className="btn" onClick={startInterview} disabled={busy}>{busy?"Preparing…":"Start AI interview"} <ChevronRight/></button>}
              </div>
            </div>
          )}
          {questions.length > 0 && (
            <div className="card interviewForm">
              <div className="interviewHead"><div><div className="eyebrow">LIVE AI INTERVIEW</div><h2>Question set</h2></div><span>{questions.length} questions</span></div>
              <VideoRecorder applicationId={id}/>
              {questions.map((q,i)=>(
                <div className="q" key={i}>
                  <label>Q{i+1}</label><h3>{q}</h3>
                  <textarea value={answers[i]} onChange={e=>{const x=[...answers];x[i]=e.target.value;setAnswers(x);}} placeholder="Write your answer with reasoning, examples and outcomes…"/>
                </div>
              ))}
              {intErr && <ErrBanner message={intErr}/>}
              <button className="btn full" onClick={submitInterview} disabled={busy}>{busy?"Evaluating…":"Submit interview"} <Sparkles/></button>
            </div>
          )}
          {hasInterview && !questions.length && a.interview && (
            <div className="card" style={{padding:"20px 28px",marginBottom:16}}>
              <div className="eyebrow">INTERVIEW COMPLETE</div>
              <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginTop:8}}>
                <h3 style={{margin:0}}>AI Interview Score</h3>
                <div style={{fontSize:"2rem",fontWeight:800,color:"#667eea"}}>{Math.round(a.interview.score)}<span style={{fontSize:"1rem",color:"#aaa"}}>/100</span></div>
              </div>
            </div>
          )}

          {/* ── STEP 03: CODING TEST ── */}
          {hasInterview && !hasCoding && isCandidate && (
            <CodingTest applicationId={id} codingTest={a.coding_test} onComplete={()=>refetch()}/>
          )}
          {hasCoding && a.coding_test && (
            <div className="card" style={{padding:"20px 28px",marginBottom:16}}>
              <div className="eyebrow">CODING TEST COMPLETE</div>
              <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginTop:8}}>
                <h3 style={{margin:0}}>Python Coding Score</h3>
                <div style={{fontSize:"2rem",fontWeight:800,color:"#10b981"}}>{Math.round(a.coding_test.score)}<span style={{fontSize:"1rem",color:"#aaa"}}>/100</span></div>
              </div>
            </div>
          )}

          {/* ── STEP 04: PROJECT & PORTFOLIO VERIFICATION ── */}
          {hasCoding && !hasProjects && isCandidate && (
            <ProjectVerification applicationId={id} projectData={a.project_verification} onComplete={()=>refetch()}/>
          )}
          {hasProjects && a.project_verification && (
            <ProjectResults pv={a.project_verification}/>
          )}

          {/* ── STEP 05: ROLE-SPECIFIC SKILL ASSESSMENT ── */}
          {hasProjects && !hasSkills && isCandidate && (
            <SkillAssessment applicationId={id} skillData={a.skill_assessment} onComplete={()=>refetch()}/>
          )}
          {hasSkills && a.skill_assessment && (
            <SkillResults sa={a.skill_assessment}/>
          )}

          {/* ── STEP 06: SITUATIONAL JUDGMENT TEST ── */}
          {hasSkills && !hasSituational && isCandidate && (
            <SituationalTest applicationId={id} situationalData={a.situational_test} onComplete={()=>refetch()}/>
          )}
          {hasSituational && a.situational_test && (
            <SituationalResults sj={a.situational_test}/>
          )}

          {/* ── EXPLAINABLE AI REPORT ── */}
          {(hasInterview || hasCoding || hasProjects || hasSkills || hasSituational) && (
            <ExplainableScore applicationId={id}/>
          )}

          {/* Test Scheduling for Recruiters */}
          {!isCandidate && (
            <TestScheduler applicationId={id} schedules={a.schedules||[]} onScheduled={refetch}/>
          )}
        </div>
      </div>
    </Shell>
  );
}

// ─── Recruiter ────────────────────────────────────────────────────────────────
function Recruiter() {
  const { data: jobs, loading, error, refetch } = useFetch(() => api.myJobs());
  const js = jobs || []; const total = js.reduce((x,j)=>x+j.applications,0);
  return (
    <Shell>
      <PageTitle eyebrow="RECRUITER WORKSPACE" title="Talent, organized." sub="Manage vacancies, view ranked candidates across all 6 evidence pillars."/>
      {loading&&<Loader/>} {error&&<ErrBanner message={error} onRetry={refetch}/>}
      {!loading&&!error&&<>
        <div className="stats">
          <Stat t="Open roles" v={js.length}/> <Stat t="Applications" v={total}/>
          <Stat t="Avg. applicants/role" v={js.length?Math.round(total/js.length):0}/> <Stat t="AI verification" v="Active"/>
        </div>
        <div className="sectionHead"><div><h2>Your roles</h2></div><Link to="/recruiter/jobs/new" className="btn small"><Plus size={17}/> New vacancy</Link></div>
        <div className="cards">
          {js.map(j=>(
            <div className="card roleCard" key={j.id}>
              <div><span className="status">OPEN</span><h3>{j.title}</h3><p>{j.location} · {j.employment_type}</p></div>
              <div className="roleRight">
                <strong>{j.applications}</strong><span>applicants</span>
                <div style={{display:"flex",gap:8,marginTop:4}}>
                  <Link className="textBtn" to={"/recruiter/jobs/"+j.id}>Leaderboard →</Link>
                  <Link className="textBtn" to={"/recruiter/jobs/"+j.id+"/analysis"}>Analysis →</Link>
                  <Link className="textBtn" to={"/recruiter/jobs/"+j.id+"/pipeline"}>Pipeline →</Link>
                </div>
              </div>
            </div>
          ))}
        </div>
        {!js.length && <Empty text="Create your first vacancy to start receiving candidates."/>}
      </>}
    </Shell>
  );
}

// ─── NewJob ───────────────────────────────────────────────────────────────────
function NewJob() {
  const [f,setF]=useState({title:"",description:"",skills:"",experience:0,location:"Remote",employment_type:"Full-time",salary:"",openings:1,deadline:""});
  const [busy,setBusy]=useState(false); const [err,setErr]=useState(""); const nav=useNavigate();
  async function save(e) {
    e.preventDefault(); setBusy(true); setErr("");
    try {
      await api.createJob({...f,skills:f.skills.split(",").map(x=>x.trim()).filter(Boolean),experience:Number(f.experience),openings:Number(f.openings)});
      nav("/recruiter");
    } catch(e){setErr(e.message);} finally{setBusy(false);}
  }
  return (
    <Shell>
      <PageTitle eyebrow="VACANCY BUILDER" title="Create a role." sub="All registered candidates will be notified by email."/>
      <form className="card jobForm" onSubmit={save}>
        <div className="formGrid">
          <Field label="Job title"><input required value={f.title} onChange={e=>setF({...f,title:e.target.value})} placeholder="e.g. Machine Learning Engineer"/></Field>
          <Field label="Location"><input value={f.location} onChange={e=>setF({...f,location:e.target.value})}/></Field>
          <Field label="Employment type"><select value={f.employment_type} onChange={e=>setF({...f,employment_type:e.target.value})}><option>Full-time</option><option>Part-time</option><option>Internship</option><option>Contract</option></select></Field>
          <Field label="Experience required"><input type="number" min="0" value={f.experience} onChange={e=>setF({...f,experience:e.target.value})}/></Field>
          <Field label="Salary"><input value={f.salary} onChange={e=>setF({...f,salary:e.target.value})} placeholder="e.g. 6-10 LPA"/></Field>
          <Field label="Openings"><input type="number" min="1" value={f.openings} onChange={e=>setF({...f,openings:e.target.value})}/></Field>
        </div>
        <Field label="Required skills"><input required value={f.skills} onChange={e=>setF({...f,skills:e.target.value})} placeholder="python, sql, machine learning"/><small>Comma-separated.</small></Field>
        <Field label="Role description"><textarea required value={f.description} onChange={e=>setF({...f,description:e.target.value})} placeholder="Responsibilities, technical expectations…"/></Field>
        {err&&<ErrBanner message={err}/>}
        <button className="btn" disabled={busy}>{busy?"Publishing…":"Publish vacancy"} <ChevronRight/></button>
      </form>
    </Shell>
  );
}
function Field({ label, children }) { return <label className="field"><span>{label}</span>{children}</label>; }

// ─── Candidates leaderboard ───────────────────────────────────────────────────
function Candidates() {
  const { id } = useParams();
  const { data, loading, error, refetch } = useFetch(() => api.candidates(id), [id]);
  const [list, setList] = useState([]);
  useEffect(()=>{ if(data) setList(data); },[data]);
  return (
    <Shell>
      <PageTitle eyebrow="AI SHORTLIST" title="Candidate ranking." sub="Resume · Interview · Coding · Projects · Skills · SJT"/>
      {loading&&<Loader/>} {error&&<ErrBanner message={error} onRetry={refetch}/>}
      {!loading&&!error&&<div className="leader card">
        <div className="leaderHead"><h2>Ranked candidates</h2><span>{list.length} applicants</span></div>
        {list.map((x,i)=>(
          <div className="candidateRow" key={x.id}>
            <div className="rank">{i+1}</div>
            <div className="avatar">{x.name[0]}</div>
            <div className="candMain">
              <b>{x.name}</b><small>{x.email}</small>
              <div style={{display:"flex",gap:5,marginTop:6,flexWrap:"wrap"}}>
                <Badge label={`Resume: ${Math.round(x.resume_score)}`} color="#10b981" bg="#ecfdf5"/>
                {x.interview_score!=null&&<Badge label={`Interview: ${Math.round(x.interview_score)}`} color="#059669" bg="#d1fae5"/>}
                {x.coding_score!=null&&<Badge label={`Code: ${Math.round(x.coding_score)}`} color="#14b8a6" bg="#f0fdfa"/>}
                {x.project_score!=null&&<Badge label={`Projects: ${Math.round(x.project_score)}`} color="#047857" bg="#ecfdf5"/>}
                {x.skills_score!=null&&<Badge label={`Skills: ${Math.round(x.skills_score)}`} color="#0d9488" bg="#ccfbf1"/>}
                {x.situational_score!=null&&<Badge label={`SJT: ${Math.round(x.situational_score)}`} color="#f59e0b" bg="#fffbeb"/>}
              </div>
            </div>
            <div className="candScore"><strong>{Math.round(x.final_score)}</strong><small>FIT</small></div>
            <div style={{display:"flex",flexDirection:"column",gap:6}}>
              <select value={x.status} onChange={async e=>{await api.status(x.id,e.target.value).catch(()=>{});setList(list.map(z=>z.id===x.id?{...z,status:e.target.value}:z));}}>
                <option value="applied">Applied</option><option value="in_review">In review</option>
                <option value="shortlisted">Shortlisted</option><option value="rejected">Rejected</option>
              </select>
              <Link to={`/application/${x.id}`} style={{fontSize:"0.76rem",fontWeight:700,color:"#10b981",textDecoration:"none",textAlign:"center",padding:"2px 6px",borderRadius:6,background:"#ecfdf5"}}>Report →</Link>
              <Link to={`/application/${x.id}/360`} style={{fontSize:"0.76rem",fontWeight:700,color:"#059669",textDecoration:"none",textAlign:"center",padding:"2px 6px",borderRadius:6,background:"#d1fae5"}}>360° Profile →</Link>
            </div>
          </div>
        ))}
        {!list.length&&<p style={{padding:"20px",color:"#888",textAlign:"center"}}>No candidates yet.</p>}
      </div>}
    </Shell>
  );
}

// ─── Recruitment Analysis (Recruiter) ────────────────────────────────────────
function JobAnalysis() {
  const { id } = useParams();
  const { data, loading, error, refetch } = useFetch(() => api.jobAnalysis(id), [id]);

  if(loading) return <Shell><Loader/></Shell>;
  if(error)   return <Shell><ErrBanner message={error} onRetry={refetch}/></Shell>;
  if(!data)   return <Shell><Empty text="No data."/></Shell>;

  return (
    <Shell>
      <PageTitle eyebrow="RECRUITMENT ANALYSIS" title="Hiring funnel & competency insights." sub="AI-powered analysis of candidate pipeline across all assessment pillars."/>
      <div className="stats">
        <Stat t="Total applicants"    v={data.total}/>
        <Stat t="Interviews done"     v={data.interviews_completed}/>
        <Stat t="Projects verified"   v={data.projects_verified || 0}/>
        <Stat t="Skills assessed"     v={data.skills_assessed || 0}/>
      </div>

      <div className="card" style={{padding:"24px 28px",marginTop:16}}>
        <h3 style={{marginTop:0,display:"flex",alignItems:"center",gap:8}}><Zap size={18}/> Recruitment Funnel</h3>
        {data.funnel?.map(stage=>(
          <div key={stage.stage} style={{marginBottom:14}}>
            <div style={{display:"flex",justifyContent:"space-between",fontSize:"0.85rem",marginBottom:5}}>
              <span style={{fontWeight:600,color:"var(--ink)"}}>{stage.stage}</span>
              <span style={{color:"var(--accent)",fontWeight:700}}>{stage.count} candidates</span>
            </div>
            <div style={{height:10,background:"#f1f5f9",borderRadius:99,overflow:"hidden",border:"1px solid #e2e8f0"}}>
              <div style={{height:"100%",width:`${data.total?Math.min(100,(stage.count/data.total)*100):0}%`,background:"var(--accent-gradient)",borderRadius:99,transition:"width 0.6s"}}/>
            </div>
          </div>
        ))}
      </div>

      <div className="card" style={{padding:"26px 28px",marginTop:18}}>
        <h3 style={{marginTop:0,display:"flex",alignItems:"center",gap:8,fontSize:"1.1rem"}}><Trophy size={18} color="var(--accent)"/> Average Competency Scores</h3>
        <ScoreBar label="Resume Score"             value={data.avg_scores?.resume||0}      color="#10b981"/>
        <ScoreBar label="Interview Score"          value={data.avg_scores?.interview||0}   color="#059669"/>
        <ScoreBar label="Coding Score"             value={data.avg_scores?.coding||0}      color="#14b8a6"/>
        <ScoreBar label="Project Verification"     value={data.avg_scores?.projects||0}    color="#047857"/>
        <ScoreBar label="Role Skills Assessment"   value={data.avg_scores?.role_skills||0} color="#0d9488"/>
        <ScoreBar label="Situational Judgment"     value={data.avg_scores?.situational||0} color="#f59e0b"/>
      </div>

      {data.skill_coverage?.length>0 && (
        <div className="card" style={{padding:"26px 28px",marginTop:18}}>
          <h3 style={{marginTop:0,display:"flex",alignItems:"center",gap:8,fontSize:"1.1rem"}}><Target size={18} color="var(--accent)"/> Skill Coverage</h3>
          {data.skill_coverage.map(s=>(
            <div key={s.skill} style={{marginBottom:14}}>
              <div style={{display:"flex",justifyContent:"space-between",fontSize:"0.84rem",marginBottom:4}}>
                <span style={{fontWeight:600,textTransform:"capitalize",color:"var(--ink)"}}>{s.skill}</span>
                <span style={{color:"var(--accent)",fontWeight:700}}>{s.candidates_with_skill}/{data.total} candidates ({s.coverage_pct}%)</span>
              </div>
              <div style={{height:8,background:"#f1f5f9",borderRadius:99,overflow:"hidden",border:"1px solid #e2e8f0"}}>
                <div style={{height:"100%",width:`${s.coverage_pct}%`,background:"var(--accent)",borderRadius:99}}/>
              </div>
            </div>
          ))}
        </div>
      )}

      {data.top_candidates?.length>0 && (
        <div className="card" style={{padding:"26px 28px",marginTop:18}}>
          <h3 style={{marginTop:0,display:"flex",alignItems:"center",gap:8,fontSize:"1.1rem"}}><Trophy size={18} color="#f59e0b"/> Top Candidates</h3>
          {data.top_candidates.map((c,i)=>(
            <div key={i} style={{display:"flex",alignItems:"center",gap:14,padding:"12px 0",borderBottom:"1px solid #e2e8f0"}}>
              <div style={{width:30,height:30,borderRadius:"50%",background:"var(--accent-gradient)",color:"#fff",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:800,fontSize:"0.82rem",boxShadow:"0 2px 8px rgba(16,185,129,0.3)"}}>{i+1}</div>
              <span style={{flex:1,fontWeight:700,color:"var(--ink)"}}>{c.name}</span>
              <Badge label={`${Math.round(c.score)} fit`} color="#10b981" bg="#ecfdf5"/>
            </div>
          ))}
        </div>
      )}
    </Shell>
  );
}

// ─── Shared ───────────────────────────────────────────────────────────────────
function Empty({ text }) { return <div className="empty card"><FileText size={28}/><p>{text}</p></div>; }

// ─── Candidate Support Chatbot Widget ─────────────────────────────────────────
function ChatbotWidget({ user }) {
  const [open, setOpen]     = useState(false);
  const [msgs, setMsgs]     = useState([
    { role: "assistant", content: "👋 Hi! I'm HireMind Assistant. Ask me anything about your application, assessments, or how to improve your score!" }
  ]);
  const [input, setInput]   = useState("");
  const [busy, setBusy]     = useState(false);
  const [sessionId]         = useState(() => localStorage.getItem("chat_session") || (() => {
    const id = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
    localStorage.setItem("chat_session", id); return id;
  })());
  const [quickReplies, setQuickReplies] = useState(["How to apply?", "How is scoring done?", "Interview tips"]);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  async function send(text) {
    const msg = text || input.trim(); if (!msg || busy) return;
    setInput(""); setBusy(true); setQuickReplies([]);
    setMsgs(m => [...m, { role: "user", content: msg }]);
    try {
      const res = await api.chatMessage(msg, sessionId);
      setMsgs(m => [...m, { role: "assistant", content: res.reply }]);
      if (res.quick_replies?.length) setQuickReplies(res.quick_replies);
    } catch {
      setMsgs(m => [...m, { role: "assistant", content: "Sorry, I'm having trouble connecting. Please try again shortly." }]);
    } finally { setBusy(false); }
  }

  const bubbleStyle = (role) => ({
    maxWidth: "85%", padding: "11px 15px", borderRadius: role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    background: role === "user" ? "var(--accent-gradient)" : "#f1f5f9",
    color: role === "user" ? "#fff" : "var(--ink)", fontSize: "0.84rem", lineHeight: 1.55,
    marginLeft: role === "user" ? "auto" : 0, whiteSpace: "pre-wrap",
    border: role === "user" ? "none" : "1px solid #e2e8f0",
    boxShadow: role === "user" ? "0 4px 12px rgba(99,102,241,0.25)" : "0 1px 3px rgba(15,23,42,0.03)",
  });

  if (!user) return null;
  return (
    <>
      {/* Floating button */}
      <button onClick={() => setOpen(o => !o)} style={{
        position: "fixed", bottom: 24, right: 24, width: 56, height: 56, borderRadius: "50%",
        background: "var(--accent-gradient)", border: "none", cursor: "pointer",
        display: "flex", alignItems: "center", justifyContent: "center", color: "#fff",
        boxShadow: "0 8px 25px rgba(99,102,241,0.45)", zIndex: 1000, transition: "transform 0.2s cubic-bezier(0.16,1,0.3,1)",
      }}>
        {open ? <X size={22}/> : <MessageCircle size={22}/>}
      </button>

      {/* Chat window */}
      {open && (
        <div style={{
          position: "fixed", bottom: 92, right: 24, width: 370, height: 530,
          background: "#fff", borderRadius: 20, boxShadow: "0 16px 45px -8px rgba(15,23,42,0.22), 0 0 0 1px rgba(99,102,241,0.15)",
          display: "flex", flexDirection: "column", zIndex: 1000, overflow: "hidden",
        }}>
          {/* Header */}
          <div style={{ background: "linear-gradient(135deg, #061714 0%, #0a2420 100%)", padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: "1px solid rgba(16,185,129,0.15)" }}>
            <div style={{ width: 36, height: 36, borderRadius: 12, background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 2px 10px rgba(16,185,129,0.4)" }}>
              <Bot size={20} color="#fff"/>
            </div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: "0.94rem", letterSpacing: "-0.01em" }}>HireMind Assistant</div>
              <div style={{ color: "#6ee7b7", fontSize: "0.74rem", display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#10b981", display: "inline-block" }}/>
                AI career guide • Always active
              </div>
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 10px", display: "flex", flexDirection: "column", gap: 12 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                <div style={bubbleStyle(m.role)}>{m.content}</div>
              </div>
            ))}
            {busy && (
              <div style={{ display: "flex", gap: 5, padding: "10px 14px", background: "#f1f5f9", borderRadius: "18px 18px 18px 4px", width: "fit-content", border: "1px solid #e2e8f0" }}>
                {[0,1,2].map(i => <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#10b981", animation: `bounce 0.8s ${i*0.2}s infinite` }}/>)}
              </div>
            )}
            <div ref={bottomRef}/>
          </div>

          {/* Quick replies */}
          {quickReplies.length > 0 && !busy && (
            <div style={{ padding: "8px 16px", display: "flex", gap: 6, flexWrap: "wrap", background: "#f0fdf4" }}>
              {quickReplies.map((q, i) => (
                <button key={i} onClick={() => send(q)} style={{
                  fontSize: "0.74rem", padding: "5px 12px", border: "1px solid #a7f3d0",
                  borderRadius: 20, background: "#fff", color: "#059669", cursor: "pointer",
                  fontWeight: 600, boxShadow: "0 1px 3px rgba(16,185,129,0.08)", transition: "all 0.15s ease",
                }}>{q}</button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{ padding: "12px 16px", borderTop: "1px solid #e2e8f0", display: "flex", gap: 10, background: "#fff" }}>
            <input
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
              placeholder="Ask me anything…" disabled={busy}
              style={{ flex: 1, border: "1.5px solid #e2e8f0", borderRadius: 24, padding: "9px 16px", fontSize: "0.85rem", outline: "none", background: "#f8fafc" }}
            />
            <button onClick={() => send()} disabled={busy || !input.trim()} style={{
              width: 38, height: 38, borderRadius: "50%", background: "var(--accent-gradient)",
              border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
              opacity: busy || !input.trim() ? 0.45 : 1, boxShadow: "0 2px 10px rgba(16,185,129,0.3)",
            }}>
              <Send size={15} color="#fff"/>
            </button>
          </div>
        </div>
      )}
      <style>{`@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}`}</style>
    </>
  );
}

// ─── Multi-Job Matching ────────────────────────────────────────────────────────
function JobMatches({ matches }) {
  const nav = useNavigate();
  const [show, setShow] = useState(false);
  const top5 = matches.slice(0, 5);
  const scoreColor = (s) => s >= 70 ? "#10b981" : s >= 45 ? "#f59e0b" : "#94a3b8";

  return (
    <div className="card" style={{ padding: "26px 30px", marginTop: 24, border: "1px solid #e2e8f0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 10, fontSize: "1.15rem" }}>
          <div style={{ width: 32, height: 32, borderRadius: 10, background: "#fffbeb", border: "1px solid #fde68a", display: "grid", placeItems: "center" }}>
            <Star size={18} color="#f59e0b"/>
          </div>
          AI-Recommended Roles for You
        </h3>
        <button onClick={() => setShow(s => !s)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--accent)", fontSize: "0.84rem", fontWeight: 700 }}>
          {show ? "Show less ▲" : "Show all ▼"}
        </button>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {(show ? matches : top5).map((m, i) => (
          <div key={i} style={{ border: "1px solid #e2e8f0", borderRadius: 14, padding: "16px 18px", display: "flex", alignItems: "flex-start", gap: 16, background: "#fff", transition: "transform 0.2s ease, box-shadow 0.2s ease" }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--accent-gradient-subtle)", border: "1px solid var(--accent-border)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, color: "var(--accent)" }}>
              <Briefcase size={22}/>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: "0.98rem", marginBottom: 3, color: "var(--ink)" }}>{m.job.title}</div>
                  <div style={{ fontSize: "0.82rem", color: "var(--ink-muted)" }}>{m.job.location} · {m.job.employment_type}</div>
                </div>
                <div style={{ textAlign: "center", flexShrink: 0 }}>
                  <div style={{ width: 46, height: 46, borderRadius: "50%", background: `${scoreColor(m.match_score)}15`, border: `2px solid ${scoreColor(m.match_score)}`, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
                    <span style={{ fontSize: "0.88rem", fontWeight: 800, color: scoreColor(m.match_score), lineHeight: 1 }}>{Math.round(m.match_score)}</span>
                    <span style={{ fontSize: "0.58rem", color: "var(--ink-muted)", fontWeight: 700 }}>match</span>
                  </div>
                </div>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--ink-secondary)", marginTop: 8, lineHeight: 1.5 }}>{m.match_reason}</div>
              {m.matched_skills?.length > 0 && (
                <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginTop: 8 }}>
                  {m.matched_skills.slice(0, 4).map((s, j) => (
                    <span key={j} style={{ background: "#ecfdf5", color: "#065f46", border: "1px solid #a7f3d0", borderRadius: 99, padding: "2px 9px", fontSize: "0.72rem", fontWeight: 600 }}>✓ {s}</span>
                  ))}
                  {m.missing_skills?.slice(0, 2).map((s, j) => (
                    <span key={j} style={{ background: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca", borderRadius: 99, padding: "2px 9px", fontSize: "0.72rem", fontWeight: 600 }}>+ {s}</span>
                  ))}
                </div>
              )}
              <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
                {m.already_applied
                  ? <span style={{ fontSize: "0.78rem", color: "var(--ink-muted)", fontStyle: "italic", display: "inline-flex", alignItems: "center", gap: 4 }}>✓ Already applied</span>
                  : <button onClick={() => nav(`/apply/${m.job.id}`)} className="btn small">Apply Now →</button>
                }
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Smart Candidate Pipeline (Kanban) ───────────────────────────────────────
function Pipeline() {
  const { id } = useParams();
  const { data, loading, error, refetch } = useFetch(() => api.pipeline(id), [id]);
  const nav = useNavigate();

  if (loading) return <Shell><Loader/></Shell>;
  if (error)   return <Shell><ErrBanner message={error} onRetry={refetch}/></Shell>;
  if (!data)   return <Shell><Empty text="No pipeline data."/></Shell>;

  const COLS = [
    { key: "applied",     label: "Applied",     color: "#10b981", bg: "#ecfdf5", border: "#a7f3d0" },
    { key: "in_review",   label: "In Review",   color: "#f59e0b", bg: "#fffbeb", border: "#fde68a" },
    { key: "shortlisted", label: "Shortlisted", color: "#047857", bg: "#d1fae5", border: "#6ee7b7" },
    { key: "rejected",    label: "Rejected",    color: "#ef4444", bg: "#fef2f2", border: "#fecaca" },
  ];

  const scoreColor = (s) => s >= 70 ? "#10b981" : s >= 45 ? "#f59e0b" : "#ef4444";

  const pRec = data.recommendations || [];
  const getRecommendation = (aid) => pRec.find(r => r.application_id === aid);

  return (
    <Shell>
      <PageTitle
        eyebrow="SMART PIPELINE"
        title={`${data.job?.title} — Talent Pipeline`}
        sub={`${data.total} candidates across ${COLS.length} stages • AI-powered next-action recommendations`}
      />

      {/* Recommendations strip */}
      {pRec.filter(r => r.priority === "high").length > 0 && (
        <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 16, padding: "16px 20px", marginBottom: 24, boxShadow: "0 2px 8px rgba(245,158,11,0.08)" }}>
          <div style={{ fontWeight: 700, fontSize: "0.92rem", marginBottom: 12, display: "flex", alignItems: "center", gap: 8, color: "#92400e" }}>
            <Zap size={18} color="#d97706"/> High-Priority Recommended Actions
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {pRec.filter(r => r.priority === "high").slice(0, 3).map((r, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, background: "#fff", padding: "10px 14px", borderRadius: 10, border: "1px solid #fef3c7" }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: r.color, flexShrink: 0, boxShadow: `0 0 8px ${r.color}` }}/>
                <span style={{ fontWeight: 700, minWidth: 140, color: "var(--ink)", fontSize: "0.88rem" }}>{r.candidate_name}</span>
                <span style={{ background: r.color + "18", color: r.color, border: `1px solid ${r.color}35`, borderRadius: 99, padding: "2px 10px", fontSize: "0.75rem", fontWeight: 700 }}>{r.action}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--ink-muted)", flex: 1 }}>{r.reason}</span>
                <button onClick={() => nav(`/application/${r.application_id}`)} className="textBtn">Review →</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Kanban board */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 18 }}>
        {COLS.map(col => {
          const candidates = data.pipeline?.[col.key] || [];
          return (
            <div key={col.key} style={{ background: "#f8fafc", borderRadius: 16, padding: "16px 14px", minHeight: 340, border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, paddingBottom: 10, borderBottom: `2px solid ${col.color}25` }}>
                <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: col.color }}/>
                  <span style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--ink)" }}>{col.label}</span>
                </div>
                <span style={{ background: col.bg, color: col.color, border: `1px solid ${col.border}`, borderRadius: 99, padding: "2px 10px", fontSize: "0.74rem", fontWeight: 800 }}>
                  {candidates.length}
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {candidates.map(c => {
                  const rec = getRecommendation(c.id);
                  return (
                    <div key={c.id} style={{
                      background: "#fff", borderRadius: 12, padding: "14px", border: "1px solid #e2e8f0",
                      cursor: "pointer", transition: "transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease",
                      boxShadow: "0 2px 6px rgba(15,23,42,0.03)"
                    }}
                         onClick={() => nav(`/application/${c.id}`)}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--accent-gradient)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "0.85rem", flexShrink: 0, boxShadow: "0 2px 8px rgba(16,185,129,0.3)" }}>
                          {(c.candidate_name || "?")[0].toUpperCase()}
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontSize: "1.05rem", fontWeight: 800, color: scoreColor(c.final_score) }}>{Math.round(c.final_score)}</div>
                          <div style={{ fontSize: "0.62rem", color: "var(--ink-faint)", fontWeight: 700 }}>FIT</div>
                        </div>
                      </div>
                      <div style={{ marginTop: 10 }}>
                        <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--ink)" }}>{c.candidate_name}</div>
                        <div style={{ fontSize: "0.74rem", color: "var(--ink-muted)", marginTop: 3 }}>
                          {[c.interview_score != null && "Interview", c.coding_score != null && "Coding", c.projects_score != null && "Projects"].filter(Boolean).join(" · ") || "Resume only"}
                        </div>
                      </div>
                      {rec && (
                        <div style={{ marginTop: 10, background: rec.color + "12", border: `1px solid ${rec.color}30`, borderRadius: 8, padding: "5px 9px", fontSize: "0.72rem", color: rec.color, fontWeight: 700 }}>
                          💡 {rec.action}
                        </div>
                      )}
                    </div>
                  );
                })}
                {!candidates.length && (
                  <div style={{ textAlign: "center", color: "var(--ink-faint)", fontSize: "0.8rem", padding: "30px 0" }}>No candidates in this stage</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Shell>
  );
}

// ─── Candidate 360° Profile ────────────────────────────────────────────────────
function CandidateProfile360() {
  const { id } = useParams();
  const { data, loading, error, refetch } = useFetch(() => api.profile360(id), [id]);
  const nav = useNavigate();

  if (loading) return <Shell><Loader/></Shell>;
  if (error)   return <Shell><ErrBanner message={error} onRetry={refetch}/></Shell>;
  if (!data)   return <Shell><Empty text="Profile not found."/></Shell>;

  const statusColors = { applied: "#10b981", in_review: "#f59e0b", shortlisted: "#047857", rejected: "#ef4444" };
  const statusSc = statusColors[data.status] || "#10b981";
  const scoreColor = (s) => s >= 70 ? "#10b981" : s >= 45 ? "#f59e0b" : "#ef4444";

  return (
    <Shell>
      <PageTitle
        eyebrow="360° CANDIDATE PROFILE"
        title={`${data.candidate_name}`}
        sub={`Applying for: ${data.job_title} • ${data.assessments_completed}/${data.assessments_total} assessments completed`}
      />

      {/* Header stats */}
      <div className="stats">
        <Stat t="Composite Score" v={`${Math.round(data.final_score || 0)}/100`}/>
        <Stat t="Resume Score"    v={`${Math.round(data.resume_score || 0)}/100`}/>
        <Stat t="Assessments"     v={`${data.assessments_completed}/${data.assessments_total}`}/>
        <Stat t="Status"          v={<span style={{ color: statusSc, textTransform: "capitalize", fontWeight: 800 }}>{data.status?.replace("_"," ")}</span>}/>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginTop: 18 }}>

        {/* Pillar scores */}
        <div className="card" style={{ padding: "26px 28px" }}>
          <h3 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 10, fontSize: "1.1rem" }}>
            <Brain size={18} color="var(--accent)"/> Assessment Pillars
          </h3>
          {data.pillars?.map((p, i) => (
            <div key={i} style={{ marginBottom: 16, opacity: p.completed ? 1 : 0.45 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: 5 }}>
                <span style={{ fontWeight: 600, color: "var(--ink)" }}>{p.name}</span>
                <span style={{ color: p.completed ? scoreColor(p.score) : "var(--ink-faint)", fontWeight: 700 }}>
                  {p.completed ? `${Math.round(p.score)}/100` : "Pending"} ({p.weight}%)
                </span>
              </div>
              <div style={{ height: 8, background: "#f1f5f9", borderRadius: 99, overflow: "hidden", border: "1px solid #e2e8f0" }}>
                {p.completed && <div style={{ height: "100%", width: `${p.score}%`, background: p.color, borderRadius: 99, transition: "width 0.8s" }}/>}
              </div>
            </div>
          ))}
        </div>

        {/* Skill heatmap */}
        <div className="card" style={{ padding: "26px 28px" }}>
          <h3 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 10, fontSize: "1.1rem" }}>
            <Target size={18} color="var(--accent)"/> Skill Heatmap
          </h3>
          {data.skill_heatmap?.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
              {data.skill_heatmap.map((s, i) => (
                <span key={i} style={{ background: s.bg, color: s.color, borderRadius: 99, padding: "5px 14px", fontSize: "0.78rem", fontWeight: 700, border: `1px solid ${s.color}35`, display: "inline-flex", alignItems: "center", gap: 5 }}>
                  {s.status === "strong" ? "✓" : s.status === "gap" ? "✗" : "~"} {s.skill}
                </span>
              ))}
            </div>
          ) : (
            <div style={{ color: "var(--ink-muted)", fontSize: "0.85rem", marginTop: 12 }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {(data.matched_skills || []).map((s, i) => (
                  <span key={i} style={{ background: "#ecfdf5", color: "#065f46", border: "1px solid #a7f3d0", borderRadius: 99, padding: "4px 12px", fontSize: "0.78rem", fontWeight: 700 }}>✓ {s}</span>
                ))}
                {(data.missing_skills || []).map((s, i) => (
                  <span key={i} style={{ background: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca", borderRadius: 99, padding: "4px 12px", fontSize: "0.78rem", fontWeight: 700 }}>✗ {s}</span>
                ))}
              </div>
            </div>
          )}
          {data.ai_summary && (
            <div style={{ marginTop: 18, padding: "14px 16px", background: "var(--accent-gradient-subtle)", border: "1px solid var(--accent-border)", borderRadius: 12, fontSize: "0.84rem", lineHeight: 1.6, color: "var(--ink-secondary)" }}>
              <strong style={{ color: "var(--accent)" }}>AI Resume Summary:</strong><br/>{data.ai_summary}
            </div>
          )}
        </div>
      </div>

      {/* Activity timeline */}
      {data.timeline?.length > 0 && (
        <div className="card" style={{ padding: "26px 28px", marginTop: 18 }}>
          <h3 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 10, fontSize: "1.1rem" }}>
            <Activity size={18} color="var(--accent)"/> Assessment Timeline
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 0, marginTop: 16 }}>
            {data.timeline.map((t, i) => (
              <div key={i} style={{ display: "flex", gap: 18, position: "relative" }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: t.color + "15", border: `2px solid ${t.color}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 2px 8px ${t.color}25` }}>
                    <CheckCircle2 size={18} color={t.color}/>
                  </div>
                  {i < data.timeline.length - 1 && <div style={{ width: 2, flex: 1, background: "#e2e8f0", margin: "6px 0" }}/>}
                </div>
                <div style={{ paddingBottom: 18, flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: "0.92rem", color: "var(--ink)" }}>{t.event}</div>
                  <div style={{ display: "flex", gap: 8, marginTop: 5, alignItems: "center" }}>
                    <Badge label={`Score: ${Math.round(t.score)}/100`} color={t.color} bg={t.color + "15"}/>
                    {t.date && <span style={{ fontSize: "0.74rem", color: "var(--ink-faint)", fontWeight: 600 }}>{new Date(t.date).toLocaleDateString()}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
        <button onClick={() => nav(`/application/${id}`)} className="btn small">View Full Report →</button>
        <button onClick={() => nav(-1)} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "8px 18px", cursor: "pointer", color: "var(--ink-secondary)", fontSize: "0.85rem", fontWeight: 600 }}>← Back</button>
      </div>
    </Shell>
  );
}

// ─── App / Router ─────────────────────────────────────────────────────────────
export default function App() {
  return (
    <Routes>
      <Route path="/"                                   element={<Landing/>}/>
      <Route path="/login"                              element={<Auth/>}/>
      <Route path="/register"                           element={<Auth register/>}/>
      <Route path="/candidate"                          element={<Candidate/>}/>
      <Route path="/jobs"                               element={<Jobs/>}/>
      <Route path="/apply/:id"                          element={<Apply/>}/>
      <Route path="/applications"                       element={<Candidate/>}/>
      <Route path="/application/:id"                    element={<Application/>}/>
      <Route path="/application/:id/360"                element={<CandidateProfile360/>}/>
      <Route path="/recruiter"                          element={<Recruiter/>}/>
      <Route path="/recruiter/jobs"                     element={<Recruiter/>}/>
      <Route path="/recruiter/jobs/new"                 element={<NewJob/>}/>
      <Route path="/recruiter/jobs/:id"                 element={<Candidates/>}/>
      <Route path="/recruiter/jobs/:id/analysis"        element={<JobAnalysis/>}/>
      <Route path="/recruiter/jobs/:id/pipeline"        element={<Pipeline/>}/>
      <Route path="/recruiter/candidates"               element={<Recruiter/>}/>
      <Route path="*"                                   element={<Navigate to="/"/>}/>
    </Routes>
  );
}
