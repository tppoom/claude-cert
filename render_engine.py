import os, sys, json, re, html, hashlib
from quiz_translator import get_thai_explanation, clean_thai_spacing
from rich_formatter import highlight_tech_terms, split_thai_sentences

# Common Technical Dictionary for Anthropic Claude Systems
TERM_MAP = [
    (r"\bautonomy ladder\b", "บันไดระดับความเป็นอิสระ (Autonomy Ladder)"),
    (r"\borchestrator-subagent\b", "Orchestrator-Subagent (ผู้ประสานงานและเอเจนต์ย่อย)"),
    (r"\borchestrator–subagent\b", "Orchestrator-Subagent (ผู้ประสานงานและเอเจนต์ย่อย)"),
    (r"\bprompt chaining\b", "Prompt Chaining (การส่งต่อผลลัพธ์เป็นลูกโซ่)"),
    (r"\brouting workflow\b", "Routing Workflow (เวิร์กโฟลว์การกระจายงานตามเงื่อนไข)"),
    (r"\bparallelization\b", "Parallelization (การประมวลผลพร้อมกัน)"),
    (r"\bevaluator-optimizer\b", "Evaluator-Optimizer (วงรอบการประเมินและปรับปรุง)"),
    (r"\bcontext window budget\b", "Context Window Budget (งบประมาณโทเค็นของบริบท)"),
    (r"\btool output pruning\b", "Tool Output Pruning (การตัดทอนผลลัพธ์เครื่องมือเพื่อประหยัดบริบท)"),
    (r"\bprompt caching\b", "Prompt Caching (การแคชพร้อมต์เพื่อลดต้นทุนและความหน่วง)"),
    (r"\bextended thinking\b", "Extended Thinking (โหมดการคิดเชิงลึกของ Claude)"),
    (r"\bthinking budget\b", "Thinking Budget (งบประมาณโทเค็นสำหรับการคิด)"),
    (r"\bfast mode\b", "Fast Mode (โหมดความเร็วสูง)"),
    (r"\bmodel context protocol\b", "Model Context Protocol (เกณฑ์วิธีบริบทโมเดล MCP)"),
    (r"\bpretooluse\b", "PreToolUse hook (ฮุกตรวจความถูกต้องก่อนเรียกเครื่องมือ)"),
    (r"\bcontext isolation\b", "Context Isolation (การแยกบริบทระหว่างเอเจนต์)"),
    (r"\bcapability bloat\b", "Capability Bloat (การใส่เครื่องมือมากเกินไปจนลดทอนความแม่นยำ)"),
    (r"\bcontent policy\b", "Content Policy (นโยบายเนื้อหาความปลอดภัย)"),
    (r"\bprompt injection\b", "Prompt Injection (การแทรกคำสั่งแปลกปลอมในพร้อมต์)"),
    (r"\bjailbreak\b", "Jailbreak (การหลอกข้ามการป้องกันของโมเดล)"),
    (r"\bworkload identity federation\b", "Workload Identity Federation (การยืนยันตัวตนภายนอกแบบไร้คีย์)"),
]

def thai_format_text(text):
    if not text: return ""
    res = text
    for pat, rep in TERM_MAP:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return clean_thai_spacing(res)

def format_multiline_thai(th_text, theme="indigo"):
    if not th_text:
        return ""
    sents = split_thai_sentences(th_text)
    if len(sents) > 1:
        bullet_color = "text-amber-400" if theme == "amber" else "text-indigo-400"
        text_color = "text-amber-200/90" if theme == "amber" else "text-indigo-200/90"
        lis = "".join(f'<li class="flex items-start gap-2 {text_color} leading-relaxed"><span class="{bullet_color} font-bold shrink-0 mt-0.5">▸</span><div class="grow">{highlight_tech_terms(s)}</div></li>' for s in sents)
        return f'<ul class="space-y-1.5 mt-1">{lis}</ul>'
    else:
        return f'<div class="mt-0.5 font-sans leading-relaxed">{highlight_tech_terms(th_text)}</div>'

def generate_section_deep_dive(heading, items, domain_title=""):
    return ""

