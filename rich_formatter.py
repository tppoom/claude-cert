import re, html
from quiz_translator import clean_thai_spacing

# Code tokens, file names, API endpoints, hooks
CODE_TOKENS = [
    r'CLAUDE\.md', r'settings\.json', r'\.claude/', r'query\(\)', r'messages\.create',
    r'messages\.batches', r'tool_choice', r'PreToolUse', r'PostToolUse', r'StopHook',
    r'/v1/messages', r'/v1/batches', r'agent\.tool_use', r'sandbox', r'sys\.stdout',
    r'temperature', r'top_p', r'top_k', r'max_tokens', r'stop_sequences',
    r'asyncio\.gather', r'stream=True', r'tools=\[', r'thinking\.budget_tokens',
    r'inputSchema', r'outputSchema', r'output_config\.effort'
]

# Conceptual, architectural, and framework terms
CONCEPT_TERMS = [
    r'Client SDK', r'Agent SDK', r'Managed Agents', r'Claude Code',
    r'Orchestrator', r'Subagents?', r'Workflows?', r'Autonomous Agents?',
    r'Context Windows?', r'Context Pollution', r'Context Isolation',
    r'Prompt Caching', r'Model Context Protocol', r'MCP Server', r'MCP Client',
    r'MCP', r'Zero Data Retention', r'ZDR', r'Human-in-the-[lL]oop', r'HITL',
    r'JSON Schema', r'Tool Runner', r'Messages API', r'Evaluator-Optimizer',
    r'Chain-of-Thought', r'Few-shot', r'Zero-shot', r'Prompt Injection', r'Jailbreak',
    r'Server-Sent Events', r'SSE', r'Thinking Modes?', r'Thinking Budget', r'Fast Mode',
    r'Model Pinning', r'Pinned Version', r'Capability Bloat', r'Single Agent',
    r'Parallelization', r'Tool Output Pruning', r'Augmented LLM', r'Building Blocks?',
    r'Prompt Engineering', r'System Prompt', r'AssistantMessage', r'UserMessage', r'ResultMessage',
    r'Claude 3\.5 Sonnet', r'Claude 3\.5 Haiku', r'Claude 3 Opus',
    r'Claude 3 Sonnet', r'Claude 3 Haiku'
]

# Clean discourse and sentence starters (never slicing inside existing clauses)
STARTERS = [
    # Discourse Connectives & Transitions
    r'นอกจากนี้', r'อย่างไรก็ตาม', r'ตัวอย่างเช่น', r'ในทางกลับกัน', r'ในขณะเดียวกัน',
    r'อันที่จริง', r'โดยสรุป', r'ท้ายที่สุด', r'ดังนั้น', r'ทั้งนี้', r'แทนที่จะ(?:ทำเช่นนั้น)?',
    
    # Conditional & Temporal Clauses
    r'หาก\s+[ก-๙a-zA-Z0-9_]+', r'ถ้า\s+[ก-๙a-zA-Z0-9_]+', r'เมื่อ\s+[ก-๙a-zA-Z0-9_]+',
    
    # Imperatives & Advice
    r'อย่า\s+[ก-๙a-zA-Z0-9_]+', r'โปรด\s+[ก-๙a-zA-Z0-9_]+', r'ระวัง\s+[ก-๙a-zA-Z0-9_]+',
    r'ข้อควรระวัง\b', r'คำเตือน\b', r'จุดสังเกต\b',
    
    # Quantifiers & Structure
    r'ขั้นตอนที่\s*\d+', r'ประการ(?:แรก|ที่สอง|ที่สาม|สุดท้าย)',
    r'สำหรับ\s+[ก-๙a-zA-Z0-9_]+', r'สําหรับ\s+[ก-๙a-zA-Z0-9_]+',
    
    # Specific Architectural Topic Subjects
    r'งานแบบ(?:แบทช์|แบตช์)', r'จอแสดงผลความคืบหน้า', r'หน้าจอแสดงผล',
    r'UI\s*แบบสด', r'ตัววงจร(?:นั้น)?', r'คุณยังคง'
]

