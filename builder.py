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
    return " ".join(t.split())

# 1. Load slugs
with open(os.path.join(BASE_DIR, "raw_data/foundations_slugs.json")) as f:
    f_slugs = json.load(f)
with open(os.path.join(BASE_DIR, "raw_data/architect_slugs.json")) as f:
    a_slugs = json.load(f)

# Helper for RSC data
def extract_rsc_data(html_content):
    pushes = re.findall(r"self\.__next_f\.push\(\[1,\"(.*?)\"\]\)", html_content)
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
        
    return blocks, questions, full_rsc

def extract_meta_and_tree(course_slug, slugs):
    catalog = []
    current_domain = "Domain 1"
    
    for idx, slug in enumerate(slugs, 1):
        fp = os.path.join(RAW_DIR, f"{course_slug}_{slug}.html")
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        soup = BeautifulSoup(html_content, "html.parser")
        h1 = soup.find("h1")
        title = clean(h1.get_text()) if h1 else slug.replace("-", " ").title()
        
        # Domain detection from RSC or sidebar
        d_match = re.search(r"\"domain\":\s*\"(Domain\s+\d+:\s+[^\"]+)\"", html_content)
        domain = d_match.group(1) if d_match else ""
        if not domain:
            # fallback find Domain in sidebar
            sidebar_domains = re.findall(r"Domain\s+\d+:\s+[^\"<]+", html_content)
            if sidebar_domains:
                domain = sidebar_domains[0]
                
        sd_match = re.search(r"\"subdomain\":\s*\"(Subdomain\s+[\d\.]+:\s+[^\"]+)\"", html_content)
        subdomain = sd_match.group(1) if sd_match else ""
        
        catalog.append({
            "idx": idx,
            "slug": slug,
            "filename": f"lesson-{idx:02d}.html",
            "title": title,
            "domain": domain,
            "subdomain": subdomain,
            "raw_file": fp
        })
    return catalog

print("Extracting catalogs...")
f_catalog = extract_meta_and_tree("claude-developer-foundations", f_slugs)
a_catalog = extract_meta_and_tree("claude-architect-professional", a_slugs)
print(f"Foundations catalog: {len(f_catalog)} lessons")
print(f"Architect catalog: {len(a_catalog)} lessons")
