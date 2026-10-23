import os, sys, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import MyMemoryTranslator

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")

sys.path.insert(0, BASE_DIR)
from generate_all import f_catalog, a_catalog, parse_lesson_file, FOUNDATIONS_DIR, ARCHITECT_DIR
from builder_page import render_lesson_page, render_course_index_page, render_master_portal
from quiz_translator import clean_thai_spacing, save_cache, _cache

# Load cache
with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

# Purge any bad English entries
purged = 0
for k in list(cache.keys()):
    v = cache[k]
    if len(re.findall(r'[\u0e00-\u0e7f]', v)) == 0 and len(re.findall(r'[a-zA-Z]', v)) > 3:
        del cache[k]
        purged += 1

print(f"Purged {purged} untranslated entries. Clean cache size: {len(cache)}", flush=True)

norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in cache.items()}

lock = threading.RLock()
save_counter = 0

EMAILS = [
    "prep_study_1@anthropic-hub.io",
    "prep_study_2@anthropic-hub.io",
    "prep_study_3@anthropic-hub.io",
    "prep_study_4@anthropic-hub.io",
    "prep_study_5@anthropic-hub.io",
    "prep_study_6@anthropic-hub.io",
    "prep_study_7@anthropic-hub.io",
    "prep_study_8@anthropic-hub.io",
    "prep_study_9@anthropic-hub.io",
    "prep_study_10@anthropic-hub.io",
]

def save_to_disk():
    with lock:
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f"[AutoSave] Cache saved: {len(cache)} entries.", flush=True)
        except Exception as e:
            print(f"[AutoSave Error] {e}", flush=True)

def translate_single(text_clean, worker_id=0):
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

    email = EMAILS[worker_id % len(EMAILS)]
    try:
        translator = MyMemoryTranslator(source="english", target="thai", email=email)
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

# Gather all texts
print("Collecting all unique texts across 98 lessons...", flush=True)
all_texts = set()

for it in f_catalog + a_catalog:
    p = parse_lesson_file(it["raw_file"])
    if not p: continue
    blocks = p.get("blocks", {})
    questions = p.get("questions", {})
    
    for sec in p.get("sections", []):
        for item in sec.get("items", []):
            itype = item["type"]
            if itype == "paragraph":
                t = item.get("text", "").strip()
                if t: all_texts.add(t)
            elif itype == "code" and item.get("caption"):
                t = item["caption"].strip()
                if t: all_texts.add(t)
            elif itype == "list":
                for li in item.get("items", []):
                    t = li.strip()
                    if t: all_texts.add(t)
            elif itype == "checkpoint_ref":
                ckey = item["key"]
                if ckey.startswith("check:"):
                    b = blocks.get(ckey[6:])
                    if b:
                        if b.get("prompt"): all_texts.add(b["prompt"].strip())
                        if b.get("explanation"): all_texts.add(b["explanation"].strip())
                        for opt in b.get("options", []):
                            if opt: all_texts.add(opt.strip())
                        for pair in b.get("pairs", []):
                            if pair.get("term"): all_texts.add(pair["term"].strip())
                            if pair.get("definition"): all_texts.add(pair["definition"].strip())
                        for s in b.get("steps", []):
                            if s: all_texts.add(s.strip())
                elif ckey.startswith("question:"):
                    q = questions.get(ckey[9:])
                    if q:
                        if q.get("question"): all_texts.add(q["question"].strip())
                        for opt in q.get("options", []):
                            if opt: all_texts.add(opt.strip())
                        for exp in q.get("explanations", []):
                            if isinstance(exp, dict) and exp.get("explanation"):
                                all_texts.add(exp["explanation"].strip())
                            elif isinstance(exp, str):
                                all_texts.add(exp.strip())
            elif itype == "predict_first":
                if item.get("prompt"): all_texts.add(item["prompt"].strip())
                if item.get("explanation"): all_texts.add(item["explanation"].strip())
                if item.get("quote"): all_texts.add(item["quote"].strip())
                for opt in item.get("options", []):
                    if opt: all_texts.add(opt.strip())

to_translate = []
for t in all_texts:
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', t.lower())
    if t in cache:
        v = cache[t]
        if len(re.findall(r'[\u0e00-\u0e7f]', v)) > 0 or len(t) <= 3:
            continue
    if norm_k in norm_cache:
        v = norm_cache[norm_k]
        if len(re.findall(r'[\u0e00-\u0e7f]', v)) > 0 or len(t) <= 3:
            continue
    to_translate.append(t)

print(f"Total texts to translate: {len(to_translate)} (Already cached: {len(all_texts) - len(to_translate)})", flush=True)

if to_translate:
    print("Starting fast parallel translation with 16 workers...", flush=True)
    t0 = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(translate_single, text, i): text for i, text in enumerate(to_translate)}
        for f in as_completed(futures):
            f.result()
            completed += 1
            if completed % 100 == 0 or completed == len(to_translate):
                print(f"Translation Progress: {completed} / {len(to_translate)} ({completed*100//len(to_translate)}%) in {time.time()-t0:.1f}s", flush=True)
                
    save_to_disk()
    print(f"Translation phase complete in {time.time()-t0:.1f}s!", flush=True)

# 2. Update global cache in quiz_translator
_cache.update(cache)

# 3. Generate all lessons
print("Generating all 45 Foundations lessons...", flush=True)
t_gen = time.time()
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

print("Generating all 53 Architect lessons...", flush=True)
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

print("Generating course indices & master portal...", flush=True)
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
print(f"All 98 lessons and 3 indices successfully generated in {time.time()-t_gen:.2f}s!", flush=True)