PAT_STARTERS = '|'.join(STARTERS)

TRANSITIVE_VERBS = [
    "ต้องการ", "ปรับ", "เลือก", "สร้าง", "เรียก", "ใช้", "รัน", "ส่ง", "พบ", 
    "มี", "เป็น", "คือ", "ได้", "ให้", "เริ่ม", "ช่วย", "ทำ", "รู้", "เห็น", 
    "ระบุ", "กำหนด", "จัด", "ทดสอบ", "ประเมิน", "รองรับ", "ครอบคลุม", "รวม",
    "นำ", "ถือ", "เขียน", "อ่าน", "รับ", "ส่งผ่าน", "ผ่าน", "เข้าสู่", "เชื่อมต่อ"
]

PREPOSITIONS_CONJUNCTIONS = [
    "และ", "หรือ", "แต่", "ว่า", "โดย", "เพื่อ", "ซึ่ง", "ที่", "กับ", "เช่น", 
    "รวมถึง", "ทั้ง", "ของ", "จาก", "สู่", "ต่อ", "ระหว่าง", "ตาม", "ด้วย",
    "ใน", "บน", "ใต้", "เกี่ยวกับ", "ด้าน", "ทาง", "เพื่อที่", "โดยที่", "เนื่องจาก",
    "ไม่", "ไม่ได้", "มิได้", "ที่จะ", "ซึ่งจะ", "อันจะ", "ที่ต้อง", "ที่ควร"
]

ALL_BAD_ENDINGS = set(TRANSITIVE_VERBS + PREPOSITIONS_CONJUNCTIONS)

def is_bad_prefix(prefix):
    prefix = prefix.strip()
    if not prefix:
        return False
    if len(prefix) < 25:
        return True
    for w in ALL_BAD_ENDINGS:
        if prefix.endswith(w) or prefix.endswith(w + " ") or prefix.endswith(w + ":"):
            return True
    return False

def highlight_tech_terms(text):
    if not text:
        return ""
    text = clean_thai_spacing(text)
    escaped = html.escape(text)
    
    # 1. Code tokens & files
    for ct in CODE_TOKENS:
        escaped = re.sub(
            rf'(?<![a-zA-Z0-9_\-\.\/])({ct})(?![a-zA-Z0-9_\-\.\/])',
            r'<code class="px-1.5 py-0.5 rounded bg-slate-800 text-amber-300 font-mono text-xs border border-slate-700/60 font-medium">\1</code>',
            escaped, flags=re.I
        )
        
    # 2. Core architectural concepts
    for t in CONCEPT_TERMS:
        escaped = re.sub(
            rf'(?<![a-zA-Z0-9_\-])({t})(?![a-zA-Z0-9_\-])',
            r'<strong class="text-indigo-300 font-semibold">\1</strong>',
            escaped
        )
        
    # 3. Clean [Reference] (Lesson X.Y)
    escaped = re.sub(
        r'\[([^\]]+)\]\s*\((?:บทเรียน|Lesson):\s*([^)]+)\)',
        r'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-950/60 text-indigo-300 border border-indigo-800/40 text-xs font-mono font-medium">📖 \1 (\2)</span>',
        escaped
    )
    
    return escaped

def extract_numbered_steps(text):
    if not text:
        return []
    parts = re.split(r'(?:^|\s+)(?=\d+[\.\)]\s+)', text.strip())
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r'^(\d+)[\.\)]\s*(.*)$', p, re.DOTALL)
        if m:
            cleaned.append((m.group(1), m.group(2).strip()))
        elif cleaned:
            prev_num, prev_body = cleaned[-1]
            cleaned[-1] = (prev_num, prev_body + ' ' + p)
    if len(cleaned) >= 2:
        return cleaned
    return []

