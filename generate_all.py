from thai_catalog_titles import get_thai_title
from quiz_translator import clean_thai_spacing
import os, sys, json, re, html
from bs4 import BeautifulSoup

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
RAW_DIR = os.path.join(BASE_DIR, "raw_html")
FOUNDATIONS_DIR = os.path.join(BASE_DIR, "foundations")
ARCHITECT_DIR = os.path.join(BASE_DIR, "architect")

os.makedirs(FOUNDATIONS_DIR, exist_ok=True)
os.makedirs(ARCHITECT_DIR, exist_ok=True)

def clean(t):
    if not t: return ""
    return clean_thai_spacing(" ".join(t.split()))

# Domain translation dictionaries
DOMAIN_NAMES_TH = {
    "Domain 1: Agents and Workflows": "สถาปัตยกรรมเอเจนต์และเวิร์กโฟลว์ (Agents & Workflows)",
    "Domain 2: Applications and Integration": "การพัฒนาแอปพลิเคชันและการเชื่อมต่อระบบ (Applications & Integration)",
    "Domain 3: Claude Code": "การใช้งานและการตั้งค่า Claude Code",
    "Domain 4: Eval, Testing, and Debugging": "การประเมินผล การทดสอบ และการแก้จุดบกพร่อง (Eval & Debugging)",
    "Domain 5: Model Selection and Optimization": "การเลือกรุ่นโมเดลและการปรับแต่งประสิทธิภาพ (Model Selection & Optimization)",
    "Domain 6: Prompt and Context Engineering": "วิศวกรรมพร้อมต์และการจัดการ Context Window",
    "Domain 7: Security and Safety": "ความปลอดภัย การควบคุม และการป้องกันระบบ (Security & Safety)",
    "Domain 8: Tools and MCPs": "การใช้งานเครื่องมือและ Model Context Protocol (Tools & MCPs)",
    "Domain 1: Agentic Architectures and Workflows": "สถาปัตยกรรมเอเจนต์ขั้นสูงและรูปแบบเวิร์กโฟลว์ (Agentic Architectures)",
    "Domain 2: Model Selection and Prompt Engineering": "การเลือกรุ่นโมเดลเชิงกลยุทธ์และวิศวกรรมพร้อมต์องค์กร",
    "Domain 3: Tools, Retrieval, and Integration": "เครื่องมือขั้นสูง ระบบ RAG และการเชื่อมต่อระบบ (Tools & Retrieval)",
    "Domain 4: Evaluation, Testing, and Optimization": "กรอบการประเมินผล การทดสอบ และการปรับแต่งต้นทุน/ความเร็ว",
    "Domain 5: Security, Safety, and Compliance": "ความปลอดภัยระดับองค์กร กฎระเบียบ HIPAA/GDPR และการกำกับดูแล",
    "Domain 6: Solution Design and Communication": "การออกแบบสถาปัตยกรรมโซลูชันและการสื่อสารกับผู้มีส่วนได้ส่วนเสีย",
    "Domain 7: Claude Code Operation and Deployment": "การควบคุมและส่งมอบนโยบายสำหรับทีม Claude Code",
}

with open(os.path.join(BASE_DIR, "raw_data/foundations_slugs.json")) as f:
    f_slugs = json.load(f)
with open(os.path.join(BASE_DIR, "raw_data/architect_slugs.json")) as f:
    a_slugs = json.load(f)

# Extract RSC block & questions
def extract_rsc(html_str):
    pushes = re.findall(r"self\.__next_f\.push\(\[1,\"(.*?)\"\]\)", html_str)
    full_rsc = "".join(pushes).replace('\\"', '"').replace('\\\\', '\\')
    
    blocks = {}
    for m in re.finditer(r'"block":\s*(\{.*?\}(?=,"linkId"|,"position"))', full_rsc):
        try:
            b_data = json.loads(m.group(1))
            b_id = b_data.get("id")
            if b_id: blocks[str(b_id)] = b_data
        except Exception: pass
        
    questions = {}
    for m in re.finditer(r'"question":\s*(\{.*?\}(?=,"vendor"))', full_rsc):
        try:
            q_data = json.loads(m.group(1))
            q_id = q_data.get("id")
            if q_id: questions[str(q_id)] = q_data
        except Exception: pass
        
    return blocks, questions

