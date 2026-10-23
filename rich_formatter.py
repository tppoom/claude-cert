import re, html
from quiz_translator import clean_thai_spacing

# Code tokens, file names, API endpoints, hooks
CODE_TOKENS = [
    r'CLAUDE\.md', r'settings\.json', r'\.claude/', r'query\(\)', r'messages\.create',
    r'messages\.batches', r'tool_choice', r'PreToolUse', r'PostToolUse', r'StopHook',
    r'/v1/messages', r'/v1/batches', r'agent\.tool_use', r'sandbox', r'sys\.stdout',
    r'temperature', r'top_p', r'top_k', r'max_tokens', r'stop_sequences',
    r'asyncio\.gather', r'stream=True', r'tools=\[', r'thinking\.budget_tokens'
]

# Conceptual, architectural, and framework terms
CONCEPT_TERMS = [
    r'Client SDK', r'Agent SDK', r'Managed Agents', r'Claude Code',
    r'Orchestrator', r'Subagents?', r'Workflows?', r'Autonomous Agents?',
    r'Context Windows?', r'Prompt Caching', r'Model Context Protocol',
    r'MCP', r'Zero Data Retention', r'ZDR', r'Human-in-the-[lL]oop',
    r'JSON Schema', r'Tool Runner', r'Messages API', r'Evaluator-Optimizer',
    r'Chain-of-Thought', r'Few-shot', r'Prompt Injection', r'Jailbreak',
    r'Server-Sent Events', r'SSE', r'Thinking Modes?', r'Fast Mode',
    r'Claude 3\.5 Sonnet', r'Claude 3\.5 Haiku', r'Claude 3 Opus',
    r'Claude 3 Sonnet', r'Claude 3 Haiku'
]

