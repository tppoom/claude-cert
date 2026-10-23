import os, sys, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["URLLIB3_FUTURE_DISABLE_HTTP2"] = "1"
os.environ["URLLIB3_DISABLE_HTTP2"] = "1"
os.environ["NIQUESTS_DISABLE_HTTP2"] = "1"

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
import translators as ts
from generate_all import f_catalog, a_catalog, parse_lesson_file
from quiz_translator import clean_thai_spacing

# 1. Load Cache
with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items() if k}
print(f"Loaded existing cache: {len(cache)} entries.", flush=True)

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
    
    # Check if already mostly Thai
    thai_chars = len(re.findall(r'[\u0e00-\u0e7f]', t_clean))
    if thai_chars > len(t_clean) * 0.4:
        return
        
    # Check if in cache
    if t_clean in cache: return
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t_clean.lower())
    if norm_k in norm_cache: return
    
    needed_texts.append(t_clean)

for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    blocks = p.get("blocks", {})
    questions = p.get("questions", {})
    
    for obj in p.get("objectives", []): add_needed(obj)
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
                for h in item.get("headers", []): add_needed(h)
                for row in item.get("rows", []):
                    for cell in row: add_needed(cell)
            elif itype == "checkpoint_ref":
                ckey = item["key"]
                if ckey.startswith("check:"):
                    b = blocks.get(ckey[6:])
                    if b:
                        add_needed(b.get("prompt"))
                        add_needed(b.get("explanation"))
                        if b.get("citation", {}).get("quote"):
                            add_needed(b["citation"]["quote"])
                        for opt in b.get("options", []): add_needed(opt)
                        for pair in b.get("pairs", []):
                            add_needed(pair.get("term"))
                            add_needed(pair.get("definition"))
                        for s in b.get("steps", []): add_needed(s)
                elif ckey.startswith("question:"):
                    q = questions.get(ckey[9:])
                    if q:
                        add_needed(q.get("question"))
                        for opt in q.get("options", []): add_needed(opt)
                        for exp in q.get("explanations", []):
                            if isinstance(exp, dict): add_needed(exp.get("explanation"))
                            elif isinstance(exp, str): add_needed(exp)
            elif itype == "predict_first":
                add_needed(item.get("prompt"))
                add_needed(item.get("explanation"))
                add_needed(item.get("quote"))
                for opt in item.get("options", []): add_needed(opt)

print(f"Total missing strings to translate: {len(needed_texts)}", flush=True)

# 3. Translation engine
DELIM = "\n__ITEM__\n"
BATCH_SIZE = 5

def translate_single(it):
    global save_counter
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', it.lower())
    for engine in ["bing", "caiyun"]:
        try:
            res = ts.translate_text(it, translator=engine, to_language="th")
            if res and not re.match(r'^[a-z0-9]{15,}$', res.strip()):
                cleaned = clean_thai_spacing(res)
                with lock:
                    cache[it] = cleaned
                    norm_cache[norm_k] = cleaned
                    save_counter += 1
                return
        except Exception:
            pass

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
        
    try:
        payload = DELIM.join(unseen)
        res = ts.translate_text(payload, translator="bing", to_language="th")
        parts = [clean_thai_spacing(p.strip()) for p in res.split("__ITEM__")]
        if len(parts) == len(unseen):
            with lock:
                for orig, th in zip(unseen, parts):
                    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', orig.lower())
                    cache[orig] = th
                    norm_cache[norm_k] = th
                    save_counter += 1
            return
    except Exception:
        pass
        
    # Fallback to single if batch fails
    for it in unseen:
        translate_single(it)

if needed_texts:
    chunks = [needed_texts[i:i+BATCH_SIZE] for i in range(0, len(needed_texts), BATCH_SIZE)]
    print(f"Translating {len(needed_texts)} items across {len(chunks)} batches using 6 workers...", flush=True)
    t0 = time.time()
    done_chunks = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
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
                if done_chunks % 50 == 0:
                    save_to_disk()

    save_to_disk()
    print(f"Batch translation completed in {time.time() - t0:.1f}s! Total cache: {len(cache)}", flush=True)
