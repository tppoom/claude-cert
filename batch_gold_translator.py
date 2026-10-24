import os, sys, json, re, time, subprocess, threading
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
CACHE_PATH = os.path.join(BASE_DIR, "raw_data", "quiz_thai_cache.json")
TRANS_DIR = os.path.join(BASE_DIR, "high_quality_translations")

os.makedirs(os.path.join(TRANS_DIR, "foundations"), exist_ok=True)
os.makedirs(os.path.join(TRANS_DIR, "architect"), exist_ok=True)

sys.path.insert(0, BASE_DIR)
from generate_all import f_catalog, a_catalog, parse_lesson_file

# Thread-safe cache lock
cache_lock = threading.Lock()

# Load current cache
with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

def run_agy_json(prompt, timeout=60, retries=2):
    """Executes agy prompt and parses JSON output safely."""
    for attempt in range(1, retries + 1):
        try:
            res = subprocess.run(
                ["agy", "--new-project", "--disable-slash-commands", "--model", "gemini-3.8-flash-low", "-p", prompt],
                capture_output=True, text=True, timeout=timeout
            )
            out = res.stdout.strip()
            
            # Extract JSON from markdown code block if present
            m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', out)
            json_str = m.group(1).strip() if m else out
            
            # Remove any trailing junk before or after JSON
            json_str = re.sub(r'^[^{\[]*', '', json_str)
            json_str = re.sub(r'[^}\]]*$', '', json_str)
            
            data = json.loads(json_str)
            return data
        except Exception as e:
            time.sleep(2)
    return None

def translate_metadata(title, objectives, key_concept):
    payload = {
        "title": title,
        "objectives": objectives,
        "key_concept": key_concept
    }
    prompt = f"""คุณคือนักพัฒนา AI ของ Anthropic ที่กำลังแปลและเรียบเรียงหัวข้อและเป้าหมายของบทเรียน Claude Certification ให้เป็นภาษาไทยที่กระชับ สละสลวย เหมาะสำหรับ Developer
กฎสำคัญ:
1. แปลกระชับ ได้ใจความ ตรงประเด็น ตัดคำฟุ่มเฟือย
2. คงศัพท์เทคนิคเป็นภาษาอังกฤษเสมอ (เช่น Workflows, Agents, Control Flow, Subagents, Orchestrator, LLM, Context Window, Prompts ฯลฯ)
3. ส่งผลลัพธ์เป็น JSON Object โครงสร้างเดิมเท่านั้น

Input JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output JSON:"""
    res = run_agy_json(prompt, timeout=40)
    return res if res else payload

def translate_sections_chunk(sections_chunk):
    payload = []
    for s in sections_chunk:
        sec_obj = {
            "heading": s.get("heading", ""),
            "items": []
        }
        for it in s.get("items", []):
            itype = it.get("type")
            if itype in ["paragraph", "exam_trap"]:
                sec_obj["items"].append({
                    "type": itype,
                    "text": it.get("text", "")
                })
            elif itype == "table":
                sec_obj["items"].append({
                    "type": "table",
                    "caption": it.get("caption", ""),
                    "headers": it.get("headers", []),
                    "rows": it.get("rows", [])
                })
        payload.append(sec_obj)

    prompt = f"""คุณคือนักพัฒนา AI ของ Anthropic ที่กำลังแปลและเรียบเรียงเนื้อหาบทเรียน Claude Certification ให้เป็นภาษาไทยที่กระชับ สละสลวย ตรงประเด็น เหมาะสำหรับ Developer
กฎสำคัญ:
1. แปลกระชับ ได้ใจความ ไม่เวิ่นเว้อ ตัดคำแปลกๆ ออก ใช้ภาษา Developer ที่เป็นธรรมชาติ
2. คงศัพท์เทคนิคเป็นภาษาอังกฤษเสมอ (เช่น Workflows, Agents, Control Flow, Orchestrator, Subagents, Autonomy Ladder, LLM, Loop, Prompt, Context, Skills, Slash Commands, Sessions, Headless, Auto Mode, Settings, Rules, JSON, API, Hooks, Compaction, Memory, Worktree ฯลฯ) ห้ามแปลเป็นคำประหลาด
3. กับดักข้อสอบ (EXAM TRAP): แปลและสรุปในรูปแบบ:
   "คำถามหลอก / สิ่งที่มักเข้าใจผิด? (ทำไมถึงผิด): ไม่จริง: ... (อธิบายเหตุผลทางเทคนิคที่ถูกต้องและกระชับ)"
4. ตาราง (Table): แปลเฉพาะคำอธิบาย คงชื่อฟังก์ชัน คลาส ตัวแปร หรือคำสั่งเป็นภาษาอังกฤษ
5. ส่งผลลัพธ์เป็น JSON Array โครงสร้างเดิมเท่านั้น

Input JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output JSON:"""
    res = run_agy_json(prompt, timeout=60)
    return res if res else payload