STARTERS = [
    # Pronouns & Direct Subjects
    r'คุณ(?:เขียน|จัดการ|สามารถ|ไม่|ต้อง|จะ|กำหนด|เลือก|ส่ง|นำ|ลอง|ให้|ยังคง|เริ่ม|ใช้|ประเมิน|ดู|พบ|สร้าง|รัน)',
    r'(?:Claude|คลอดด์|Anthropic)\s*(?:จะ|ประเมิน|ตอบสนอง|ได้|จัดกลุ่ม|แนะนำ)',
    r'โมเดล(?:จะ|สามารถ|ต้อง|ให้|นี้|ที่)',
    r'ระบบ(?:จะ|สามารถ|มี|นี้|ที่|อัตโนมัติ)',
    r'เอเจนต์(?:จะ|สามารถ|ทุก|นี้|ที่|ปล่อย|เรียก|คือ|ช่วย|ย่อย|หลัก)',
    r'ตัวแทน(?:จะ|สามารถ|ทุก|นี้|ที่|ปล่อย|เรียก|คือ|ช่วย|ย่อย|หลัก)',
    r'เวิร์กโฟลว์(?:เรียกใช้|มี|สามารถ|จะ|คือ|นี้|ที่)',
    r'ไคลเอ็นต์(?:จะ|สามารถ|มี|ของ)',
    r'เซิร์ฟเวอร์(?:จะ|สามารถ|มี)',
    r'บริการนี้(?:เหมาะ|ช่วย|จะ)',
    r'สิ่งนี้(?:ช่วย|ทำ|เป็น|หมายถึง)',
    r'บาง(?:งาน|ครั้ง|ระบบ|กรณี)',
    
    # Quantifiers & Noun phrases
    r'ทุก(?:ระบบ|ครั้ง|ขั้นตอน|กรณี|ตัวเลือก|โมเดล|เอเจนต์|คน)',
    r'แต่ละ(?:เลเยอร์|ตัวเลือก|ขั้นตอน|แบบ|รุ่น|รอบ|งาน|เซสชัน|ส่วน)',
    r'ประการ(?:แรก|ที่สอง|ที่สาม|สุดท้าย)',
    r'การ(?:วิจัย|ค้นหา|ประเมิน|ทำงาน|ทดสอบ|สลับ|เลือก|สร้าง|กำหนด|ใช้งาน|จัดการ|เรียก|ตอบสนอง|ตั้งค่า|ปักหมุด|วิ่งซ้ำ|ประสานงาน|รวม|ดำเนินการ|บีบอัด|เขียน|เข้าถึง|สนทนา|ตอบกลับ|แลกเปลี่ยน|เชื่อมต่อ)',
    r'ความ(?:แตกต่าง|สามารถ|เป็นไปได้|เสี่ยง|ถูกต้อง)',
    r'(?:ต้นทุน|ค่าใช้จ่าย|ความเสี่ยง|ข้อดี|ข้อเสีย|เป้าหมาย|ผลลัพธ์|กฎ|ข้อแตกต่าง|จุดประสงค์|จุดเด่น|สิ่งสำคัญ)(?:หลัก|การออกแบบ|นี้)?คือ',
    r'งานแบบ(?:แบตช์)?',
    r'จอแสดงผล(?:ความคืบหน้า)?',
    r'UI\s*(?:แบบสด)?',
    r'SDK\b', r'API\b', r'TypeScript\b', r'Python\b', r'LLM\b', r'JSON\b', r'MCP\b',
    r'หน้าต่างบริบท(?:คือ|จะ|มี)?',
    r'สคีมา(?:คือ|จะ|มี)?',
    r'รูปแบบที่(?:ง่าย|ซับซ้อน|เหมาะ)?',
    
    # Connectives & Adverbs
    r'ดังนั้น', r'นอกจากนี้', r'อย่างไรก็ตาม', r'ตัวอย่างเช่น', r'ในทางกลับกัน', r'ในขณะเดียวกัน',
    r'อันที่จริง', r'โดยสรุป', r'ท้ายที่สุด', r'นอกเหนือจาก(?:นั้น|พวกเขา|นี้)',
    
    # Prepositional & Temporal
    r'ใน\s*(?:TypeScript|Python|กรณี|บทเรียน|การรัน|การวิจัย|สตรีม|ระบบ|เซสชัน|ที่สุด)',
    r'สำหรับ\s*(?:แอปพลิเคชัน|งาน|กรณี|ระบบ|โมเดล|เอเจนต์|ผู้ใช้|การ|สิ่งนั้น|ข้อมูลนี้|สิ่งนี้)',
    r'สําหรับ\s*(?:แอปพลิเคชัน|งาน|กรณี|ระบบ|โมเดล|เอเจนต์|ผู้ใช้|การ|สิ่งนั้น|ข้อมูลนี้|สิ่งนี้)',
    r'ภายใต้\s*(?:การ|โหมด|สภาวะ|auto)',
    r'เมื่อ\s*(?:รันไทม์|คุณ|โมเดล|ระบบ|เซสชัน|เกิด)',
    r'หาก\s*(?:คุณ|โมเดล|ระบบ|เพื่อนร่วมงาน|ผลลัพธ์|ต้องการ|ค่า)',
    r'ถ้า\s*(?:คุณ|โมเดล|ระบบ)',
    r'เนื่องจาก\s*(?:เวิร์กโฟลว์|ระบบ|โมเดล|เอเจนต์|การ)?',
    r'หลัง(?:จาก|การ)',
    r'ข้อ(?:แรก|ที่สอง|ที่สาม|สุดท้าย|สำคัญ)',
    r'ส่วน(?:นี้|ที่)',
    
    # Imperatives & Advice
    r'อย่า\s*(?:หยุด|ลืม|ใช้|ปล่อย|พึ่งพา)',
    r'โปรด\s*(?:ระบุ|ตรวจสอบ|ใช้)',
    r'ระวัง\s*(?:การ|ว่า)',
    r'ควร\s*(?:ใช้|ระบุ|กำหนด)',
    r'ให้\s*(?:เริ่มต้น|พิจารณา|ใช้|ส่ง|ถาม)',
    r'ตั้ง(?:ชื่อ|ค่า)',
    r'เพิ่ม(?:ฟิลด์|เติม|โค้ด)',
    r'ไม่มี(?:สิ่งใด|อะไร|ใคร)'
]

