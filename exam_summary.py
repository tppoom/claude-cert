import os, sys, json, re, html
from section_translator import get_thai_heading
from domain_knowledge import get_thai_objective, get_thai_key_concept
from quiz_translator import get_thai_explanation, clean_thai_spacing
from rich_formatter import highlight_tech_terms, split_thai_sentences

KEY_ARCH_TERMS = [
    "workflow", "agent", "subagent", "orchestrator", "prompt", "token", 
    "context", "tool", "hook", "api", "model", "cache", "batch",
    "control flow", "autonomy ladder", "latency", "cost", "session",
    "system prompt", "parallel", "specialization", "isolation",
    "claude code", "sampling", "streaming", "temperature", "top_p",
    "schema", "json", "guardrail", "jailbreak", "injection", "mcp",
    "retrieval", "rag", "embedding", "chunking", "evaluation", "telemetry",
    "hitl", "human-in-the-loop", "compaction", "pinning", "haiku", "sonnet", "opus"
]

def score_sentence(s):
    s_lower = s.lower()
    score = 0
    if 40 <= len(s) <= 240:
        score += 3
    elif len(s) > 240:
        score += 1
    else:
        score -= 2
        
    if re.search(r'^(?:จึง|และ|แต่|หรือ|ว่า|คือ|มี|เป็น|ทั้งนี้|ดังนั้น|โดยที่|ที่)\b', s):
        score -= 5
    if re.search(r'^(?:ดูเนื้อหา|ดังต่อไปนี้|รูปภาพ|ตาราง|นี่คือลำดับ|ขั้นตอนคือ|ด้านล่างนี้|ต่อไปนี้)', s):
        score -= 8
        
    for k in KEY_ARCH_TERMS:
        if k in s_lower:
            score += 2
            
    if ":" in s or "หมายถึง" in s or "คือ" in s or "กำหนด" in s or "เปรียบเทียบ" in s:
        score += 2
        
    return score

def parse_trap_text(text):
    if not text:
        return "", ""
    text = clean_thai_spacing(text)
    # Strip any leading trap labels
    prefix_pat = r"^(?:(?:จุดที่ข้อสอบชอบหลอก|กับดักการสอบ|หลุมพรางการสอบ|หลุมพรางการทดสอบ|Exam\s*Trap)[\s:\(\)]*)*"
    body = re.sub(prefix_pat, "", text, flags=re.I).strip()
    
    # Split on (ทำไมถึงผิด / Why it's wrong)
    split_pat = r"\((?:ทำไมถึงผิด(?:พลาด)?|ทําไมถึงผิด(?:พลาด)?|Why\s*it[\x27\x22\x27]s\s*wrong|Why\s*wrong)\):?\s*"
    parts = re.split(split_pat, body, maxsplit=1, flags=re.I)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return body, ""

def extract_section_key_takeaways(sec):
    pts = []
    
    # 1. Inspect Paragraphs
    paras = [it for it in sec.get("items", []) if it.get("type") == "paragraph"]
    candidates = []
    for it in paras:
        p_raw = it.get("text", "")
        p_th = get_thai_explanation(p_raw)
        sents = split_thai_sentences(p_th)
        for s in sents:
            s_clean = s.strip()
            # Clean leading colons, numbers, dashes
            s_clean = re.sub(r'^[:–—\s\.\d\)]+', '', s_clean).strip()
            s_clean = re.sub(r'^(?:ดังนั้น|ทั้งนี้|อย่างไรก็ตาม|ในทางกลับกัน|ในขณะเดียวกัน|นอกจากนี้)\s*', '', s_clean).strip()
            sc = score_sentence(s_clean)
            if sc > 0:
                candidates.append((sc, s_clean))
                
    # Sort candidates by score descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    for sc, s in candidates:
        if s not in pts and len(pts) < 3:
            pts.append(s)
            
    # 2. Inspect Tables
    tables = [it for it in sec.get("items", []) if it.get("type") == "table"]
    for t in tables:
        cap = clean_thai_spacing(t.get("caption", ""))
        if cap and len(pts) < 4:
            cap_th = get_thai_explanation(cap)
            if cap_th and cap_th.lower() != cap.lower():
                pts.append(f"ตารางเปรียบเทียบสำคัญ: {cap} ({cap_th})")
            else:
                pts.append(f"ตารางเปรียบเทียบสำคัญ: {cap}")
                
    # 3. Inspect Code Schemas
    codes = [it for it in sec.get("items", []) if it.get("type") == "code"]
    for c in codes:
        cap = clean_thai_spacing(c.get("caption", ""))
        if cap and len(pts) < 4:
            cap_th = get_thai_explanation(cap)
            pts.append(f"สถาปัตยกรรมโค้ด/สคีมา: {cap_th or cap}")
            
    return pts[:3]

