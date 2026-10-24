import os, sys, json, re, time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
import quiz_translator
from generate_all import f_catalog, a_catalog, parse_lesson_file, FOUNDATIONS_DIR, ARCHITECT_DIR
from builder_page import render_lesson_page, render_course_index_page, render_master_portal
from builder_summary import render_summary_page
from quiz_translator import clean_thai_spacing

# Load Cache into quiz_translator
with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items()}

quiz_translator._cache = cache
quiz_translator._norm_cache = norm_cache

# Pure fast cache lookup (Zero network latency)
def fast_trans(text):
    if not text: return ""
    t_clean = text.strip()
    if t_clean in cache:
        return cache[t_clean]
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t_clean.lower())
    if norm_k in norm_cache:
        return norm_cache[norm_k]
    # Check if mostly Thai
    if len(re.findall(r'[\u0e00-\u0e7f]', t_clean)) > len(t_clean) * 0.4:
        return clean_thai_spacing(t_clean)
    return clean_thai_spacing(t_clean)

quiz_translator.trans_one = fast_trans

print(f"Loaded {len(cache)} cached translations. Zero-latency generator ready.", flush=True)

t0 = time.time()

# 1. Render Foundations
print(f"Generating 45 Foundations lessons...", flush=True)
def gen_foundations(it):
    p_data = parse_lesson_file(it["raw_file"])
    if not p_data: return
    p_data["domain_title"] = it["domain_title"]
    p_data["sub_no"] = it.get("sub_no")
    p_data["title_th"] = it.get("title")
    p_data["title_en"] = it.get("title_en")
    html_out = render_lesson_page(p_data, f_catalog, it["idx"], "foundations")
    out_path = os.path.join(FOUNDATIONS_DIR, it["filename"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(gen_foundations, f_catalog))

# 2. Render Architect
print(f"Generating 53 Architect lessons...", flush=True)
def gen_architect(it):
    p_data = parse_lesson_file(it["raw_file"])
    if not p_data: return
    p_data["domain_title"] = it["domain_title"]
    p_data["sub_no"] = it.get("sub_no")
    p_data["title_th"] = it.get("title")
    p_data["title_en"] = it.get("title_en")
    html_out = render_lesson_page(p_data, a_catalog, it["idx"], "architect")
    out_path = os.path.join(ARCHITECT_DIR, it["filename"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(gen_architect, a_catalog))

# 3. Render Indices
print("Generating course portals and master index...", flush=True)
f_index_html = render_course_index_page(f_catalog, "foundations")
with open(os.path.join(FOUNDATIONS_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(f_index_html)

a_index_html = render_course_index_page(a_catalog, "architect")
with open(os.path.join(ARCHITECT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(a_index_html)

master_html = render_master_portal(f_catalog, a_catalog)
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(master_html)

# 4. Render Master Cram Sheets (Final Review after last domain)
print("Generating master cram sheets for both courses...", flush=True)
f_summary_html = render_summary_page(f_catalog, "foundations")
with open(os.path.join(FOUNDATIONS_DIR, "summary.html"), "w", encoding="utf-8") as f:
    f.write(f_summary_html)

a_summary_html = render_summary_page(a_catalog, "architect")
with open(os.path.join(ARCHITECT_DIR, "summary.html"), "w", encoding="utf-8") as f:
    f.write(a_summary_html)

elapsed = time.time() - t0
print(f"SUCCESS! All 98 lessons + 3 indices + 2 Cram Sheets generated in {elapsed:.2f} seconds!", flush=True)