# Extract single file data
def parse_lesson_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, "html.parser")
    article = soup.find("article")
    if not article: return None
    
    h1 = soup.find("h1")
    title = clean(h1.get_text()) if h1 else ""
    
    # meta description for subdomain
    sub_no, sub_title, domain_no = "", "", ""
    m = re.search(r"Subdomain\s+([\d\.]+):\s+([^,\.\"]+)", html_content)
    if m:
        sub_no = m.group(1)
        sub_title = clean(m.group(2))
        domain_no = sub_no.split(".")[0]
        
    # Badges
    badges = []
    meta_div = article.find("div", class_=re.compile("flex-wrap.*gap-1.5"))
    if meta_div:
        for span in meta_div.find_all("span"):
            t = clean(span.get_text())
            if t: badges.append(t)
            
    # Objectives
    objectives = []
    obj_sec = article.find(lambda t: t.name == "section" and "What you will be able to do" in t.get_text())
    if obj_sec:
        for li in obj_sec.find_all("li"):
            objectives.append(clean(li.get_text(separator=" ")))
            
    # Key concept
    key_concept = ""
    kc_sec = article.find(lambda t: t.name == "section" and "Key concept" in t.get_text())
    if kc_sec:
        kc_text = clean(kc_sec.get_text(separator=" ")).replace("Key concept", "", 1).strip()
        key_concept = kc_text
        
    blocks, questions = extract_rsc(html_content)
    
    # Sections
    sections = []
    for sec in article.find_all("section"):
        h2 = sec.find("h2")
        if not h2: continue
        h2_text = clean(h2.get_text(separator=" "))
        if any(ignore in h2_text for ignore in ["What you will be able to do", "Key concept", "In this lesson", "Ready to test yourself?"]):
            continue
            
        items = []
        for child in sec.children:
            if not hasattr(child, "name") or not child.name or child.name == "h2":
                continue
            
            if child.name == "aside":
                items.append({"type": "exam_trap", "text": clean(child.get_text(separator=" "))})
            elif child.name == "figure":
                table = child.find("table")
                if table:
                    headers = [clean(th.get_text(separator=" ")) for th in table.find_all("th")]
                    rows = [[clean(td.get_text(separator=" ")) for td in tr.find_all("td")] for tr in table.find_all("tr") if tr.find_all("td")]
                    cap = child.find("figcaption")
                    items.append({
                        "type": "table",
                        "caption": clean(cap.get_text(separator=" ")) if cap else "",
                        "headers": headers,
                        "rows": rows
                    })
                else:
                    items.append({"type": "figure_text", "text": clean(child.get_text(separator=" "))})
            elif child.name == "pre":
                items.append({"type": "code", "text": child.get_text()})
            elif child.name == "p":
                t = clean(child.get_text(separator=" "))
                if not re.match(r"^Sources\s*\d+", t):
                    items.append({"type": "paragraph", "text": t})
            elif child.name in ["ul", "ol"]:
                items.append({
                    "type": "list",
                    "ordered": child.name == "ol",
                    "items": [clean(li.get_text(separator=" ")) for li in child.find_all("li")]
                })
            elif child.name == "div" and child.get("data-checkpoint-key"):
                ckey = child.get("data-checkpoint-key")
                items.append({"type": "checkpoint_ref", "key": ckey})
                
        sections.append({"heading": h2_text, "items": items})
        
    sources = []
    for dt in article.find_all("details"):
        if "Sources" in dt.get_text():
            for a in dt.find_all("a"):
                href = a.get("href", "")
                stitle = clean(a.get_text())
                if href and stitle and href.startswith("http"):
                    sources.append({"url": href, "title": stitle})
                    
    return {
        "title": title,
        "sub_no": sub_no,
        "sub_title": sub_title,
        "domain_no": domain_no,
        "badges": badges,
        "objectives": objectives,
        "key_concept": key_concept,
        "sections": sections,
        "blocks": blocks,
        "questions": questions,
        "sources": sources
    }

print("Loaded parser module.")