def render_exam_summary_section(lesson_data, catalog, current_idx, course_type):
    p = lesson_data
    sub_no = p.get("sub_no", "")
    domain_no = p.get("domain_no", "")
    sections = p.get("sections", [])
    
    # --- 1. Golden Rule Card ---
    kc_raw = p.get("key_concept", "")
    golden_rule_html = ""
    if kc_raw:
        kc_thai = clean_thai_spacing(get_thai_key_concept(kc_raw))
        golden_rule_html = f"""
        <div class="p-5 rounded-2xl border-l-4 border-l-amber-500 border-y border-r border-amber-500/30 bg-gradient-to-r from-amber-950/40 to-slate-900/90 space-y-2 shadow-md">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
            <span class="text-base">💡</span>
            <span>กฎเหล็กทางสถาปัตยกรรมประจำบทเรียน (Key Architectural Law)</span>
          </div>
          <p class="text-sm sm:text-[15px] text-slate-100 font-medium leading-relaxed">
            {highlight_tech_terms(kc_thai)}
          </p>
        </div>
        """

    # --- 2. Topic-by-Topic Cards ---
    sec_cards = ""
    for idx, sec in enumerate(sections):
        h_en = sec.get("heading", "")
        h_th = clean_thai_spacing(get_thai_heading(h_en))
        clean_id = re.sub(r"[^a-zA-Z0-9]+", "-", h_en).lower().strip("-")
        
        pts = extract_section_key_takeaways(sec)
        if not pts:
            pts = ["ครอบคลุมแนวคิดทางสถาปัตยกรรมหลักและการเชื่อมต่อระบบตามมาตรฐาน Anthropic Claude"]
            
        point_lis = "".join(
            f'<li class="flex items-start gap-2.5 text-xs sm:text-[13px] text-slate-300 leading-relaxed">'
            f'<span class="text-indigo-400 font-bold shrink-0 mt-0.5">•</span>'
            f'<div class="grow">{highlight_tech_terms(pt)}</div>'
            f'</li>'
            for pt in pts
        )
        
        sec_cards += f"""
        <div class="p-4 sm:p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/40 transition-colors shadow-sm flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-start justify-between gap-2 pb-2.5 border-b border-slate-800/80">
              <h3 class="text-xs sm:text-sm font-bold text-white leading-snug">
                <span class="text-indigo-400 font-mono mr-1">#{idx+1}</span>
                <span>{h_th}</span>
              </h3>
              <a href="#{clean_id}" class="text-[11px] text-slate-400 hover:text-indigo-300 shrink-0 font-medium transition-colors ml-2">
                อ่านเนื้อหา ↗
              </a>
            </div>
            <ul class="space-y-2 pt-2">
              {point_lis}
            </ul>
          </div>
        </div>
        """

    # --- 3. Exam Traps & Pitfalls Comparison ---
    traps = []
    for sec in sections:
        for it in sec.get("items", []):
            if it.get("type") == "exam_trap":
                t_raw = it.get("text", "")
                t_th = get_thai_explanation(t_raw)
                mis_en, real_en = parse_trap_text(t_raw)
                mis_th, real_th = parse_trap_text(t_th)
                traps.append({
                    "mis_en": mis_en or t_raw,
                    "real_en": real_en,
                    "mis_th": mis_th or t_th,
                    "real_th": real_th
                })
                
    traps_card_html = ""
    if traps:
        trap_items_html = ""
        for idx, t in enumerate(traps):
            en_sub_mis = f'<div class="text-[11px] text-slate-400 font-mono mt-0.5">{html.escape(t["mis_en"])}</div>' if t["mis_en"] and t["mis_en"] != t["mis_th"] else ""
            en_sub_real = f'<div class="text-[11px] text-slate-400 font-mono mt-0.5">{html.escape(t["real_en"])}</div>' if t["real_en"] and t["real_en"] != t["real_th"] else ""
            
            trap_items_html += f"""
            <div class="p-4 rounded-xl border border-amber-500/30 bg-slate-950/60 space-y-3 shadow-xs">
              <div class="flex items-start gap-2.5">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-rose-500/20 text-rose-400 font-bold text-xs shrink-0 mt-0.5 shadow-xs">❌</span>
                <div class="text-xs sm:text-sm text-slate-200 leading-relaxed grow">
                  <strong class="text-rose-300 font-semibold block mb-0.5">สิ่งที่ข้อสอบมักหลอก (Common Trap / Misconception):</strong>
                  <div class="font-medium text-slate-100">{highlight_tech_terms(t["mis_th"])}</div>
                  {en_sub_mis}
                </div>
              </div>
              <div class="flex items-start gap-2.5 pt-2.5 border-t border-slate-800/80">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-emerald-500/20 text-emerald-400 font-bold text-xs shrink-0 mt-0.5 shadow-xs">✅</span>
                <div class="text-xs sm:text-sm text-slate-200 leading-relaxed grow font-sans">
                  <strong class="text-emerald-300 font-semibold block mb-0.5">ความเป็นจริงทางเทคนิค (Anthropic Reality / Deep Insight):</strong>
                  <div class="font-normal text-slate-200">{highlight_tech_terms(t["real_th"] or t["real_en"])}</div>
                  {en_sub_real}
                </div>
              </div>
            </div>
            """
            
        traps_card_html = f"""
        <div class="space-y-3 pt-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <span class="text-base">⚠️</span>
              <span>รวมจุดที่ข้อสอบชอบหลอก & สิ่งที่มักเข้าใจผิด ({len(traps)} ข้อควรระวัง)</span>
            </div>
            <span class="text-[11px] text-slate-400 font-mono">Exam Traps Checklist</span>
          </div>
          <div class="space-y-3">
            {trap_items_html}
          </div>
        </div>
        """

    # --- 4. Exam Objectives & Skills Tested ---
    objectives = p.get("objectives", [])
    skills_card_html = ""
    if objectives:
        obj_lis = "".join(
            f'<li class="flex items-start gap-2.5 p-2.5 rounded-lg border border-slate-800/80 bg-slate-900/40">'
            f'<span class="text-emerald-400 font-bold text-xs shrink-0 mt-0.5">✓</span>'
            f'<span class="leading-relaxed font-sans">{highlight_tech_terms(clean_thai_spacing(get_thai_objective(obj)))}</span>'
            f'</li>'
            for obj in objectives
        )
        skills_card_html = f"""
        <div class="p-4 sm:p-5 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
          <div class="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center justify-between">
            <span class="flex items-center gap-2">
              <span class="text-sm">🎯</span>
              <span>ทักษะที่ข้อสอบประเมินในบทนี้ (Exam Competency Checklist)</span>
            </span>
            <span class="text-slate-500 font-mono text-[11px]">{len(objectives)} วัตถุประสงค์</span>
          </div>
          <ul class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs sm:text-[13px] text-slate-200">
            {obj_lis}
          </ul>
        </div>
        """

    badge_sub = f"Subdomain {sub_no}" if sub_no else f"Domain {domain_no}"

    return f"""
    <section id="exam-summary" class="mt-16 pt-10 border-t-2 border-indigo-500/40 scroll-mt-20">
      <div class="rounded-2xl border border-indigo-500/40 bg-gradient-to-br from-indigo-950/60 via-slate-900/95 to-slate-950 p-5 sm:p-8 shadow-2xl space-y-7">
        
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-indigo-500/30 pb-5">
          <div class="flex items-start gap-3.5">
            <div class="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-indigo-500/20 text-indigo-300 text-xl font-bold shrink-0 mt-0.5 shadow-md shadow-indigo-500/20">
              ⚡
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold uppercase tracking-wider text-amber-400">สรุปเร่งด่วนก่อนสอบ (Exam Cram Sheet)</span>
                <span class="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono font-medium">{badge_sub}</span>
              </div>
              <h2 class="text-xl sm:text-2xl font-bold text-white mt-1">
                สรุปสาระสำคัญทุกหัวข้อประจำบทเรียน
              </h2>
              <p class="text-xs sm:text-sm text-slate-300 mt-1 leading-relaxed">
                รวบรวมแก่นสถาปัตยกรรม กลไกสำคัญ และจุดที่ข้อสอบมักหลอก สำหรับทบทวนแบบเร่งด่วนก่อนเข้าห้องสอบ Anthropic Certification
              </p>
            </div>
          </div>
          <a href="#" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}}); return false;" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium transition cursor-pointer self-start sm:self-auto shrink-0 shadow-xs">
            <span>↑</span>
            <span>กลับด้านบน</span>
          </a>
        </div>

        <!-- 1. Golden Architectural Rule -->
        {golden_rule_html}

        <!-- 2. Topic-by-Topic Breakdown -->
        <div class="space-y-3.5">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-400">
              <span class="text-sm">📌</span>
              <span>สาระสำคัญแยกตามทุกหัวข้อ (Topic-by-Topic Key Points)</span>
            </div>
            <span class="text-slate-500 font-mono text-[11px]">{len(sections)} หัวข้อ</span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sec_cards}
          </div>
        </div>

        <!-- 3. Exam Traps Checklist -->
        {traps_card_html}

        <!-- 4. Competency Checklist -->
        {skills_card_html}

      </div>
    </section>
    """