PAT_STARTERS = '|'.join(STARTERS)
BAD_CONJUNCTIONS = {'และ', 'หรือ', 'แต่', 'ว่า', 'โดย', 'เพื่อ', 'ซึ่ง', 'ที่', 'กับ', 'เช่น', 'รวมถึง', 'ทั้ง', 'ของ', 'คือ', ':', ',', 'ให้'}

def is_bad_prefix(prefix):
    prefix = prefix.strip()
    if not prefix:
        return False
    if prefix in BAD_CONJUNCTIONS:
        return True
    if any(prefix.endswith(c) for c in ['และ', 'หรือ', 'แต่', 'ว่า', 'โดย', 'เพื่อ', 'ซึ่ง', 'กับ', 'รวมถึง', ' ให้']):
        return True
    if prefix.endswith('ที่') and not any(prefix.endswith(w) for w in ['คงที่', 'หน้าที่', 'สถานที่', 'พื้นที่', 'เต็มที่', 'ทันที', 'ทุกที่', 'เหล่านี้']):
        return True
    if prefix.endswith('ของ') and not any(prefix.endswith(w) for w in ['สิ่งของ', 'ข้าวของ']):
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

    if not split_indices:
        return [text.strip()]
        
    chunks = []
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
        if merged and (len(merged[-1]) < 35 or is_bad_prefix(merged[-1])):
            merged[-1] = merged[-1] + ' ' + c
        else:
            merged.append(c)
    return merged

def format_readable_content(p_th, p_raw, is_first_para=False):
    p_th = p_th.strip()
    if not p_th:
        return ""
    p_th = clean_thai_spacing(p_th)
    
    # Clean glued exam labels
    p_th = re.sub(r'^(?:กับดักการสอบ|Exam Trap:?\s*)(.+)$', r'⚠️ จุดที่ข้อสอบชอบหลอก: \1', p_th)
    p_th = re.sub(r'^(?:คาดการณ์ก่อน|Predict First:?\s*)(.+)$', r'🔮 คาดการณ์ก่อนตอบ: \1', p_th)

    # 1. Numbered Sequence Step List (e.g. "1. The SDK... 2. Claude... 3. SDK...")
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

    # 2. Bullet list inside paragraph (e.g. "- ตัวแทน: โมเดล... - สภาพแวดล้อม: ที่ที่...")
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

    # 3. Lead Concept Card (First paragraph of section)
    if is_first_para:
        sents = split_thai_sentences(p_th)
        if len(sents) > 1:
            body = "".join(f'<p class="text-sm sm:text-base text-slate-100 leading-relaxed sm:leading-loose font-normal my-2">{highlight_tech_terms(s)}</p>' for s in sents)
        else:
            body = f'<p class="text-sm sm:text-base text-slate-100 font-medium leading-relaxed sm:leading-loose">{highlight_tech_terms(p_th)}</p>'
        return f"""
        <div class="my-5 p-4 sm:p-5 rounded-2xl border-l-4 border-l-indigo-500 border-y border-r border-slate-800 bg-slate-900/70 shadow-sm space-y-1.5">
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

    # 5. Long paragraph with multiple sentences -> format into spaced sub-paragraphs
    sents = split_thai_sentences(p_th)
    if len(sents) >= 2 and len(p_th) > 140:
        # Group sentences into readable sub-paragraphs of 1-2 sentences
        sub_paras = []
        curr = []
        curr_len = 0
        for s in sents:
            if curr and (curr_len + len(s) > 200 or len(curr) >= 2):
                sub_paras.append(" ".join(curr))
                curr = [s]
                curr_len = len(s)
            else:
                curr.append(s)
                curr_len += len(s)
        if curr:
            sub_paras.append(" ".join(curr))
            
        paras_html = "".join(f'<p class="text-slate-300 text-sm sm:text-[15px] leading-relaxed sm:leading-loose my-3">{highlight_tech_terms(sp)}</p>' for sp in sub_paras)
        return f'<div class="my-4 space-y-3 p-0.5">{paras_html}</div>'

    # 6. Standard paragraph
    return f"""
    <p class="text-slate-300 text-sm sm:text-[15px] leading-relaxed sm:leading-loose my-3.5">
      {highlight_tech_terms(p_th)}
    </p>
    """