def split_thai_sentences(text):
    text = clean_thai_spacing(text)
    matches = list(re.finditer(rf'({PAT_STARTERS})', text))
    split_indices = []
    for m in matches:
        start_idx = m.start()
        prefix = text[:start_idx]
        sub = text[:start_idx]
        if sub.count('(') > sub.count(')') or sub.count('[') > sub.count(']'):
            continue
        if is_bad_prefix(prefix):
            continue
        split_indices.append(start_idx)

    chunks = []
    if not split_indices:
        chunks = [text.strip()]
    else:
        last_idx = 0
        for s_start in split_indices:
            chunk = text[last_idx:s_start].strip()
            if chunk:
                chunks.append(chunk)
            last_idx = s_start
        final_chunk = text[last_idx:].strip()
        if final_chunk:
            chunks.append(final_chunk)
        
    merged = []
    for c in chunks:
        if merged and (len(merged[-1]) < 22 or is_bad_prefix(merged[-1])):
            merged[-1] = merged[-1] + ' ' + c
        else:
            merged.append(c)

    # Intelligent fallback: If still a single chunk and length > 260 chars,
    # split on secondary pauses like commas, semicolons, dashes or secondary Thai markers
    if len(merged) == 1 and len(merged[0]) > 260:
        single = merged[0]
        sec_matches = list(re.finditer(r'(?:[;:\.]\s+|(?<=[^\s])\s*[–—]\s*|(?<=[^\s])\s+(?:ในขณะที่|โดยที่|ทั้งนี้|เนื่องจาก|เพื่อที่|รวมถึง|ซึ่งครอบคลุมใน)\s*)', single))
        if sec_matches:
            sec_chunks = []
            l_idx = 0
            for sm in sec_matches:
                split_pt = sm.start()
                if split_pt - l_idx >= 40:
                    sec_chunks.append(single[l_idx:split_pt].strip())
                    l_idx = sm.start()
            if single[l_idx:].strip():
                sec_chunks.append(single[l_idx:].strip())
            if len(sec_chunks) >= 2:
                return [sc for sc in sec_chunks if sc]

    return merged

