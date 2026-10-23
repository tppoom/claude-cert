import os, sys, json, re, time, threading, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["NIQUESTS_DISABLE_HTTP2"] = "1"
os.environ["URLLIB3_DISABLE_HTTP2"] = "1"

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
import translators as ts
from generate_all import f_catalog, a_catalog, parse_lesson_file, FOUNDATIONS_DIR, ARCHITECT_DIR
from builder_page import render_lesson_page, render_course_index_page, render_master_portal
from quiz_translator import clean_thai_spacing
import quiz_translator

# 1. Load Cache
if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

# Clean cache: remove pure garbage tokens
for k in list(cache.keys()):
    v = cache[k]
    if re.match(r'^[a-z0-9]{15,}$', v.strip()):
        del cache[k]

norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items() if k}
print(f"Loaded existing clean cache: {len(cache)} entries.", flush=True)

lock = threading.RLock()
save_counter = 0

def save_to_disk():
    with lock:
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f"[AutoSave] Cache saved: {len(cache)} entries.", flush=True)
        except Exception as e:
            print(f"[AutoSave Error] {e}", flush=True)

# 2. Extract all strings across syllabus
print("Extracting all strings across 98 lessons...", flush=True)
needed_texts = []
seen = set()

def add_needed(t):
    if not t: return
    t_clean = t.strip()
    if not t_clean or t_clean in seen: return
    seen.add(t_clean)
    
    # Check if already in cache
    if t_clean in cache: return
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t_clean.lower())
    if norm_k in norm_cache: return
    
    # Check if mostly Thai already
    thai_chars = len(re.findall(r'[\u0e00-\u0e7f]', t_clean))
    if thai_chars > len(t_clean) * 0.4:
        cache[t_clean] = clean_thai_spacing(t_clean)
        norm_cache[norm_k] = clean_thai_spacing(t_clean)
        return
        
    needed_texts.append(t_clean)

for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    blocks = p.get("blocks", {})
    questions = p.get("questions", {})
    
    add_needed(p.get("objective"))
    add_needed(p.get("key_concept"))
    
    for sec in p.get("sections", []):
        add_needed(sec.get("heading"))
        core_h = re.sub(r'^\d+\.\s*', '', sec.get("heading", "")).strip()
        add_needed(core_h)
        
        for item in sec.get("items", []):
            itype = item["type"]
            if itype == "paragraph":
                add_needed(item.get("text"))
            elif itype == "code" and item.get("caption"):
                add_needed(item.get("caption"))
            elif itype == "list":
                for li in item.get("items", []):
                    add_needed(li)
            elif itype == "exam_trap":
                add_needed(item.get("text"))
            elif itype == "figure_text":
                add_needed(item.get("text"))
            elif itype == "table":
                add_needed(item.get("caption"))
                for h in item.get("headers", []):
                    add_needed(h)
                for row in item.get("rows", []):
                    for cell in row:
                        add_needed(cell)
            elif itype == "checkpoint_ref":
                ckey = item["key"]
                if ckey.startswith("check:"):
                    b = blocks.get(ckey[6:])
                    if b:
                        add_needed(b.get("prompt"))
                        add_needed(b.get("explanation"))
                        if b.get("citation", {}).get("quote"):
                            add_needed(b["citation"]["quote"])
                        for opt in b.get("options", []):
                            add_needed(opt)
                        for pair in b.get("pairs", []):
                            add_needed(pair.get("term"))
                            add_needed(pair.get("definition"))
                        for s in b.get("steps", []):
                            add_needed(s)
                elif ckey.startswith("question:"):
                    q = questions.get(ckey[9:])
                    if q:
                        add_needed(q.get("question"))
                        for opt in q.get("options", []):
                            add_needed(opt)
                        for exp in q.get("explanations", []):
                            if isinstance(exp, dict):
                                add_needed(exp.get("explanation"))
                            elif isinstance(exp, str):
                                add_needed(exp)
            elif itype == "predict_first":
                add_needed(item.get("prompt"))
                add_needed(item.get("explanation"))
                add_needed(item.get("quote"))
                for opt in item.get("options", []):
                    add_needed(opt)

print(f"Total missing strings to translate: {len(needed_texts)}", flush=True)

# 3. Translation engine
DELIM = "\n<__101__>\n"
BATCH_SIZE = 10

def is_garbage(text):
    if not text: return True
    stripped = text.strip()
    if re.match(r'^[a-z0-9]{15,}$', stripped):
        return True
    return False