def render_predict_first_html(item, idx):
    qid = f"pred_{hashlib.md5(item.get('prompt', '').encode('utf-8')).hexdigest()[:8]}"
    prompt_raw = item.get("prompt", "")
    prompt_th = get_thai_explanation(prompt_raw)
    options = [clean_thai_spacing(opt) for opt in item.get("options", [])]
    correct_idx = item.get("correct_index", 0)
    opt_letters = ["A", "B", "C", "D", "E"]
    correct_letter = opt_letters[correct_idx] if correct_idx < len(opt_letters) else "A"
    
    explanation_raw = item.get("explanation", "")
    explanation_th = get_thai_explanation(explanation_raw)
    quote = item.get("quote", "")
    quote_th = get_thai_explanation(quote) if quote else ""
    citation_url = item.get("citation_url", "")
    
    opt_html = ""
    for i, opt in enumerate(options):
        let = opt_letters[i] if i < len(opt_letters) else str(i)
        opt_th = get_thai_explanation(opt)
        opt_html += f"""
        <button type="button"
                class="quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-slate-800 hover:border-amber-500/50 transition-all text-slate-200 text-sm select-none cursor-pointer"
                id="opt-{qid}-{let}"
                data-qid="{qid}"
                data-opt="{let}"
                onclick="handleQuizAnswer('{qid}', '{let}')">
          <span class="opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0 transition-colors">{let}</span>
          <div class="leading-relaxed mt-0.5 grow">
            <span class="text-sm font-semibold text-white block">{html.escape(opt)}</span>
            <span class="text-xs text-amber-200/80 block mt-1 leading-normal font-sans">{highlight_tech_terms(opt_th)}</span>
          </div>
          <span class="opt-icon ml-2 shrink-0 font-bold text-sm hidden"></span>
        </button>
        """
        
    quote_html = ""
    if quote:
        quote_html = f"""
        <blockquote class="my-3 p-3 rounded-lg border-l-4 border-amber-500 bg-amber-950/30 text-xs sm:text-sm text-amber-200 leading-relaxed italic">
          “{html.escape(quote)}”
          {f'<div class="mt-1 text-[11px] text-amber-300/80 not-italic">คำแปล: {highlight_tech_terms(quote_th)}</div>' if quote_th else ''}
          {f'<div class="mt-1.5 not-italic"><a href="{citation_url}" target="_blank" class="underline text-amber-400 hover:text-amber-300 font-mono text-xs">🔗 Source: {citation_url}</a></div>' if citation_url else ''}
        </blockquote>
        """
        
    return f"""
    <div class="quiz-card my-8 rounded-2xl border border-amber-500/40 bg-slate-900/90 p-5 sm:p-6 shadow-xl backdrop-blur"
         id="quiz-{qid}"
         data-qid="{qid}"
         data-correct="{correct_letter}">
      <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
        <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-amber-400 uppercase">
          <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-300">💡</span>
          <span>คำถามท้าทายความคิดก่อนอ่านเนื้อหา (Predict First Challenge)</span>
        </div>
        <div class="flex items-center gap-2">
          <span id="status-badge-{qid}" class="hidden px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">✓ ตอบถูกแล้ว</span>
          <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">Predict</span>
        </div>
      </div>
      
      <div class="mb-4 space-y-2">
        <p class="text-base sm:text-lg font-semibold text-white leading-relaxed">{html.escape(prompt_raw)}</p>
        <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-amber-200/90 leading-relaxed">
          <span class="text-amber-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลโจทย์:</span>
          {format_multiline_thai(prompt_th, "amber")}
        </div>
      </div>
      
      <div class="space-y-2.5 mb-3" id="options-{qid}">
        {opt_html}
      </div>
      
      <div id="feedback-{qid}" class="hidden my-3 p-3.5 rounded-xl text-xs sm:text-sm transition-all duration-200"></div>
      
      <div id="solution-{qid}" class="hidden mt-4 pt-4 border-t border-slate-800 space-y-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">คำตอบที่ถูกต้อง:</span>
          <span class="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-sm">ตัวเลือก {correct_letter}</span>
        </div>
        <div class="p-4 rounded-xl bg-amber-950/30 border border-amber-900/50 text-xs sm:text-sm text-slate-200 space-y-2.5">
          <strong class="text-amber-300 block text-xs uppercase tracking-wider">💡 Official Explanation (คำอธิบายเฉลย):</strong>
          <p class="text-slate-100 font-medium leading-relaxed text-sm sm:text-base">{html.escape(explanation_raw)}</p>
          <div class="pt-2 border-t border-amber-900/40 text-xs sm:text-sm text-amber-200/90 leading-relaxed">
            <span class="text-amber-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลไทย:</span>
            {format_multiline_thai(explanation_th, "amber")}
          </div>
          {quote_html}
        </div>
      </div>
      
      <div class="flex items-center justify-between pt-2">
        <button type="button" onclick="toggleSolutionManual('{qid}')" class="text-xs text-amber-400 hover:text-amber-300 underline font-medium cursor-pointer">
          ดูเฉลยและคำอธิบาย
        </button>
        <span class="text-[11px] text-slate-400">คลิกเลือกคำตอบได้จนกว่าจะถูกต้อง · บันทึกผลใน LocalStorage</span>
      </div>
    </div>
    """