# Domain titles map
FOUNDATIONS_DOMAINS = {
    "1": "Domain 1: Agents and Workflows (สถาปัตยกรรมเอเจนต์และเวิร์กโฟลว์)",
    "2": "Domain 2: Applications and Integration (การพัฒนาแอปพลิเคชันและการเชื่อมต่อระบบ)",
    "3": "Domain 3: Claude Code (การใช้งานและการตั้งค่า Claude Code)",
    "4": "Domain 4: Eval, Testing, and Debugging (การประเมินผล การทดสอบ และการแก้จุดบกพร่อง)",
    "5": "Domain 5: Model Selection and Optimization (การเลือกรุ่นโมเดลและการปรับแต่งประสิทธิภาพ)",
    "6": "Domain 6: Prompt and Context Engineering (วิศวกรรมพร้อมต์และการจัดการ Context Window)",
    "7": "Domain 7: Security and Safety (ความปลอดภัย การควบคุม และการป้องกันระบบ)",
    "8": "Domain 8: Tools and MCPs (การใช้งานเครื่องมือและ Model Context Protocol)",
}

ARCHITECT_DOMAINS = {
    "1": "Domain 1: Agentic Architectures and Workflows (สถาปัตยกรรมเอเจนต์ขั้นสูงและรูปแบบเวิร์กโฟลว์)",
    "2": "Domain 2: Model Selection and Prompt Engineering (การเลือกรุ่นโมเดลเชิงกลยุทธ์และวิศวกรรมพร้อมต์องค์กร)",
    "3": "Domain 3: Tools, Retrieval, and Integration (เครื่องมือขั้นสูง ระบบ RAG และการเชื่อมต่อระบบ)",
    "4": "Domain 4: Evaluation, Testing, and Optimization (กรอบการประเมินผล การทดสอบ และการปรับแต่งต้นทุน/ความเร็ว)",
    "5": "Domain 5: Security, Safety, and Compliance (ความปลอดภัยระดับองค์กร กฎระเบียบ HIPAA/GDPR และการกำกับดูแล)",
    "6": "Domain 6: Solution Design and Communication (การออกแบบสถาปัตยกรรมโซลูชันและการสื่อสารกับผู้มีส่วนได้ส่วนเสีย)",
    "7": "Domain 7: Claude Code Operation and Deployment (การควบคุมและส่งมอบนโยบายสำหรับทีม Claude Code)",
}

def build_catalogs():
    f_cat = []
    for idx, slug in enumerate(f_slugs, 1):
        fp = os.path.join(RAW_DIR, f"claude-developer-foundations_{slug}.html")
        p = parse_lesson_file(fp)
        d_no = p["domain_no"] if p and p["domain_no"] else "1"
        d_title = FOUNDATIONS_DOMAINS.get(d_no, f"Domain {d_no}")
        orig_title = p["title"] if p else slug
        th_title = get_thai_title(slug, orig_title, is_foundations=True)
        f_cat.append({
            "idx": idx,
            "slug": slug,
            "filename": f"lesson-{idx:02d}.html",
            "title": th_title,
            "title_en": orig_title,
            "sub_no": p["sub_no"] if p else "",
            "sub_title": p["sub_title"] if p else "",
            "domain_no": d_no,
            "domain_title": d_title,
            "badges": p["badges"] if p else [],
            "raw_file": fp
        })
        
    a_cat = []
    for idx, slug in enumerate(a_slugs, 1):
        fp = os.path.join(RAW_DIR, f"claude-architect-professional_{slug}.html")
        p = parse_lesson_file(fp)
        d_no = p["domain_no"] if p and p["domain_no"] else "1"
        d_title = ARCHITECT_DOMAINS.get(d_no, f"Domain {d_no}")
        orig_title = p["title"] if p else slug
        th_title = get_thai_title(slug, orig_title, is_foundations=False)
        a_cat.append({
            "idx": idx,
            "slug": slug,
            "filename": f"lesson-{idx:02d}.html",
            "title": th_title,
            "title_en": orig_title,
            "sub_no": p["sub_no"] if p else "",
            "sub_title": p["sub_title"] if p else "",
            "domain_no": d_no,
            "domain_title": d_title,
            "badges": p["badges"] if p else [],
            "raw_file": fp
        })
        
    return f_cat, a_cat

f_catalog, a_catalog = build_catalogs()
print(f"Catalogs built: Foundations ({len(f_catalog)}), Architect ({len(a_catalog)})")