def translate_questions(questions_dict):
    if not questions_dict:
        return []
    payload = []
    for qid, q in questions_dict.items():
        payload.append({
            "id": qid,
            "question": q.get("question", ""),
            "options": q.get("options", []),
            "explanation": q.get("explanation", "")
        })

    prompt = f"""คุณคือนักพัฒนา AI ของ Anthropic ที่กำลังแปลโจทย์ข้อสอบ Claude Certification เป็นภาษาไทยสำหรับ Developer
กฎสำคัญ:
1. แปลโจทย์และตัวเลือกให้อ่านเข้าใจง่าย กระชับ ชัดเจน
2. คงชื่อฟังก์ชัน, ตัวแปร, และศัพท์เทคนิคเป็นภาษาอังกฤษเสมอ (Workflows, Agents, Control Flow, LLM, Prompt Chaining, Routing, Orchestrator-workers ฯลฯ)
3. ส่งผลลัพธ์เป็น JSON Array โครงสร้างเดิมเท่านั้น

Input JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output JSON:"""
    res = run_agy_json(prompt, timeout=50)
    return res if res else payload

def update_cache_from_lesson(raw_data, trans_data):
    """Thread-safe updates the global cache dictionary and persists to disk."""
    if not trans_data:
        return

    with cache_lock:
        # 1. Title
        if raw_data.get("title") and trans_data.get("title"):
            cache[raw_data["title"]] = trans_data["title"]

        # 2. Objectives
        raw_objs = raw_data.get("objectives", [])
        trans_objs = trans_data.get("objectives", [])
        for i in range(min(len(raw_objs), len(trans_objs))):
            cache[raw_objs[i]] = trans_objs[i]

        # 3. Key concept
        if raw_data.get("key_concept") and trans_data.get("key_concept"):
            cache[raw_data["key_concept"]] = trans_data["key_concept"]

        # 4. Sections
        raw_secs = raw_data.get("sections", [])
        trans_secs = trans_data.get("sections", [])
        for s_idx in range(min(len(raw_secs), len(trans_secs))):
            rs = raw_secs[s_idx]
            ts = trans_secs[s_idx]

            r_head = rs.get("heading", "")
            t_head = ts.get("heading", "")
            if r_head and t_head:
                cache[r_head] = t_head
                core_r = re.sub(r"^\d+\.\s*", "", r_head).strip()
                core_t = re.sub(r"^\d+\.\s*", "", t_head).strip()
                cache[core_r] = core_t

            r_items = [it for it in rs.get("items", []) if it["type"] in ["paragraph", "exam_trap", "table"]]
            t_items = ts.get("items", [])
            for i_idx in range(min(len(r_items), len(t_items))):
                ri = r_items[i_idx]
                ti = t_items[i_idx]
                if ri["type"] in ["paragraph", "exam_trap"]:
                    cache[ri["text"]] = ti.get("text", ri["text"])
                elif ri["type"] == "table":
                    if ri.get("caption") and ti.get("caption"):
                        cache[ri["caption"]] = ti["caption"]
                    r_h = ri.get("headers", [])
                    t_h = ti.get("headers", [])
                    for h_i in range(min(len(r_h), len(t_h))):
                        cache[r_h[h_i]] = t_h[h_i]
                    r_rows = ri.get("rows", [])
                    t_rows = ti.get("rows", [])
                    for row_i in range(min(len(r_rows), len(t_rows))):
                        rr = r_rows[row_i]
                        tr = t_rows[row_i]
                        for cell_i in range(min(len(rr), len(tr))):
                            cache[rr[cell_i]] = tr[cell_i]

        # 5. Questions
        raw_qs = list(raw_data.get("questions", {}).values())
        trans_qs = trans_data.get("questions", [])
        for q_idx in range(min(len(raw_qs), len(trans_qs))):
            rq = raw_qs[q_idx]
            tq = trans_qs[q_idx]
            if rq.get("question") and tq.get("question"):
                cache[rq["question"]] = tq["question"]
            r_opts = rq.get("options", [])
            t_opts = tq.get("options", [])
            for opt_i in range(min(len(r_opts), len(t_opts))):
                cache[r_opts[opt_i]] = t_opts[opt_i]

        # Persist checkpoint to disk
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as fp:
                json.dump(cache, fp, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}", flush=True)

