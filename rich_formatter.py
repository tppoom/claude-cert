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

def format_readable_content(p_th, p_raw="", is_first_para=False):
    p_th = p_th.strip()
    if not p_th:
        return ""
    p_th = clean_thai_spacing(p_th)
    
    # Clean glued exam labels
    p_th = re.sub(r'^(?:(?:จุดที่ข้อสอบชอบหลอก|กับดักการสอบ|หลุมพรางการสอบ|Exam\s*Trap)[\s:\(\)]*)+', '⚠️ จุดที่ข้อสอบชอบหลอก: ', p_th)
    p_th = re.sub(r'^(?:(?:คาดการณ์ก่อนตอบ|คาดการณ์ก่อน|Predict\s*First)[\s:\(\)]*)+', '🔮 คาดการณ์ก่อนตอบ: ', p_th)

    # 1. Numbered Sequence Step List (Clean, readable, NO heavy cards)
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
                en_ref_html = f'<div class="text-xs text-slate-400 font-mono mt-1 leading-relaxed">{html.escape(raw_steps[idx][1])}</div>'
            lis += f"""
            <li class="flex items-start gap-3">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/15 text-indigo-300 font-semibold text-xs shrink-0 mt-0.5 border border-indigo-500/30">{num}</span>
              <div class="grow leading-relaxed">
                <div class="text-slate-200 text-[15px] sm:text-base leading-relaxed sm:leading-loose font-normal">
                  {th_body_fmt}
                </div>
                {en_ref_html}
              </div>
            </li>
            """
        return f'<ol class="space-y-3.5 my-5 pl-1">{lis}</ol>'

    # 2. Explicit Bullet list inside paragraph (e.g. "- ตัวแทน: โมเดล... - สภาพแวดล้อม: ที่ที่...")
    bullet_parts = [b.strip().lstrip('-•* \t') for b in re.split(r'(?:^|\s+)[-•*]\s+', p_th) if b.strip().lstrip('-•* \t')]
    if len(bullet_parts) >= 2:
        lis = ""
        for bp in bullet_parts:
            m_colon = re.match(r'^([^:]{2,35}):\s*(.+)$', bp)
            if m_colon:
                term, desc = m_colon.group(1), m_colon.group(2)
                item_content = f'<strong class="text-indigo-300 font-semibold">{highlight_tech_terms(term)}:</strong> <span class="text-slate-300">{highlight_tech_terms(desc)}</span>'
            else:
                item_content = f'<span class="text-slate-300">{highlight_tech_terms(bp)}</span>'
            lis += f"""
            <li class="flex items-start gap-3">
              <span class="text-indigo-400 font-bold shrink-0 mt-1 text-sm">•</span>
              <div class="grow text-[15px] sm:text-base leading-relaxed sm:leading-loose text-slate-300">{item_content}</div>
            </li>
            """
        return f'<ul class="space-y-2.5 my-4 pl-1">{lis}</ul>'

    # 3. Separate Warning/Caution if embedded in paragraph
    sents = split_thai_sentences(p_th)
    warnings = []
    normal_sents = []
    for s in sents:
        if re.search(r'^(?:อย่า|ระวัง|ข้อควรระวัง|คําเตือน|คำเตือน|Exam Trap)', s.strip()):
            warnings.append(s.strip())
        else:
            normal_sents.append(s.strip())

    warn_html = ""
    for w in warnings:
        warn_html += f"""
        <div class="my-4 p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/20 text-xs sm:text-sm text-amber-200 leading-relaxed flex items-start gap-2.5 shadow-xs">
          <span class="text-amber-400 shrink-0 text-base leading-none">⚠️</span>
          <div class="grow"><strong class="text-amber-300 font-semibold">ข้อควรระวัง & จุดสังเกต:</strong> {highlight_tech_terms(w)}</div>
        </div>
        """

    if not normal_sents:
        return warn_html

    # 4. Standard Flowing Paragraphs (Natural typography, zero card clutter!)
    # If the text is very long (>= 4 sentences and >= 350 chars), break into 2 natural paragraphs
    if len(normal_sents) >= 4 and len(p_th) >= 350:
        mid = (len(normal_sents) + 1) // 2
        p1 = " ".join(normal_sents[:mid])
        p2 = " ".join(normal_sents[mid:])
        html_p = f"""
        <p class="text-[15px] sm:text-base text-slate-300 leading-relaxed sm:leading-loose mb-4 font-normal">
          {highlight_tech_terms(p1)}
        </p>
        <p class="text-[15px] sm:text-base text-slate-300 leading-relaxed sm:leading-loose mb-4 font-normal">
          {highlight_tech_terms(p2)}
        </p>
        """
    else:
        full_text = " ".join(normal_sents)
        html_p = f"""
        <p class="text-[15px] sm:text-base text-slate-300 leading-relaxed sm:leading-loose mb-4 font-normal">
          {highlight_tech_terms(full_text)}
        </p>
        """

    return html_p + warn_html