def format_readable_content(p_th, p_raw, is_first_para=False):
    p_th = p_th.strip()
    if not p_th:
        return ""
    p_th = clean_thai_spacing(p_th)
    
    # Clean glued exam labels
    p_th = re.sub(r'^(?:(?:จุดที่ข้อสอบชอบหลอก|กับดักการสอบ|หลุมพรางการสอบ|Exam\s*Trap)[\s:\(\)]*)+', '⚠️ จุดที่ข้อสอบชอบหลอก: ', p_th)
    p_th = re.sub(r'^(?:(?:คาดการณ์ก่อนตอบ|คาดการณ์ก่อน|Predict\s*First)[\s:\(\)]*)+', '🔮 คาดการณ์ก่อนตอบ: ', p_th)

    # 1. Numbered Sequence Step List (Cards with step badges)
    th_steps = extract_numbered_steps(p_th)
    raw_steps = extract_numbered_steps(p_raw) if p_raw else []
    
    use_steps = th_steps if len(th_steps) >= 2 else (raw_steps if len(raw_steps) >= 2 else [])
    if use_steps:
        lis = ""
        has_matching_raw = len(raw_steps) == len(use_steps)
        for idx, (num, body) in enumerate(use_steps):
            th_body_fmt = highlight_tech_terms(body)
            en_ref_html = ""
            if has_matching_raw and raw_steps[idx][1] != body:
                en_ref_html = f'<div class="text-xs text-slate-400 font-mono pt-1.5 border-t border-slate-800/60 leading-relaxed">{html.escape(raw_steps[idx][1])}</div>'
            lis += f"""
            <li class="flex items-start gap-3.5 p-4 rounded-xl border border-slate-800/90 bg-slate-900/50 hover:border-indigo-500/40 transition-colors shadow-sm">
              <span class="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-600 text-white font-bold text-xs shrink-0 mt-0.5 shadow-md shadow-indigo-600/30">{num}</span>
              <div class="grow space-y-1.5">
                <div class="text-slate-200 text-sm sm:text-[15px] leading-relaxed sm:leading-loose font-normal">
                  {th_body_fmt}
                </div>
                {en_ref_html}
              </div>
            </li>
            """
        return f'<ol class="space-y-3.5 my-5">{lis}</ol>'

    # 2. Explicit Bullet list inside paragraph (e.g. "- ตัวแทน: โมเดล... - สภาพแวดล้อม: ที่ที่...")
    bullet_parts = [b.strip().lstrip('-•* \t') for b in re.split(r'(?:^|\s+)[-•*]\s+', p_th) if b.strip().lstrip('-•* \t')]
    if len(bullet_parts) >= 2:
        lis = ""
        for bp in bullet_parts:
            m_colon = re.match(r'^([^:]{2,35}):\s*(.+)$', bp)
            if m_colon:
                term, desc = m_colon.group(1), m_colon.group(2)
                item_content = f'<strong class="text-indigo-300 font-semibold">{highlight_tech_terms(term)}:</strong> <span class="text-slate-200">{highlight_tech_terms(desc)}</span>'
            else:
                item_content = f'<span class="text-slate-200">{highlight_tech_terms(bp)}</span>'
            lis += f"""
            <li class="flex items-start gap-3 p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 text-sm sm:text-base leading-relaxed hover:border-indigo-500/30 transition-colors shadow-sm">
              <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-bold shrink-0 mt-0.5">▸</span>
              <div class="grow">{item_content}</div>
            </li>
            """
        return f'<ul class="space-y-2.5 my-4">{lis}</ul>'

    # 3. Lead Concept Hero Card (First paragraph of section)
    if is_first_para:
        sents = split_thai_sentences(p_th)
        if len(sents) > 1:
            lis = "".join(f'<li class="flex items-start gap-2.5 text-sm sm:text-base text-slate-100 leading-relaxed"><span class="text-indigo-400 font-bold shrink-0 mt-0.5">▸</span><div class="grow">{highlight_tech_terms(s)}</div></li>' for s in sents)
            body = f'<ul class="space-y-2.5 pt-1">{lis}</ul>'
        else:
            body = f'<p class="text-sm sm:text-base text-slate-100 font-medium leading-relaxed sm:leading-loose">{highlight_tech_terms(p_th)}</p>'
        return f"""
        <div class="my-5 p-5 rounded-2xl border-l-4 border-l-indigo-500 border-y border-r border-slate-800 bg-slate-900/80 shadow-md space-y-3">
          <div class="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
            <span class="text-base">💡</span>
            <span>แนวคิดหลักของหัวข้อนี้ (Core Concept)</span>
          </div>
          {body}
        </div>
        """

    # 4. Colon definition card (starts with 'Concept: ...')
    m_lead = re.match(r'^([^:]{2,30}):\s*([^\n]+)$', p_th)
    if m_lead and len(p_th) < 350:
        term, desc = m_lead.group(1), m_lead.group(2)
        return f"""
        <div class="my-3.5 p-4 rounded-xl border border-slate-800/90 bg-slate-900/50 hover:border-indigo-500/40 transition-colors shadow-sm">
          <div class="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
            <span class="text-indigo-500">🔹</span>
            <span>{html.escape(term)}</span>
          </div>
          <p class="text-sm sm:text-[15px] text-slate-200 leading-relaxed font-normal">{highlight_tech_terms(desc)}</p>
        </div>
        """

    # 5. Multi-sentence Paragraph -> Card Box with Bullet Points & Highlights
    sents = split_thai_sentences(p_th)
    if len(sents) >= 3:
        intro = sents[0]
        points = sents[1:]
        normal_points = []
        warnings = []
        for pt in points:
            if re.search(r'^(?:อย่า|ระวัง|ข้อควรระวัง|คําเตือน|คำเตือน|Exam Trap)', pt.strip()):
                warnings.append(pt)
            else:
                normal_points.append(pt)
                
        bullet_lis = ""
        for pt in normal_points:
            m_colon = re.match(r'^([^:–—]{2,35})[:–—]\s*(.+)$', pt)
            if m_colon:
                term, desc = m_colon.group(1), m_colon.group(2)
                pt_fmt = f'<strong class="text-indigo-300 font-semibold">{highlight_tech_terms(term)}:</strong> <span class="text-slate-200">{highlight_tech_terms(desc)}</span>'
            else:
                pt_fmt = f'<span class="text-slate-200">{highlight_tech_terms(pt)}</span>'
                
            bullet_lis += f"""
            <li class="flex items-start gap-3 p-3 rounded-xl border border-slate-800/80 bg-slate-950/40 text-xs sm:text-sm leading-relaxed hover:border-indigo-500/30 transition-colors shadow-xs">
              <span class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-indigo-500/20 text-indigo-400 text-xs font-bold shrink-0 mt-0.5">▸</span>
              <div class="grow">{pt_fmt}</div>
            </li>
            """

        warn_html = ""
        for w in warnings:
            warn_html += f"""
            <div class="p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/25 text-xs sm:text-sm text-amber-200 leading-relaxed flex items-start gap-2.5 mt-2.5 shadow-xs">
              <span class="text-amber-400 shrink-0 text-base leading-none">⚠️</span>
              <div class="grow"><strong class="text-amber-300 font-semibold">ข้อควรระวัง & จุดสังเกต:</strong> {highlight_tech_terms(w)}</div>
            </div>
            """
            
        return f"""
        <div class="my-5 p-4 sm:p-5 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-sm space-y-3.5">
          <div class="text-slate-100 font-semibold text-sm sm:text-base flex items-start gap-2.5 leading-relaxed pb-2.5 border-b border-slate-800/70">
            <span class="text-indigo-400 shrink-0 text-base mt-0.5">📌</span>
            <span>{highlight_tech_terms(intro)}</span>
          </div>
          <ul class="space-y-2.5 pt-1">
            {bullet_lis}
          </ul>
          {warn_html}
        </div>
        """

    # 6. Two-sentence Paragraph -> Dual-Point Mini Card with Bullet Chips
    elif len(sents) == 2:
        return f"""
        <div class="my-4 p-4 sm:p-4.5 rounded-xl border border-slate-800/85 bg-slate-900/50 hover:border-indigo-500/30 transition-colors shadow-xs">
          <ul class="space-y-2.5">
            <li class="flex items-start gap-3 text-xs sm:text-sm leading-relaxed text-slate-200">
              <span class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-indigo-500/20 text-indigo-400 text-xs font-bold shrink-0 mt-0.5">▸</span>
              <div class="grow font-medium text-slate-100">{highlight_tech_terms(sents[0])}</div>
            </li>
            <li class="flex items-start gap-3 text-xs sm:text-sm leading-relaxed text-slate-300">
              <span class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-indigo-500/20 text-indigo-400 text-xs font-bold shrink-0 mt-0.5">▸</span>
              <div class="grow">{highlight_tech_terms(sents[1])}</div>
            </li>
          </ul>
        </div>
        """

    # 7. Single Sentence Statement / Transition Line
    else:
        if len(p_th) >= 140:
            return f"""
            <div class="my-3.5 p-3.5 sm:p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 text-xs sm:text-sm text-slate-200 leading-relaxed flex items-start gap-3 shadow-xs">
              <span class="text-indigo-400 text-sm shrink-0 mt-0.5">📌</span>
              <div class="grow">{highlight_tech_terms(p_th)}</div>
            </div>
            """
        else:
            return f"""
            <p class="text-slate-300 text-xs sm:text-sm font-medium leading-relaxed my-3 flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0"></span>
              <span>{highlight_tech_terms(p_th)}</span>
            </p>
            """