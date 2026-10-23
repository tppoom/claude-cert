import os, sys, json, re, time, threading
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
from quiz_translator import clean_thai_spacing, _cache, _norm_cache
from deep_translator import MyMemoryTranslator

# 1. Load Cache
if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

# Keep only entries that contain Thai or are short symbols/numbers
cache = {k: v for k, v in cache.items() if len(re.findall(r'[\u0e00-\u0e7f]', v)) > 0 or len(k) <= 3}
norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items() if k}

print(f"Clean cached entries with Thai: {len(cache)}", flush=True)

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

# 2. Collect ALL strings needed for the full site
print("Extracting all text elements across 98 lessons...", flush=True)
needed_texts = set()

for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    blocks = p.get("blocks", {})
    questions = p.get("questions", {})
    
    # Headings and Objectives
    if p.get("objective"): needed_texts.add(p["objective"].strip())
    if p.get("key_concept"): needed_texts.add(p["key_concept"].strip())
    
    for sec in p.get("sections", []):
        if sec.get("heading"):
            needed_texts.add(sec["heading"].strip())
            core_h = re.sub(r'^\d+\.\s*', '', sec["heading"]).strip()
            if core_h: needed_texts.add(core_h)
            
        for item in sec.get("items", []):
            itype = item["type"]
            if itype == "paragraph":
                t = item.get("text", "").strip()
                if t: needed_texts.add(t)
            elif itype == "code" and item.get("caption"):
                t = item["caption"].strip()
                if t: needed_texts.add(t)
            elif itype == "list":
                for li in item.get("items", []):
                    t = li.strip()
                    if t: needed_texts.add(t)
            elif itype == "exam_trap":
                t = item.get("text", "").strip()
                if t: needed_texts.add(t)
            elif itype == "figure_text":
                t = item.get("text", "").strip()
                if t: needed_texts.add(t)
            elif itype == "table":
                if item.get("caption"):
                    needed_texts.add(item["caption"].strip())
                for h in item.get("headers", []):
                    if h: needed_texts.add(h.strip())
                for row in item.get("rows", []):
                    for cell in row:
                        if cell: needed_texts.add(cell.strip())
            elif itype == "checkpoint_ref":
                ckey = item["key"]
                if ckey.startswith("check:"):
                    b = blocks.get(ckey[6:])
                    if b:
                        if b.get("prompt"): needed_texts.add(b["prompt"].strip())
                        if b.get("explanation"): needed_texts.add(b["explanation"].strip())
                        if b.get("citation", {}).get("quote"): needed_texts.add(b["citation"]["quote"].strip())
                        for opt in b.get("options", []):
                            if opt: needed_texts.add(opt.strip())
                        for pair in b.get("pairs", []):
                            if pair.get("term"): needed_texts.add(pair["term"].strip())
                            if pair.get("definition"): needed_texts.add(pair["definition"].strip())
                        for s in b.get("steps", []):
                            if s: needed_texts.add(s.strip())
                elif ckey.startswith("question:"):
                    q = questions.get(ckey[9:])
                    if q:
                        if q.get("question"): needed_texts.add(q["question"].strip())
                        for opt in q.get("options", []):
                            if opt: needed_texts.add(opt.strip())
                        for exp in q.get("explanations", []):
                            if isinstance(exp, dict) and exp.get("explanation"):
                                needed_texts.add(exp["explanation"].strip())
                            elif isinstance(exp, str):
                                needed_texts.add(exp.strip())
            elif itype == "predict_first":
                if item.get("prompt"): needed_texts.add(item["prompt"].strip())
                if item.get("explanation"): needed_texts.add(item["explanation"].strip())
                if item.get("quote"): needed_texts.add(item["quote"].strip())
                for opt in item.get("options", []):
                    if opt: needed_texts.add(opt.strip())

to_translate = []
for t in needed_texts:
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t.lower())
    val = cache.get(t) or norm_cache.get(norm_k)
    if not val or (len(re.findall(r'[\u0e00-\u0e7f]', val)) == 0 and len(t) > 3):
        # Also check if text is already >40% Thai
        if len(re.findall(r'[\u0e00-\u0e7f]', t)) > len(t) * 0.4:
            cleaned = clean_thai_spacing(t)
            cache[t] = cleaned
            norm_cache[norm_k] = cleaned
        else:
            to_translate.append(t)

print(f"Total unique strings needed: {len(needed_texts)}")
print(f"Already cached / Thai: {len(needed_texts) - len(to_translate)}")
print(f"To translate: {len(to_translate)}", flush=True)

# 3. Translation logic
DELIM = "\n===ITEM===\n"
BATCH_SIZE = 6