def render_checkpoint_html(key, block_data, question_data):
    opt_letters = ["A", "B", "C", "D", "E"]
    
    # 1. Official Exam Question
    if question_data:
        q = question_data
        qid = str(q.get("id", ""))
        stem_raw = q.get("question", "")
        stem_th = get_thai_explanation(stem_raw)
        options = [clean_thai_spacing(opt) for opt in q.get("options", [])]
        correct_answers = q.get("correct_answers", ["A"])
        explanations = q.get("explanations", [])
        
        opt_html = ""
        for i, opt in enumerate(options):
            let = opt_letters[i] if i < len(opt_letters) else str(i)
            opt_th = get_thai_explanation(opt)
            opt_html += f"""
            <button type="button"
                    class="quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-slate-800 hover:border-indigo-500/50 transition-all text-slate-200 text-sm select-none cursor-pointer"
                    id="opt-{qid}-{let}"
                    data-qid="{qid}"
                    data-opt="{let}"
                    onclick="handleQuizAnswer('{qid}', '{let}')">
              <span class="opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0 transition-colors">{let}</span>
              <div class="leading-relaxed mt-0.5 grow">
                <span class="text-sm font-semibold text-white block">{html.escape(opt)}</span>
                <span class="text-xs text-indigo-300/80 block mt-1 leading-normal font-sans">{highlight_tech_terms(opt_th)}</span>
              </div>
              <span class="opt-icon ml-2 shrink-0 font-bold text-sm hidden"></span>
            </button>
            """
            
        exp_html = ""
        for exp in explanations:
            let = exp.get("option", "")
            e_text = exp.get("explanation", "")
            e_text_th = get_thai_explanation(e_text)
            is_c = let in correct_answers
            badge = '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-xs font-semibold">✓ คำตอบที่ถูกต้อง</span>' if is_c else '<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-xs">ตัวเลือกที่ไม่ถูกต้อง</span>'
            border_cls = "border-emerald-500/30 bg-emerald-950/20" if is_c else "border-slate-800/80 bg-slate-900/40"
            exp_html += f"""
            <div class="p-3.5 rounded-lg border {border_cls} space-y-2">
              <div class="flex items-center gap-2">
                <span class="font-bold text-slate-200 text-xs">ตัวเลือก {let}:</span>
                {badge}
              </div>
              <p class="text-slate-100 text-xs sm:text-sm font-medium leading-relaxed">{html.escape(e_text)}</p>
              <div class="pt-1.5 border-t border-slate-800/60 text-xs text-indigo-200/90 leading-relaxed">
                <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปล:</span>
                {format_multiline_thai(e_text_th, "indigo")}
              </div>
            </div>
            """
            
        correct_str = ", ".join(correct_answers)
        return f"""
        <div class="quiz-card my-8 rounded-2xl border border-indigo-500/40 bg-slate-900/95 p-5 sm:p-6 shadow-xl backdrop-blur"
             id="quiz-{qid}"
             data-qid="{qid}"
             data-correct="{correct_str}">
          <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
            <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-indigo-400 uppercase">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300">📝</span>
              <span>ข้อสอบจำลองทางการ (Official Exam Question)</span>
            </div>
            <div class="flex items-center gap-2">
              <span id="status-badge-{qid}" class="hidden px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">✓ ตอบถูกแล้ว</span>
              <span class="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">ID: {qid}</span>
            </div>
          </div>
          
          <div class="mb-4 space-y-2">
            <p class="text-base sm:text-lg font-semibold text-white leading-relaxed">{html.escape(stem_raw)}</p>
            <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-indigo-200/90 leading-relaxed">
              <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลโจทย์:</span>
              {format_multiline_thai(stem_th, "indigo")}
            </div>
          </div>
          
          <div class="space-y-2.5 mb-3" id="options-{qid}">
            {opt_html}
          </div>
          
          <div id="feedback-{qid}" class="hidden my-3 p-3.5 rounded-xl text-xs sm:text-sm transition-all duration-200"></div>
          
          <div id="solution-{qid}" class="hidden mt-4 pt-4 border-t border-slate-800 space-y-3">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">คำตอบที่ถูกต้อง:</span>
              <span class="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-sm">ตัวเลือก {correct_str}</span>
            </div>
            <div class="p-4 rounded-xl bg-indigo-950/40 border border-indigo-900/60 text-xs sm:text-sm text-slate-200 space-y-3">
              <strong class="text-indigo-300 block text-xs uppercase tracking-wider">💡 Option Analysis (คำอธิบายเฉลยรายตัวเลือก):</strong>
              <div class="space-y-2">
                {exp_html}
              </div>
            </div>
          </div>
          
          <div class="flex items-center justify-between pt-2">
            <button type="button" onclick="toggleSolutionManual('{qid}')" class="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium cursor-pointer">
              ดูเฉลยและคำอธิบาย
            </button>
            <span class="text-[11px] text-slate-400">คลิกเลือกคำตอบได้จนกว่าจะถูกต้อง · บันทึกผลใน LocalStorage</span>
          </div>
        </div>
        """
        
    # 2. Checkpoint Block
    elif block_data:
        b = block_data
        bid = str(b.get("id", key.replace("check:", "")))
        b_type = b.get("type", "choice")
        prompt_raw = b.get("prompt", "")
        prompt_th = get_thai_explanation(prompt_raw)
        explanation_raw = b.get("explanation", "")
        explanation_th = get_thai_explanation(explanation_raw)
        citation = b.get("citation", {})
        
        cit_html = ""
        if citation and citation.get("quote"):
            quote_raw = citation.get("quote", "")
            quote_th = get_thai_explanation(quote_raw)
            cit_html = f"""
            <div class="mt-3 pt-2.5 border-t border-slate-800 text-xs text-slate-300 italic">
              “{html.escape(quote_raw)}”
              {f'<div class="mt-1 text-[11px] text-indigo-300/80 not-italic">คำแปล: {highlight_tech_terms(quote_th)}</div>' if quote_th else ''}
              <br><a href="{citation.get('sourceUrl', '#')}" target="_blank" class="underline text-indigo-400 not-italic font-sans mt-1 inline-block">🔗 เอกสารอ้างอิงทางการจาก Anthropic</a>
            </div>
            """

        # --- Subtype 1: MATCHING CHALLENGE ---
        if b_type == "match":
            pairs = b.get("pairs", [])
            total_pairs = len(pairs)
            
            # Deterministic shuffle for definitions so terms and defs are not aligned
            import random
            rng = random.Random(bid)
            shuffled_defs = list(enumerate(pairs))
            rng.shuffle(shuffled_defs)
            
            terms_html = ""
            for idx, p in enumerate(pairs):
                term_en = p.get("term", "")
                term_th = get_thai_explanation(term_en)
                terms_html += f"""
                <button type="button"
                        id="match-term-{bid}-{idx}"
                        data-term-idx="{idx}"
                        class="match-term-btn w-full text-left p-3.5 rounded-xl border border-slate-700/80 bg-slate-800/60 hover:border-indigo-400 hover:bg-slate-800 text-slate-200 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-2.5 shadow-sm"
                        onclick="handleMatchClick('{bid}', 'term', {idx}, {total_pairs})">
                  <span id="match-badge-term-{bid}-{idx}" class="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 rounded-lg bg-indigo-500/20 text-indigo-300 font-bold text-xs shrink-0 mt-0.5">{idx+1}</span>
                  <div class="leading-relaxed grow">
                    <span class="text-xs sm:text-sm font-bold text-white block">{html.escape(term_en)}</span>
                    <span class="text-[11px] text-indigo-300/80 block mt-0.5 font-sans">{highlight_tech_terms(term_th)}</span>
                  </div>
                </button>
                """
                
            defs_html = ""
            for slot_idx, (orig_idx, p) in enumerate(shuffled_defs):
                def_en = p.get("definition", "")
                def_th = get_thai_explanation(def_en)
                defs_html += f"""
                <button type="button"
                        id="match-def-{bid}-{orig_idx}"
                        data-def-idx="{orig_idx}"
                        class="match-def-btn w-full text-left p-3.5 rounded-xl border border-slate-700/80 bg-slate-800/60 hover:border-indigo-400 hover:bg-slate-800 text-slate-200 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-2.5 shadow-sm"
                        onclick="handleMatchClick('{bid}', 'def', {orig_idx}, {total_pairs})">
                  <span id="match-badge-def-{bid}-{orig_idx}" class="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 rounded-lg bg-slate-700 text-slate-300 font-bold text-xs shrink-0 mt-0.5">?</span>
                  <div class="leading-relaxed grow">
                    <span class="text-xs sm:text-sm font-semibold text-slate-100 block">{html.escape(def_en)}</span>
                    <span class="text-[11px] text-indigo-200/80 block mt-1 leading-normal font-sans">{highlight_tech_terms(def_th)}</span>
                  </div>
                </button>
                """
                
            verified_pairs_html = ""
            for idx, p in enumerate(pairs):
                term_en = p.get("term", "")
                term_th = get_thai_explanation(term_en)
                def_en = p.get("definition", "")
                def_th = get_thai_explanation(def_en)
                verified_pairs_html += f"""
                <div class="p-3.5 rounded-xl border border-indigo-500/30 bg-indigo-950/20 space-y-2 text-xs sm:text-sm">
                  <div class="font-bold text-white flex items-center gap-2">
                    <span class="inline-flex items-center justify-center w-5 h-5 rounded bg-indigo-500/30 text-indigo-200 text-xs font-bold shrink-0">{idx+1}</span>
                    <span class="font-bold text-white text-sm">{html.escape(term_en)}</span>
                    <span class="text-xs text-indigo-300/80 font-sans">({highlight_tech_terms(term_th)})</span>
                  </div>
                  <div class="ml-7 pl-3 border-l-2 border-indigo-500/40 leading-relaxed space-y-1">
                    <span class="text-emerald-300 font-medium block">➔ {html.escape(def_en)}</span>
                    <span class="text-xs text-indigo-200/85 block font-sans">{highlight_tech_terms(def_th)}</span>
                  </div>
                </div>
                """
                
            return f"""
            <div class="quiz-card my-8 rounded-2xl border border-indigo-500/30 bg-slate-900/90 p-5 sm:p-6 shadow-xl backdrop-blur"
                 id="quiz-{bid}"
                 data-qid="{bid}"
                 data-correct="MATCH"
                 data-total-pairs="{total_pairs}">
              <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
                <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-indigo-400 uppercase">
                  <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300">🔄</span>
                  <span>แบบฝึกหัดจับคู่ความสัมพันธ์ (Matching Challenge)</span>
                </div>
                <div class="flex items-center gap-2">
                  <span id="status-badge-{bid}" class="hidden px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">✓ ตรวจสอบแล้ว</span>
                  <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">Match ({total_pairs} คู่)</span>
                </div>
              </div>
              
              <div class="mb-4 space-y-2">
                <p class="text-base sm:text-lg font-semibold text-white leading-relaxed">{html.escape(prompt_raw)}</p>
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-indigo-200/90 leading-relaxed">
                  <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลโจทย์:</span>
                  {format_multiline_thai(prompt_th, "indigo")}
                </div>
              </div>

              <!-- Interactive Matching Board -->
              <div class="my-4 p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-3">
                <div class="text-xs text-indigo-300 font-medium flex items-center justify-between pb-2 border-b border-slate-800">
                  <span class="flex items-center gap-1.5"><span>👉</span><span>คำแนะนำ: คลิกเลือกคำศัพท์ฝั่งซ้ายหรือคำอธิบายฝั่งขวาเพื่อจับคู่ (คลิกคู่ที่จับแล้วเพื่อยกเลิกได้)</span></span>
                  <span id="match-counter-{bid}" class="text-slate-400 font-mono">จับคู่ได้ 0/{total_pairs} คู่</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  <!-- Terms (Left) -->
                  <div class="space-y-2.5">
                    <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">1. รายการคำศัพท์ / หัวข้อ:</div>
                    {terms_html}
                  </div>
                  <!-- Definitions (Right) -->
                  <div class="space-y-2.5">
                    <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">2. คำอธิบาย / ความหมาย (สลับตำแหน่ง):</div>
                    {defs_html}
                  </div>
                </div>
              </div>

              <!-- Feedback Banner -->
              <div id="feedback-{bid}" class="hidden my-3 p-3.5 rounded-xl text-xs sm:text-sm transition-all duration-200"></div>

              <!-- Controls -->
              <div class="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div class="flex items-center gap-3">
                  <button type="button"
                          onclick="resetMatchGame('{bid}')"
                          class="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5">
                    <span>🔄</span>
                    <span>เริ่มจับคู่ใหม่ (Reset)</span>
                  </button>
                  <button type="button"
                          onclick="toggleSolutionManual('{bid}')"
                          class="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium cursor-pointer">
                    ดูเฉลยคู่ความสัมพันธ์
                  </button>
                </div>
                <span class="text-[11px] text-slate-400">จับคู่ให้ครบทุกข้อเพื่อบันทึกผลสำเร็จอัตโนมัติ</span>
              </div>
              
              <!-- Solution Box -->
              <div id="solution-{bid}" class="hidden mt-4 pt-4 border-t border-slate-800 space-y-3">
                <strong class="text-indigo-300 block text-xs uppercase tracking-wider">✓ Verified Pairs (เฉลยคู่ความสัมพันธ์ที่ถูกต้อง):</strong>
                <div class="space-y-2.5">
                  {verified_pairs_html}
                </div>
                <div class="mt-3 p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs sm:text-sm text-slate-200 space-y-2">
                  <strong class="text-indigo-300 block text-xs uppercase tracking-wider">💡 Key Takeaway (หลักการสำคัญ):</strong>
                  <p class="text-slate-100 font-medium leading-relaxed">{html.escape(explanation_raw)}</p>
                  <div class="pt-1.5 border-t border-slate-700/60 text-xs text-indigo-200/90 leading-relaxed">
                    <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลไทย:</span>
                    {format_multiline_thai(explanation_th, "indigo")}
                  </div>
                  {cit_html}
                </div>
              </div>
            </div>
            """

        # --- Subtype 2: ORDER / SEQUENCING CHALLENGE ---
        elif b_type == "order":
            steps = b.get("steps", [])
            total_steps = len(steps)
            
            # Scramble steps deterministically
            import random
            rng = random.Random(bid)
            scrambled = list(enumerate(steps))
            rng.shuffle(scrambled)
            
            scrambled_html = ""
            for slot_idx, (orig_idx, s) in enumerate(scrambled):
                s_th = get_thai_explanation(s)
                scrambled_html += f"""
                <div class="order-step-item flex items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-700/80 bg-slate-800/60 text-slate-200 transition-all shadow-sm"
                     id="order-item-{bid}-{orig_idx}"
                     data-orig-idx="{orig_idx}">
                  <div class="flex items-start gap-3 grow min-w-0">
                    <span class="order-rank-badge inline-flex items-center justify-center min-w-[32px] h-8 px-2 rounded-lg bg-slate-700/80 text-slate-200 font-mono font-bold text-xs shrink-0 select-none mt-0.5">{slot_idx + 1}</span>
                    <div class="leading-relaxed min-w-0">
                      <span class="text-xs sm:text-sm font-bold text-white block leading-relaxed">{html.escape(s)}</span>
                      <span class="text-xs text-indigo-300/80 block mt-1 leading-normal font-sans">{highlight_tech_terms(s_th)}</span>
                    </div>
                  </div>
                  <div class="flex flex-col gap-1 shrink-0 ml-1">
                    <button type="button"
                            title="เลื่อนขึ้น (Move Up)"
                            class="order-move-up-btn w-8 h-8 rounded-lg bg-slate-700/70 hover:bg-indigo-600 active:scale-95 text-slate-300 hover:text-white flex items-center justify-center text-xs font-bold transition cursor-pointer"
                            onclick="moveOrderStep('{bid}', this, -1)">▲</button>
                    <button type="button"
                            title="เลื่อนลง (Move Down)"
                            class="order-move-down-btn w-8 h-8 rounded-lg bg-slate-700/70 hover:bg-indigo-600 active:scale-95 text-slate-300 hover:text-white flex items-center justify-center text-xs font-bold transition cursor-pointer"
                            onclick="moveOrderStep('{bid}', this, 1)">▼</button>
                  </div>
                </div>
                """
                
            verified_steps_html = ""
            for idx, s in enumerate(steps):
                s_th = get_thai_explanation(s)
                verified_steps_html += f"""
                <div class="p-3 rounded-xl border border-indigo-500/30 bg-indigo-950/20 flex items-start gap-3">
                  <span class="inline-flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-600 text-white text-xs font-bold shrink-0 mt-0.5">{idx+1}</span>
                  <div class="leading-relaxed text-xs sm:text-sm space-y-1">
                    <span class="text-white font-semibold block">{html.escape(s)}</span>
                    <span class="text-xs text-indigo-200/90 block font-sans">{highlight_tech_terms(s_th)}</span>
                  </div>
                </div>
                """
                
            return f"""
            <div class="quiz-card my-8 rounded-2xl border border-indigo-500/30 bg-slate-900/90 p-5 sm:p-6 shadow-xl backdrop-blur"
                 id="quiz-{bid}"
                 data-qid="{bid}"
                 data-correct="ORDER"
                 data-total-steps="{total_steps}">
              <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
                <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-indigo-400 uppercase">
                  <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300">🔢</span>
                  <span>แบบฝึกหัดเรียงลำดับขั้นตอน (Step Sequencing)</span>
                </div>
                <div class="flex items-center gap-2">
                  <span id="status-badge-{bid}" class="hidden px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">✓ ตอบถูกแล้ว</span>
                  <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">Order ({total_steps} ขั้นตอน)</span>
                </div>
              </div>
              
              <div class="mb-4 space-y-2">
                <p class="text-base sm:text-lg font-semibold text-white leading-relaxed">{html.escape(prompt_raw)}</p>
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-indigo-200/90 leading-relaxed">
                  <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลโจทย์:</span>
                  {format_multiline_thai(prompt_th, "indigo")}
                </div>
              </div>

              <!-- Interactive Step Ordering Board -->
              <div class="my-4 p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-3">
                <div class="text-xs text-indigo-300 font-medium flex items-center justify-between pb-2 border-b border-slate-800">
                  <span class="flex items-center gap-1.5"><span>👉</span><span>คำแนะนำ: กดปุ่ม ▲ หรือ ▼ บนการ์ดเพื่อสลับเรียงลำดับขั้นตอนที่ถูกต้องจาก 1 ถึง {total_steps} แล้วกด "ตรวจคำตอบ"</span></span>
                  <span class="text-slate-400 font-mono">ทั้งหมด {total_steps} ขั้นตอน</span>
                </div>
                <div class="space-y-2.5 pt-1" id="order-cards-{bid}">
                  {scrambled_html}
                </div>
              </div>

              <!-- Feedback Banner -->
              <div id="feedback-{bid}" class="hidden my-3 p-3.5 rounded-xl text-xs sm:text-sm transition-all duration-200"></div>

              <!-- Controls -->
              <div class="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div class="flex items-center gap-3">
                  <button type="button"
                          onclick="checkOrderSequence('{bid}', {total_steps})"
                          class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs sm:text-sm shadow-md transition cursor-pointer flex items-center gap-2">
                    <span>✓</span>
                    <span>ตรวจคำตอบ (Check Order)</span>
                  </button>
                  <button type="button"
                          onclick="resetOrderGame('{bid}')"
                          class="px-3 py-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5">
                    <span>🔄</span>
                    <span>คืนค่าเริ่มต้น (Reset)</span>
                  </button>
                </div>
                <button type="button"
                        onclick="toggleSolutionManual('{bid}')"
                        class="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium cursor-pointer">
                  ดูเฉลยลำดับที่ถูกต้อง
                </button>
              </div>
              
              <!-- Solution Box -->
              <div id="solution-{bid}" class="hidden mt-4 pt-4 border-t border-slate-800 space-y-3">
                <strong class="text-indigo-300 block text-xs uppercase tracking-wider">✓ Correct Sequence 1 ➔ {total_steps} (ลำดับขั้นตอนที่ถูกต้อง):</strong>
                <div class="space-y-2">
                  {verified_steps_html}
                </div>
                <div class="mt-3 p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs sm:text-sm text-slate-200 space-y-2">
                  <strong class="text-indigo-300 block text-xs uppercase tracking-wider">💡 Reasoning (เหตุผลเบื้องหลังลำดับขั้น):</strong>
                  <p class="text-slate-100 font-medium leading-relaxed">{html.escape(explanation_raw)}</p>
                  <div class="pt-1.5 border-t border-slate-700/60 text-xs text-indigo-200/90 leading-relaxed">
                    <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลไทย:</span>
                    {format_multiline_thai(explanation_th, "indigo")}
                  </div>
                  {cit_html}
                </div>
              </div>
            </div>
            """

        # --- Subtype 3 & 4: CHOICE & FILL (Multiple Choice) ---
        else:
            options = [clean_thai_spacing(opt) for opt in b.get("options", [])]
            ans_idx = b.get("answerIndex", 0)
            correct_letter = opt_letters[ans_idx] if ans_idx is not None and ans_idx < len(opt_letters) else "A"
            code_snippet = b.get("code", "")
            
            code_html = ""
            if code_snippet:
                code_html = f"""
                <div class="my-3 rounded-xl overflow-hidden border border-slate-800 bg-slate-950 font-mono text-xs sm:text-sm shadow-inner">
                  <pre class="p-4 text-emerald-300 overflow-x-auto leading-relaxed"><code>{html.escape(code_snippet)}</code></pre>
                </div>
                """
                
            opt_html = ""
            for i, opt in enumerate(options):
                let = opt_letters[i] if i < len(opt_letters) else str(i)
                opt_th = get_thai_explanation(opt)
                opt_html += f"""
                <button type="button"
                        class="quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-slate-800 hover:border-indigo-500/50 transition-all text-slate-200 text-sm select-none cursor-pointer"
                        id="opt-{bid}-{let}"
                        data-qid="{bid}"
                        data-opt="{let}"
                        onclick="handleQuizAnswer('{bid}', '{let}')">
                  <span class="opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0 transition-colors">{let}</span>
                  <div class="leading-relaxed mt-0.5 grow">
                    <span class="text-sm font-semibold text-white block">{html.escape(opt)}</span>
                    <span class="text-xs text-indigo-300/80 block mt-1 leading-normal font-sans">{highlight_tech_terms(opt_th)}</span>
                  </div>
                  <span class="opt-icon ml-2 shrink-0 font-bold text-sm hidden"></span>
                </button>
                """
                
            return f"""
            <div class="quiz-card my-8 rounded-2xl border border-indigo-500/30 bg-slate-900/90 p-5 sm:p-6 shadow-xl backdrop-blur"
                 id="quiz-{bid}"
                 data-qid="{bid}"
                 data-correct="{correct_letter}">
              <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
                <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-indigo-400 uppercase">
                  <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300">✓</span>
                  <span>แบบฝึกหัดตรวจสอบความเข้าใจ (Checkpoint Practice)</span>
                </div>
                <div class="flex items-center gap-2">
                  <span id="status-badge-{bid}" class="hidden px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">✓ ตอบถูกแล้ว</span>
                  <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">Check</span>
                </div>
              </div>
              
              <div class="mb-4 space-y-2">
                <p class="text-base sm:text-lg font-semibold text-white leading-relaxed">{html.escape(prompt_raw)}</p>
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs sm:text-sm text-indigo-200/90 leading-relaxed">
                  <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลโจทย์:</span>
                  {format_multiline_thai(prompt_th, "indigo")}
                </div>
              </div>
              
              {code_html}
              
              <div class="space-y-2.5 mb-3" id="options-{bid}">
                {opt_html}
              </div>
              
              <div id="feedback-{bid}" class="hidden my-3 p-3.5 rounded-xl text-xs sm:text-sm transition-all duration-200"></div>
              
              <div id="solution-{bid}" class="hidden mt-4 pt-4 border-t border-slate-800 space-y-3">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs font-semibold uppercase text-slate-400">คำตอบที่ถูกต้อง:</span>
                  <span class="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-sm">ตัวเลือก {correct_letter}</span>
                </div>
                <div class="p-4 rounded-xl bg-indigo-950/30 border border-indigo-900/50 text-xs sm:text-sm text-slate-200 space-y-2.5">
                  <strong class="text-indigo-300 block text-xs uppercase tracking-wider">💡 Official Explanation (คำอธิบายเฉลย):</strong>
                  <p class="text-slate-100 font-medium leading-relaxed text-sm sm:text-base">{html.escape(explanation_raw)}</p>
                  <div class="pt-2 border-t border-indigo-900/40 text-xs sm:text-sm text-indigo-200/90 leading-relaxed">
                    <span class="text-indigo-400 font-bold text-xs uppercase tracking-wider block mb-1">คำแปลไทย:</span>
                    {format_multiline_thai(explanation_th, "indigo")}
                  </div>
                  {cit_html}
                </div>
              </div>
              
              <div class="flex items-center justify-between pt-2">
                <button type="button" onclick="toggleSolutionManual('{bid}')" class="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium cursor-pointer">
                  ดูเฉลยและคำอธิบาย
                </button>
                <span class="text-[11px] text-slate-400">คลิกเลือกคำตอบได้จนกว่าจะถูกต้อง · บันทึกผลใน LocalStorage</span>
              </div>
            </div>
            """
    return ""

print("render_engine.py ready with full support for choice, match, order, fill, and predict_first.")
