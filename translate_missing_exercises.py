import os, sys, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.parse

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
from generate_all import f_catalog, a_catalog, parse_lesson_file
from quiz_translator import clean_thai_spacing

with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items() if k}
print(f"Loaded {len(cache)} existing cached translations.", flush=True)

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

def has_trans(text):
    if not text:
        return True
    t = text.strip()
    if t in cache:
        val = cache[t]
        # Ensure the cached value is actually Thai, not just untranslated English
        if len(re.findall(r'[\u0e00-\u0e7f]', val)) > 0:
            return True
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t.lower())
    if norm_k in norm_cache:
        val = norm_cache[norm_k]
        if len(re.findall(r'[\u0e00-\u0e7f]', val)) > 0:
            return True
    if len(re.findall(r'[\u0e00-\u0e7f]', t)) > len(t) * 0.4:
        return True
    return False

def translate_str(text_clean):
    global save_counter
    if not text_clean or len(text_clean.strip()) == 0:
        return ""
    
    t_clean = text_clean.strip()
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t_clean.lower())
    
    # If text is code or file path or single symbol, check if translation needed
    if re.match(r'^(/|\./|\.claude/|--|"matcher":|```)', t_clean):
        # Pure CLI flag or path or JSON schema key, just keep
        with lock:
            cache[t_clean] = t_clean
            norm_cache[norm_k] = t_clean
        return t_clean
    
    clients = ["gtx", "dict-chrome-ex", "webapp"]
    for c in clients:
        url = f"https://translate.googleapis.com/translate_a/single?client={c}&sl=en&tl=th&dt=t"
        data = urllib.parse.urlencode({"q": t_clean}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        try:
            with urllib.request.urlopen(req, timeout=8) as res:
                data_json = json.loads(res.read().decode())
                translated = ''.join([part[0] for part in data_json[0] if part[0]])
                cleaned = clean_thai_spacing(translated)
                should_save = False
                with lock:
                    cache[t_clean] = cleaned
                    norm_cache[norm_k] = cleaned
                    save_counter += 1
                    if save_counter % 100 == 0:
                        should_save = True
                if should_save:
                    save_to_disk()
                return cleaned
        except Exception:
            time.sleep(0.3)
            continue
            
    # Fallback
    fallback = clean_thai_spacing(t_clean)
    with lock:
        cache[t_clean] = fallback
        norm_cache[norm_k] = fallback
    return fallback

missing_set = set()

for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    
    # Blocks (Checkpoints: match, order, choice, fill)
    blocks = p.get("blocks", {})
    for bid, b in blocks.items():
        for k in ["prompt", "explanation"]:
            v = b.get(k)
            if v and not has_trans(v): missing_set.add(v)
        for opt in b.get("options", []):
            if opt and not has_trans(opt): missing_set.add(opt)
        for s in b.get("steps", []):
            if s and not has_trans(s): missing_set.add(s)
        for pr in b.get("pairs", []):
            t = pr.get("term")
            d = pr.get("definition")
            if t and not has_trans(t): missing_set.add(t)
            if d and not has_trans(d): missing_set.add(d)
        cit = b.get("citation", {})
        if cit and cit.get("quote"):
            q_str = cit.get("quote")
            if q_str and not has_trans(q_str): missing_set.add(q_str)
            
    # Questions (Official Exam Questions)
    questions = p.get("questions", {})
    for qid, q in questions.items():
        v = q.get("question")
        if v and not has_trans(v): missing_set.add(v)
        for opt in q.get("options", []):
            if opt and not has_trans(opt): missing_set.add(opt)
        for exp in q.get("explanations", []):
            e = exp.get("explanation")
            if e and not has_trans(e): missing_set.add(e)
            
    # Sections (predict_first, exam_trap)
    for sec in p.get("sections", []):
        for item in sec.get("items", []):
            itype = item.get("type")
            if itype == "predict_first":
                v = item.get("prompt")
                if v and not has_trans(v): missing_set.add(v)
                for opt in item.get("options", []):
                    if opt and not has_trans(opt): missing_set.add(opt)
                v = item.get("explanation")
                if v and not has_trans(v): missing_set.add(v)
                q_str = item.get("quote")
                if q_str and not has_trans(q_str): missing_set.add(q_str)
            elif itype == "exam_trap":
                v = item.get("text")
                if v and not has_trans(v): missing_set.add(v)

print(f"Total missing strings to translate: {len(missing_set)}", flush=True)

if missing_set:
    print("Starting concurrent translation with 25 workers...", flush=True)
    done_count = 0
    total = len(missing_set)
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(translate_str, text): text for text in missing_set}
        for f in as_completed(futures):
            done_count += 1
            if done_count % 50 == 0 or done_count == total:
                elapsed = time.time() - t0
                print(f"Progress: {done_count}/{total} ({done_count/total*100:.1f}%) in {elapsed:.1f}s", flush=True)
                
    save_to_disk()
    print("Translation complete and cache saved successfully!", flush=True)
else:
    print("No missing strings! All exercises have Thai translations.", flush=True)
