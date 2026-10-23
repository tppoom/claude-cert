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

def split_thai_sentences(text):
    text = clean_thai_spacing(text)
    starters = [
        r'(?<!ที่)(?<!ซึ่ง)คุณ(?:เขียน|สามารถ|ไม่|ต้อง|จะ|กำหนด|เลือก|ส่ง)',
        r'(?<!ที่)(?<!ซึ่ง)โมเดล(?:จะ|สามารถ|ต้อง|ให้)',
        r'(?<!ที่)(?<!ซึ่ง)ระบบ(?:จะ|สามารถ|มี)',
        r'(?<!ที่)(?<!ซึ่ง)เอเจนต์(?:จะ|สามารถ|ทุก)',
        r'บริการนี้(?:เหมาะ|ช่วย|จะ)',
        r'(?:การควบคุม|ข้อแตกต่าง|จุดประสงค์|จุดเด่น|ข้อดี|ข้อสังเกต|เป้าหมาย|ผลลัพธ์|สิ่งสำคัญ)คือ',
        r'ดังนั้น', r'นอกจากนี้', r'อย่างไรก็ตาม', r'ตัวอย่างเช่น', r'ในทางกลับกัน', r'ในขณะเดียวกัน',
        r'แต่ละ(?:ตัวเลือก|ขั้นตอน|แบบ|รุ่น)',
        r'(?:หาก|ถ้า|เมื่อ)คุณ', r'เมื่อรันไทม์'
    ]
    pat_str = '|'.join(starters)
    spaced = re.sub(rf'([ก-๙\)])(?=(?:{pat_str}))\s*', r'\1  ', text)
    raw_parts = [p.strip() for p in re.split(r'\s{2,}|\.\s+', spaced) if p.strip()]
    merged = []
    for p in raw_parts:
        if merged and len(merged[-1]) < 40:
            merged[-1] = merged[-1] + ' ' + p
        else:
            merged.append(p)
    return merged

def format_readable_content(p_th, p_raw, is_first_para=False):
    p_th = p_th.strip()
    if not p_th:
        return ""
    p_th = clean_thai_spacing(p_th)
    
    # Clean glued exam labels
    p_th = re.sub(r'^(?:กับดักการสอบ|Exam Trap:?\s*)(.+)$', r'⚠️ จุดที่ข้อสอบชอบหลอก: \1', p_th)
    p_th = re.sub(r'^(?:คาดการณ์ก่อน|Predict First:?\s*)(.+)$', r'🔮 คาดการณ์ก่อนตอบ: \1', p_th)

    # 1. Bullet list inside paragraph (e.g. "- ตัวแทน: โมเดล... - สภาพแวดล้อม: ที่ที่...")
    bullet_parts = [b.strip().lstrip('-•* \t') for b in re.split(r'(?:^|\s+)[-•*]\s+', p_th) if b.strip().lstrip('-•* \t')]
    if len(bullet_parts) >= 2:
        lis = ""
        for bp in bullet_parts:
            m_colon = re.match(r'^([^:]{2,30}):\s*(.+)$', bp)
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

    # 2. Lead Concept Card (First paragraph of section)
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

    # 3. Colon definition card (starts with 'Concept: ...')
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

    # 4. Long paragraph with multiple sentences -> format into spaced sub-paragraphs
    sents = split_thai_sentences(p_th)
    if len(sents) >= 2 and len(p_th) > 150:
        paras_html = "".join(f'<p class="text-slate-300 text-sm sm:text-[15px] leading-relaxed sm:leading-loose my-2.5">{highlight_tech_terms(s)}</p>' for s in sents)
        return f'<div class="my-4 space-y-2 p-1">{paras_html}</div>'

    # 5. Standard paragraph
    return f"""
    <p class="text-slate-300 text-sm sm:text-[15px] leading-relaxed sm:leading-loose my-3.5">
      {highlight_tech_terms(p_th)}
    </p>
    """
