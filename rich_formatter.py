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
    r'(?:Claude|คลอดด์|Anthropic)\s*(?:จะ|อาจ|สามารถ|ประเมิน|ตอบสนอง|ได้|จัดกลุ่ม|แนะนำ|ช่วย)',
    r'โมเดล(?:จะ|สามารถ|ต้อง|ให้|นี้|ที่|เหล่านั้น|นั้น)',
    r'ระบบ(?:จะ|สามารถ|มี|นี้|ที่|อัตโนมัติ|เหล่านั้น)',
    r'เอเจนต์(?:จะ|สามารถ|ทุก|นี้|ที่|ปล่อย|เรียก|คือ|ช่วย|ย่อย|หลัก|เหล่านั้น)',
    r'ตัวแทน(?:จะ|สามารถ|ทุก|นี้|ที่|ปล่อย|เรียก|คือ|ช่วย|ย่อย|หลัก|เหล่านั้น)',
    r'เวิร์กโฟลว์(?:เรียกใช้|มี|สามารถ|จะ|คือ|นี้|ที่)',
    r'ไคลเอ็นต์(?:จะ|อาจ|สามารถ|มี|ของ|อ่าน|เขียน|รับ|ส่ง)',
    r'เซิร์ฟเวอร์(?:จะ|อาจ|สามารถ|มี|อ่าน|เขียน|รับ|ส่ง)',
    r'ผู้ใช้(?:ที่|จะ|สามารถ|เหล่านั้น)',
    r'นักพัฒนา(?:ที่|จะ|สามารถ|ของ)',
    r'ทีม(?:วิศวกร|พัฒนา|ความปลอดภัย|ที่)',
    r'บริการนี้(?:เหมาะ|ช่วย|จะ)',
    r'สิ่งนี้(?:ช่วย|ทำ|เป็น|หมายถึง)',
    r'บาง(?:งาน|ครั้ง|ระบบ|กรณี)',
    
    # Quantifiers & Noun phrases
    r'ทุก(?:ระบบ|ครั้ง|ขั้นตอน|กรณี|ตัวเลือก|โมเดล|เอเจนต์|คน)',
    r'แต่ละ(?:เลเยอร์|ตัวเลือก|ขั้นตอน|แบบ|รุ่น|รอบ|งาน|เซสชัน|ส่วน|ID|ฟิลด์|คีย์|พารามิเตอร์|โมเดล|เอเจนต์|เครื่องมือ|รายการ|ข้อความ)',
    r'ประการ(?:แรก|ที่สอง|ที่สาม|สุดท้าย)',
    r'การ(?:วิจัย|ค้นหา|ประเมิน|ทำงาน|ทดสอบ|สลับ|เลือก|สร้าง|กำหนด|ใช้งาน|จัดการ|เรียก|ตอบสนอง|ตั้งค่า|ปักหมุด|วิ่งซ้ำ|ประสานงาน|รวม|ดำเนินการ|บีบอัด|เขียน|เข้าถึง|สนทนา|ตอบกลับ|แลกเปลี่ยน|เชื่อมต่อ|กระตุ้น|แยกบริบท|ตรวจสอบสิทธิ์)',
    r'ความ(?:แตกต่าง|สามารถ|เป็นไปได้|เสี่ยง|ถูกต้อง)',
    r'(?:ต้นทุน|ค่าใช้จ่าย|ความเสี่ยง|ข้อดี|ข้อเสีย|เป้าหมาย|ผลลัพธ์|กฎ|ข้อแตกต่าง|จุดประสงค์|จุดเด่น|สิ่งสำคัญ)(?:หลัก|การออกแบบ|นี้)?คือ',
    r'งานแบบ(?:แบตช์)?',
    r'งาน(?:วิศวกรรม|แบบ|ย่อย)',
    r'จอแสดงผล(?:ความคืบหน้า)?',
    r'UI\s*(?:แบบสด)?',
    r'ปลั๊กอิน(?:ที่|นี้|จะ)?',
    r'กลไก(?:เดียวนี้|นี้)?',
    r'มี(?:สองวิธี|หลายวิธี|ข้อดี|ข้อเสีย|ตัวเลือก)',
    r'การคิดแบบ(?:ปรับตัวได้|ขยาย)?',
    r'งบประมาณ(?:ต้อง|โทเค็น)?',
    r'หน้าต่างบริบท(?:คือ|จะ|มี)?',
    r'สคีมา(?:คือ|จะ|มี)?',
    r'รูปแบบที่(?:ง่าย|ซับซ้อน|เหมาะ)?',
    r'ขั้นตอน(?:สุดท้าย|แรก|ที่สอง|ที่สาม)',
    r'ยืนยันว่า',
    r'ตั้งแต่(?:รุ่น|เวอร์ชัน|วันนี้|นั้น|เริ่ม|ระดับ|ปี|เดือน|Claude)',
    r'(?<!ใน)รุ่น(?:เก่า|ใหม่|ก่อนหน้า)(?:จะ|มี|เป็น)?',
    r'ปัญหา(?:ใน|ด้าน|เรื่อง)',
    r'ความยุติธรรม(?:เป็น|คือ)',
    r'ความลับ(?:ที่)?',
    r'คำจำกัดความ(?:ของ)?',
    r'ชื่อ(?:เครื่องมือ|โมเดล|ฟังก์ชัน|พารามิเตอร์)?(?:ต้อง|ควร|มี)',
    r'กฎ(?:เช่น|ที่|สิทธิ์|ข้อกำหนด|ความปลอดภัย)',
    r'ข้อความ(?:ใดก็ตาม|ที่สร้างขึ้น|ตอบกลับ)',
    r'แพลตฟอร์ม(?:ที่|จะ)?',
    r'เครื่องมือ(?:ที่|นี้|จะ|มากเกินไป)',
    r'ทั้งสอง(?:ฝ่าย|อย่าง|วิธี)?(?:ต่างกัน|แตกต่าง)',
    r'สถาปัตยกรรม(?:ที่)?',
    r'เกตเวย์(?:จัดการ|นี้)?',
    r'โค้ด(?:แอปพลิเคชัน|ของคุณ)?(?:จะ)?',
    r'สถานการณ์(?:แรก|ที่สอง|ที่สาม|สุดท้าย)(?:คือ)?',
    r'แทนที่จะ(?:ทําเช่นนั้น|ทำเช่นนั้น)?',
    
    # Connectives & Adverbs
    r'นอกจากนี้', r'อย่างไรก็ตาม', r'ตัวอย่างเช่น', r'ในทางกลับกัน', r'ในขณะเดียวกัน',
    r'อันที่จริง', r'โดยสรุป', r'ท้ายที่สุด', r'นอกเหนือจาก(?:นั้น|พวกเขา|นี้)',
    r'โดย(?:ปกติแล้ว|ทั่วไปแล้ว|ค่าเริ่มต้น|อัตโนมัติ|ธรรมชาติ)',
    r'ดังนั้น', r'ทั้งนี้',
    r'(?<!หลัง)จากนั้น(?:จะ|ก็)?',
    
    # Prepositional & Temporal
    r'ใน\s*(?:TypeScript|Python|กรณี|บทเรียน|การรัน|การวิจัย|สตรีม|ระบบ|เซสชัน|ที่สุด)',
    r'สำหรับ\s*(?:แอปพลิเคชัน|งาน|กรณี|ระบบ|โมเดล|เอเจนต์|ผู้ใช้|การ|สิ่งนั้น|ข้อมูลนี้|สิ่งนี้)',
    r'สําหรับ\s*(?:แอปพลิเคชัน|งาน|กรณี|ระบบ|โมเดล|เอเจนต์|ผู้ใช้|การ|สิ่งนั้น|ข้อมูลนี้|สิ่งนี้)',
    r'ภายใต้\s*(?:การ|โหมด|สภาวะ|auto)',
    r'เมื่อ\s*(?:รันไทม์|คุณ|นักพัฒนา|โมเดล|ระบบ|เซสชัน|เกิด|งาน|ID|โค้ด|เครื่องมือ|ข้อมูล|ได้รับ)',
    r'หาก\s*(?:คุณ|นักพัฒนา|โมเดล|ระบบ|เพื่อนร่วมงาน|ผลลัพธ์|ต้องการ|ค่า|ไม่มี|ID|โค้ด|เครื่องมือ|เซสชัน|ข้อมูล)',
    r'ถ้า\s*(?:คุณ|นักพัฒนา|โมเดล|ระบบ|ID|โค้ด|เครื่องมือ|เซสชัน|ข้อมูล)',
    r'เนื่องจาก\s*(?:เวิร์กโฟลว์|ระบบ|โมเดล|เอเจนต์|การ)?',
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
    if any(prefix.endswith(c) for c in ['และ', 'หรือ', 'แต่', 'ว่า', 'โดย', 'เพื่อ', 'ซึ่ง', 'กับ', 'รวมถึง', ' ให้', 'ยังมี', 'เพื่อให้', 'โดยที่', 'และใน', 'แต่ใน', 'ที่อยู่', 'รอบๆ']):
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
    p_th = re.sub(r'^(?:กับดักการสอบ|Exam Trap:?\s*)(.+)$', r'⚠️ จุดที่ข้อสอบชอบหลอก: \1', p_th)
    p_th = re.sub(r'^(?:คาดการณ์ก่อน|Predict First:?\s*)(.+)$', r'🔮 คาดการณ์ก่อนตอบ: \1', p_th)

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
        lead_topic_pat = re.compile(
            r'^((?:งานแบบแบตช์|จอแสดงผลความคืบหน้า|UI\s*แบบสด|ใน\s+[A-Za-z]+|ประการ(?:แรก|ที่สอง|ที่สาม|สุดท้าย)|ตัวแทน|เอเจนต์(?:ย่อย)?|เวิร์กโฟลว์|การวิจัย|การค้นหา|การทดสอบ|การประเมิน|การแยกบริบท|การเฉพาะทาง|การจัดการ|การควบคุม|ความแตกต่าง|ผลลัพธ์|ต้นทุน|ข้อกำหนด|เป้าหมาย|กฎการออกแบบ|สคีมา|หน้าต่างบริบท|โมเดล|ระบบ|ไคลเอ็นต์|เซิร์ฟเวอร์))'
            r'[:\s]*(.*)$'
        )
        for pt in normal_points:
            m_colon = re.match(r'^([^:]{2,35}):\s*(.+)$', pt)
            if m_colon:
                term, desc = m_colon.group(1), m_colon.group(2)
                pt_fmt = f'<strong class="text-indigo-300 font-semibold">{highlight_tech_terms(term)}:</strong> <span class="text-slate-200">{highlight_tech_terms(desc)}</span>'
            else:
                m_lead = lead_topic_pat.match(pt)
                if m_lead and len(m_lead.group(2).strip()) > 3:
                    head, rest = m_lead.group(1), m_lead.group(2).strip()
                    pt_fmt = f'<strong class="text-indigo-300 font-semibold">{head}:</strong> <span class="text-slate-200">{highlight_tech_terms(rest)}</span>'
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