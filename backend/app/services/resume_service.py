import io,re
import pdfplumber
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS=["python","java","c++","c#","javascript","typescript","go","rust","sql","mysql","postgresql","mongodb","redis","sqlite","html","css","react","angular","vue","next.js","node.js","express","django","flask","fastapi","spring boot","machine learning","deep learning","nlp","computer vision","data science","tensorflow","pytorch","scikit-learn","pandas","numpy","keras","aws","azure","gcp","docker","kubernetes","terraform","jenkins","git","github","linux","bash","excel","power bi","tableau","communication","leadership","teamwork","agile","scrum","rest api","graphql","microservices","data structures","algorithms","system design","testing","unit testing"]

def extract_text(data,filename):
    name=filename.lower()
    if name.endswith('.pdf'):
        with pdfplumber.open(io.BytesIO(data)) as pdf: return '\n'.join((p.extract_text() or '') for p in pdf.pages)
    if name.endswith('.docx'):
        return '\n'.join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    if name.endswith('.txt'): return data.decode('utf-8',errors='ignore')
    raise ValueError('Only PDF, DOCX and TXT resumes are supported')

def skills(text):
    t=text.lower(); return sorted({s for s in SKILLS if re.search(r'(?<![\w+#])'+re.escape(s)+r'(?![\w+#])',t)})

def experience(text):
    nums=[int(x) for x in re.findall(r'(\d{1,2})\+?\s*(?:years?|yrs?)',text.lower())]
    return max(nums,default=0)

def score_resume(text,job):
    req=[s.lower().strip() for s in job['skills']]
    found=skills(text); matched=[s for s in req if s in found]; missing=[s for s in req if s not in found]
    try: sim=cosine_similarity(TfidfVectorizer(stop_words='english').fit_transform([text,job['description']]))[0,1]
    except Exception: sim=0
    exp=experience(text); exp_score=100 if job['experience']==0 or exp>=job['experience'] else max(0,100*exp/max(job['experience'],1))
    skill_score=100*len(matched)/max(len(req),1)
    total=round(.45*min(sim*100,100)+.40*skill_score+.15*exp_score,2)
    return total,matched,missing,round(exp_score,2)