def process_single_lesson(item, course_type):
    fn = item["filename"]
    save_path = os.path.join(TRANS_DIR, course_type, fn.replace(".html", ".json"))

    raw_data = parse_lesson_file(item["raw_file"])
    if not raw_data:
        print(f"[{course_type} {fn}] Parse error, skipping.", flush=True)
        return

    # If already translated, load and update cache
    if os.path.exists(save_path):
        try:
            with open(save_path, "r", encoding="utf-8") as fp:
                trans_data = json.load(fp)
            update_cache_from_lesson(raw_data, trans_data)
            print(f"[{course_type} {fn}] Loaded from high_quality_translations.", flush=True)
            return
        except Exception:
            pass

    t0 = time.time()
    print(f"[{course_type} {fn}] Translating (parallel chunks)...", flush=True)

    raw_sections = raw_data.get("sections", [])
    section_chunks = [raw_sections[i:i+2] for i in range(0, len(raw_sections), 2)]

    # Run intra-lesson chunks in parallel for maximum throughput
    with ThreadPoolExecutor(max_workers=5) as ex:
        f_meta = ex.submit(
            translate_metadata,
            raw_data.get("title", ""),
            raw_data.get("objectives", []),
            raw_data.get("key_concept", "")
        )
        f_chunks = [ex.submit(translate_sections_chunk, ch) for ch in section_chunks]
        f_q = ex.submit(translate_questions, raw_data.get("questions", {}))

        meta = f_meta.result()
        trans_sections = []
        for f in f_chunks:
            res = f.result()
            if isinstance(res, list):
                trans_sections.extend(res)
            else:
                trans_sections.extend(raw_sections)
        trans_questions = f_q.result()

    full_trans = {
        "title": meta.get("title", raw_data.get("title", "")),
        "objectives": meta.get("objectives", raw_data.get("objectives", [])),
        "key_concept": meta.get("key_concept", raw_data.get("key_concept", "")),
        "sections": trans_sections,
        "questions": trans_questions
    }

    # Save to high_quality_translations
    with open(save_path, "w", encoding="utf-8") as fp:
        json.dump(full_trans, fp, ensure_ascii=False, indent=2)

    # Update cache & persist
    update_cache_from_lesson(raw_data, full_trans)

    elapsed = time.time() - t0
    print(f"[{course_type} {fn}] Done in {elapsed:.1f}s!", flush=True)

def run_all(lesson_workers=2):
    print(f"=== STARTING PARALLEL TRANSLATION (Lesson Workers: {lesson_workers}) ===", flush=True)
    t_start = time.time()

    print(">>> Foundations (45 lessons) <<<", flush=True)
    with ThreadPoolExecutor(max_workers=lesson_workers) as ex:
        futures = [ex.submit(process_single_lesson, it, "foundations") for it in f_catalog]
        for f in futures:
            try:
                f.result()
            except Exception as e:
                print(f"Worker exception: {e}", flush=True)

    print(">>> Architect (53 lessons) <<<", flush=True)
    with ThreadPoolExecutor(max_workers=lesson_workers) as ex:
        futures = [ex.submit(process_single_lesson, it, "architect") for it in a_catalog]
        for f in futures:
            try:
                f.result()
            except Exception as e:
                print(f"Worker exception: {e}", flush=True)

    total_time = time.time() - t_start
    print(f"=== ALL 98 LESSONS FINISHED IN {total_time:.1f}s ===", flush=True)

if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    run_all(workers)
