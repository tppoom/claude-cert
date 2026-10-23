import os, sys, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import MyMemoryTranslator
import urllib.request, urllib.parse

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
from generate_all import f_catalog, a_catalog, parse_lesson_file
from quiz_translator import clean_thai_spacing

with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

# Purge any remaining entries with 0 Thai characters
purged = 0
for k in list(cache.keys()):
    v = cache[k]
    if len(re.findall(r'[\u0e00-\u0e7f]', v)) == 0 and len(re.findall(r'[a-zA-Z]', v)) > 3:
        del cache[k]
        purged += 1

print(f"Purged {purged} bad English entries. Valid cache size: {len(cache)}", flush=True)

norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items() if k}

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

def translate_item(text_clean):
    global save_counter
    if not text_clean:
        return ""
    
    with lock:
        if text_clean in cache:
            return cache[text_clean]
        norm_k = re.sub(r'[^a-zA-Z0-9]+', '', text_clean.lower())
        if norm_k in norm_cache:
            return norm_cache[norm_k]
    
    # If text is already predominantly Thai
    thai_chars = len(re.findall(r'[\u0e00-\u0e7f]', text_clean))
    if thai_chars > len(text_clean) * 0.4:
        res = clean_thai_spacing(text_clean)
        with lock:
            cache[text_clean] = res
            norm_cache[norm_k] = res
        return res

    # 1. Try Google Translate endpoints
    for c in ["dict-chrome-ex", "gtx", "webapp"]:
        url = f"https://translate.googleapis.com/translate_a/single?client={c}&sl=en&tl=th&dt=t"
        data = urllib.parse.urlencode({"q": text_clean}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        try:
            with urllib.request.urlopen(req, timeout=3) as res:
                data_json = json.loads(res.read().decode())
                translated = ''.join([part[0] for part in data_json[0] if part[0]])
                if len(re.findall(r'[\u0e00-\u0e7f]', translated)) > 0:
                    cleaned = clean_thai_spacing(translated)
                    should_save = False
                    with lock:
                        cache[text_clean] = cleaned
                        norm_cache[norm_k] = cleaned
                        save_counter += 1
                        if save_counter % 50 == 0:
                            should_save = True
                    if should_save:
                        save_to_disk()
                    return cleaned
        except Exception:
            continue

    # 2. Try MyMemoryTranslator
    try:
        translator = MyMemoryTranslator(source="english", target="thai")
        translated = translator.translate(text_clean)
        if translated and len(re.findall(r'[\u0e00-\u0e7f]', translated)) > 0:
            cleaned = clean_thai_spacing(translated)
            should_save = False
            with lock:
                cache[text_clean] = cleaned
                norm_cache[norm_k] = cleaned
                save_counter += 1
                if save_counter % 50 == 0:
                    should_save = True
            if should_save:
                save_to_disk()
            return cleaned
    except Exception:
        pass

    # Do not cache failed translation
    return clean_thai_spacing(text_clean)

# Gather all texts priority: 1. Quizzes & checkpoints first, then sections & paragraphs
quiz_texts = []
other_texts = []

for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    
    # Check blocks
    for bid, b in p.get("blocks", {}).items():
        if b.get("prompt"): quiz_texts.append(b["prompt"].strip())
        if b.get("explanation"): quiz_texts.append(b["explanation"].strip())
        for opt in b.get("options", []):
            if opt: quiz_texts.append(opt.strip())
        for pair in b.get("pairs", []):
            if pair.get("term"): quiz_texts.append(pair["term"].strip())
            if pair.get("definition"): quiz_texts.append(pair["definition"].strip())
        for s in b.get("steps", []):
            if s: quiz_texts.append(s.strip())
            
    # Check questions
    for qid, q in p.get("questions", {}).items():
        if q.get("question"): quiz_texts.append(q["question"].strip())
        for opt in q.get("options", []):
            if opt: quiz_texts.append(opt.strip())
        for exp in q.get("explanations", []):
            if isinstance(exp, dict) and exp.get("explanation"):
                quiz_texts.append(exp["explanation"].strip())
            elif isinstance(exp, str):
                quiz_texts.append(exp.strip())
            
    # Check predict_first & exam traps
    for sec in p.get("sections", []):
        for item in sec.get("items", []):
            if item["type"] == "predict_first":
                if item.get("prompt"): quiz_texts.append(item["prompt"].strip())
                if item.get("explanation"): quiz_texts.append(item["explanation"].strip())
                if item.get("quote"): quiz_texts.append(item["quote"].strip())
                for opt in item.get("options", []):
                    if opt: quiz_texts.append(opt.strip())
            elif item["type"] == "exam_trap":
                if item.get("text"): quiz_texts.append(item["text"].strip())
            elif item["type"] == "code" and item.get("caption"):
                other_texts.append(item["caption"].strip())
            elif item["type"] == "paragraph":
                other_texts.append(item["text"].strip())
            elif item["type"] == "list":
                for li in item.get("items", []):
                    if li: other_texts.append(li.strip())
            elif item["type"] == "table":
                if item.get("caption"): other_texts.append(item["caption"].strip())
                for th in item.get("headers", []):
                    if th: other_texts.append(th.strip())
                for row in item.get("rows", []):
                    for c in row:
                        if c: other_texts.append(c.strip())

# Filter unique & untranslated
def get_untranslated(items):
    seen = set()
    res = []
    for t in items:
        if not t or t in seen: continue
        seen.add(t)
        norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t.lower())
        if t in cache:
            val = cache[t]
            if len(re.findall(r'[\u0e00-\u0e7f]', val)) > 0 or len(t) <= 3:
                continue
        if norm_k in norm_cache:
            val = norm_cache[norm_k]
            if len(re.findall(r'[\u0e00-\u0e7f]', val)) > 0 or len(t) <= 3:
                continue
        res.append(t)
    return res

untranslated_quizzes = get_untranslated(quiz_texts)
untranslated_others = get_untranslated(other_texts)

print(f"Quizzes/Checkpoints requiring translation: {len(untranslated_quizzes)}", flush=True)
print(f"Other lesson elements requiring translation: {len(untranslated_others)}", flush=True)

all_to_translate = untranslated_quizzes + untranslated_others
print(f"Total to translate: {len(all_to_translate)}", flush=True)

if all_to_translate:
    print("Translating with 6 concurrent workers...", flush=True)
    t0 = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(translate_item, text): text for text in all_to_translate}
        for f in as_completed(futures):
            f.result()
            completed += 1
            if completed % 50 == 0 or completed == len(all_to_translate):
                print(f"Progress: {completed} / {len(all_to_translate)} ({completed*100//len(all_to_translate)}%) in {time.time()-t0:.1f}s", flush=True)
                
    save_to_disk()
    print(f"Translation completed in {time.time()-t0:.1f}s!", flush=True)
else:
    print("Everything is already translated!", flush=True)