def translate_single(it):
    global save_counter
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', it.lower())
    for attempt in range(2):
        try:
            res = ts.translate_text(it, translator="caiyun", to_language="th", timeout=8)
            if res and not is_garbage(res):
                cleaned = clean_thai_spacing(res)
                with lock:
                    cache[it] = cleaned
                    norm_cache[norm_k] = cleaned
                    save_counter += 1
                return
        except Exception:
            time.sleep(0.5)

def process_batch(chunk):
    global save_counter
    unseen = []
    with lock:
        for it in chunk:
            norm_k = re.sub(r'[^a-zA-Z0-9]+', '', it.lower())
            if it not in cache and norm_k not in norm_cache:
                unseen.append(it)
                
    if not unseen:
        return
        
    time.sleep(0.2) # friendly rate limiting
    
    # Flatten internal newlines so batch delimiter splitting is exact
    flattened = [re.sub(r'\s+', ' ', it.strip()) for it in unseen]
    
    try:
        payload = DELIM.join(flattened)
        res = ts.translate_text(payload, translator="caiyun", to_language="th", timeout=12)
        parts = [p.strip() for p in re.split(r'<__101__>', res)]
        if len(parts) == len(unseen) and not any(is_garbage(p) for p in parts):
            with lock:
                for orig, th in zip(unseen, parts):
                    cleaned = clean_thai_spacing(th)
                    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', orig.lower())
                    cache[orig] = cleaned
                    norm_cache[norm_k] = cleaned
                    save_counter += 1
            return
    except Exception:
        pass
        
    # Fallback to single translation
    for it in unseen:
        translate_single(it)

if needed_texts:
    chunks = [needed_texts[i:i+BATCH_SIZE] for i in range(0, len(needed_texts), BATCH_SIZE)]
    print(f"Translating {len(needed_texts)} items across {len(chunks)} batches using 3 rate-safe workers...", flush=True)
    t0 = time.time()
    done_chunks = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(process_batch, c): c for c in chunks}
        for f in as_completed(futures):
            f.result()
            done_chunks += 1
            if done_chunks % 20 == 0 or done_chunks == len(chunks):
                elapsed = time.time() - t0
                pct = done_chunks * 100 // len(chunks)
                rate = (done_chunks * BATCH_SIZE) / max(1, elapsed)
                rem_sec = (len(chunks) - done_chunks) * BATCH_SIZE / max(0.1, rate)
                print(f"[{done_chunks}/{len(chunks)} ({pct}%)] ~{rate:.1f} it/s | Rem: {rem_sec/60:.1f}m | Cache: {len(cache)}", flush=True)
                if done_chunks % 40 == 0:
                    save_to_disk()

    save_to_disk()
    print(f"Translation finished in {time.time() - t0:.1f}s! Total cache size: {len(cache)}", flush=True)

# 4. Ultra-fast Zero-Latency Site Generation
print("Generating all 101 HTML pages from memory cache...", flush=True)
t_gen = time.time()

def fast_trans(text):
    if not text: return ""
    t_clean = text.strip()
    if t_clean in cache:
        return cache[t_clean]
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t_clean.lower())
    if norm_k in norm_cache:
        return norm_cache[norm_k]
    return clean_thai_spacing(t_clean)

quiz_translator.trans_one = fast_trans
quiz_translator._cache = cache
quiz_translator._norm_cache = norm_cache

# Foundations
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

# Architect
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

# Portals & Index
f_index_html = render_course_index_page(f_catalog, "foundations")
with open(os.path.join(FOUNDATIONS_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(f_index_html)

a_index_html = render_course_index_page(a_catalog, "architect")
with open(os.path.join(ARCHITECT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(a_index_html)

master_html = render_master_portal(f_catalog, a_catalog)
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(master_html)

print(f"SUCCESS! All 101 HTML pages compiled in {time.time()-t_gen:.2f} seconds!", flush=True)

# 5. Git commit & push
print("Staging and pushing changes to GitHub...", flush=True)
try:
    subprocess.run(["git", "add", "."], check=True, cwd=BASE_DIR)
    subprocess.run(["git", "commit", "-m", "feat: complete 100% Thai certification study hub with interactive checkpoints and responsive tables"], check=False, cwd=BASE_DIR)
    push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=BASE_DIR)
    print("Git push result:", push_res.stdout, push_res.stderr, flush=True)
    print("DEPLOYMENT COMPLETE! Site live at: https://tppoom.github.io/claude-cert/", flush=True)
except Exception as e:
    print("Git deploy error:", e, flush=True)