def is_valid_thai(text):
    if not text: return False
    stripped = text.strip()
    if len(re.findall(r'[\u0e00-\u0e7f]', stripped)) == 0:
        return False
    # Reject random tokens (e.g. k63lbeouqvc8oyt57rrs)
    if re.match(r'^[a-z0-9]{15,}$', stripped):
        return False
    return True

def translate_single_item(it):
    global save_counter
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', it.lower())
    # Try Caiyun
    try:
        res = ts.translate_text(it, translator="caiyun", to_language="th")
        if is_valid_thai(res):
            cleaned = clean_thai_spacing(res)
            with lock:
                cache[it] = cleaned
                norm_cache[norm_k] = cleaned
                save_counter += 1
            return
    except Exception:
        pass
        
    # Try MyMemory
    try:
        res = MyMemoryTranslator(source="english", target="thai").translate(it)
        if is_valid_thai(res):
            cleaned = clean_thai_spacing(res)
            with lock:
                cache[it] = cleaned
                norm_cache[norm_k] = cleaned
                save_counter += 1
            return
    except Exception:
        pass

def translate_chunk(chunk):
    global save_counter
    # Filter items not yet cached
    unseen = []
    with lock:
        for it in chunk:
            norm_k = re.sub(r'[^a-zA-Z0-9]+', '', it.lower())
            if it not in cache and norm_k not in norm_cache:
                unseen.append(it)
                
    if not unseen:
        return
        
    # Attempt batch translation with Caiyun
    try:
        payload = DELIM.join(unseen)
        res = ts.translate_text(payload, translator="caiyun", to_language="th")
        parts = [p.strip() for p in re.split(r'===ITEM===', res, flags=re.I)]
        if len(parts) == len(unseen) and all(is_valid_thai(p) for p in parts):
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
        
    # Fallback to item-by-item
    for it in unseen:
        translate_single_item(it)

if to_translate:
    chunks = [to_translate[i:i+BATCH_SIZE] for i in range(0, len(to_translate), BATCH_SIZE)]
    print(f"Starting parallel batch translation ({len(chunks)} chunks, {len(to_translate)} items) with 6 workers...", flush=True)
    t0 = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(translate_chunk, chunk): chunk for chunk in chunks}
        for f in as_completed(futures):
            f.result()
            completed += 1
            if completed % 15 == 0 or completed == len(chunks):
                elapsed = time.time() - t0
                pct = completed * 100 // len(chunks)
                rate = (completed * BATCH_SIZE) / max(1, elapsed)
                rem_sec = (len(chunks) - completed) * BATCH_SIZE / max(0.1, rate)
                print(f"Progress: {completed}/{len(chunks)} chunks ({pct}%) | Rate: {rate:.1f} it/s | Est. Rem: {rem_sec/60:.1f}m", flush=True)
                if completed % 30 == 0:
                    save_to_disk()

    save_to_disk()
    print(f"Translation finished in {time.time() - t0:.1f}s!", flush=True)

# 4. Synchronize fast cache in memory
_cache.clear()
_cache.update(cache)
_norm_cache.clear()
_norm_cache.update(norm_cache)

print("Starting full site generation for all 101 HTML pages...", flush=True)
t_gen = time.time()

# Generate Foundations
for it in f_catalog:
    p_data = parse_lesson_file(it["raw_file"])
    if not p_data: continue
    p_data["domain_title"] = it["domain_title"]
    p_data["sub_no"] = it.get("sub_no")
    p_data["title_th"] = it.get("title")
    p_data["title_en"] = it.get("title_en")
    html_out = render_lesson_page(p_data, f_catalog, it["idx"], "foundations")
    out_path = os.path.join(FOUNDATIONS_DIR, it["filename"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

# Generate Architect
for it in a_catalog:
    p_data = parse_lesson_file(it["raw_file"])
    if not p_data: continue
    p_data["domain_title"] = it["domain_title"]
    p_data["sub_no"] = it.get("sub_no")
    p_data["title_th"] = it.get("title")
    p_data["title_en"] = it.get("title_en")
    html_out = render_lesson_page(p_data, a_catalog, it["idx"], "architect")
    out_path = os.path.join(ARCHITECT_DIR, it["filename"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

# Generate Indexes
f_index_html = render_course_index_page(f_catalog, "foundations")
with open(os.path.join(FOUNDATIONS_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(f_index_html)

a_index_html = render_course_index_page(a_catalog, "architect")
with open(os.path.join(ARCHITECT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(a_index_html)

master_html = render_master_portal(f_catalog, a_catalog)
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(master_html)

save_to_disk()
print(f"ALL DONE! All 98 lessons + 3 indices successfully generated in {time.time()-t_gen:.2f} seconds!", flush=True)
