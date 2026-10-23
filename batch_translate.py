import os, sys, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.parse

# Ensure line-buffered stdout for real-time logging
sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
from generate_all import f_catalog, a_catalog, parse_lesson_file
from quiz_translator import clean_thai_spacing

# Load existing cache
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

def trans_single(text_clean):
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

    for c in ["dict-chrome-ex", "gtx", "webapp"]:
        url = f"https://translate.googleapis.com/translate_a/single?client={c}&sl=en&tl=th&dt=t"
        data = urllib.parse.urlencode({"q": text_clean}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"})
        try:
            with urllib.request.urlopen(req, timeout=6) as res:
                data_json = json.loads(res.read().decode())
                translated = ''.join([part[0] for part in data_json[0] if part[0]])
                cleaned = clean_thai_spacing(translated)
                should_save = False
                with lock:
                    cache[text_clean] = cleaned
                    norm_cache[norm_k] = cleaned
                    save_counter += 1
                    if save_counter % 100 == 0:
                        should_save = True
                if should_save:
                    save_to_disk()
                return cleaned
        except Exception:
            time.sleep(0.2)
            continue
            
    # Fallback
    fallback = clean_thai_spacing(text_clean)
    with lock:
        cache[text_clean] = fallback
        norm_cache[norm_k] = fallback
    return fallback

# Collect all texts to translate
all_texts = set()
for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    for s in p["sections"]:
        for item in s["items"]:
            itype = item["type"]
            if itype == "paragraph":
                t = item["text"].strip()
                if t: all_texts.add(t)
            elif itype == "list":
                for li in item.get("items", []):
                    t = li.strip()
                    if t: all_texts.add(t)
            elif itype == "code" and item.get("caption"):
                t = item["caption"].strip()
                if t: all_texts.add(t)
            elif itype == "table":
                if item.get("caption"):
                    t = item["caption"].strip()
                    if t: all_texts.add(t)
                for th in item.get("headers", []):
                    t = th.strip()
                    if t: all_texts.add(t)
                for row in item.get("rows", []):
                    for cell in row:
                        t = cell.strip()
                        if t: all_texts.add(t)
            elif itype == "figure_text":
                t = item["text"].strip()
                if t: all_texts.add(t)

print(f"Total unique texts collected: {len(all_texts)}", flush=True)
to_translate = []
for t in all_texts:
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t.lower())
    if t not in cache and norm_k not in norm_cache:
        to_translate.append(t)

print(f"Texts requiring translation: {len(to_translate)}", flush=True)

if to_translate:
    print(f"Starting concurrent translation with 10 workers...", flush=True)
    t0 = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(trans_single, text): text for text in to_translate}
        for f in as_completed(futures):
            f.result()
            completed += 1
            if completed % 100 == 0 or completed == len(to_translate):
                print(f"Progress: {completed} / {len(to_translate)} ({completed*100//len(to_translate)}%) in {time.time()-t0:.1f}s", flush=True)
                
    save_to_disk()
    print(f"All {len(to_translate)} texts translated and cached in {time.time()-t0:.1f}s!", flush=True)
else:
    print("All texts are already cached!", flush=True)
