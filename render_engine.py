import os, sys, json, re, html
from quiz_translator import get_thai_explanation, clean_thai_spacing

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

def generate_section_deep_dive(heading, items, domain_title=""):
    # Duplicate template removed completely as requested by user
    return ""

def render_checkpoint_html(key, block_data, question_data):
    opt_letters = ["A", "B", "C", "D", "E"]
    
    if question_data:
        q = question_data
        qid = str(q.get("id", ""))
        stem_raw = q.get("question", "")
        stem = clean_thai_spacing(stem_raw)
        options = [clean_thai_spacing(opt) for opt in q.get("options", [])]
        correct_answers = q.get("correct_answers", ["A"])
        explanations = q.get("explanations", [])
        
        # Build options interactive HTML
        opt_html = ""
        for i, opt in enumerate(options):
            let = opt_letters[i] if i < len(opt_letters) else str(i)
            opt_html += f"""
            <button type="button"
                    class="quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-slate-800 hover:border-indigo-500/50 transition-all text-slate-200 text-sm select-none cursor-pointer"
                    id="opt-{qid}-{let}"
                    data-qid="{qid}"
                    data-opt="{let}"
                    onclick="handleQuizAnswer('{qid}', '{let}')">
              <span class="opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0 transition-colors">{let}</span>
              <span class="opt-text leading-relaxed mt-0.5 grow">{html.escape(opt)}</span>
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
            <div class="p-3 rounded-lg border {border_cls} space-y-1.5">
              <div class="flex items-center gap-2">
                <span class="font-bold text-slate-200 text-xs">ตัวเลือก {let}:</span>
                {badge}
              </div>
              <p class="text-slate-300 text-xs sm:text-sm leading-relaxed">{html.escape(e_text_th)}</p>
              <div class="text-[11px] text-slate-400 italic font-mono pt-1">EN: {html.escape(e_text)}</div>
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
          
          <div class="mb-4">
            <p class="text-base font-medium text-slate-100 leading-relaxed">{html.escape(stem)}</p>
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
              <strong class="text-indigo-300 block text-xs uppercase tracking-wider">💡 คำอธิบายเฉลยภาษาไทยรายตัวเลือก (Option Analysis):</strong>
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
    elif block_data:
        b = block_data
        bid = str(b.get("id", key.replace("check:", "")))
        prompt_raw = b.get("prompt", "")
        prompt = clean_thai_spacing(prompt_raw)
        options = [clean_thai_spacing(opt) for opt in b.get("options", [])]
        ans_idx = b.get("answerIndex", 0)
        explanation_raw = b.get("explanation", "")
        explanation_th = get_thai_explanation(explanation_raw)
        citation = b.get("citation", {})
        correct_letter = opt_letters[ans_idx] if ans_idx is not None and ans_idx < len(opt_letters) else "A"
        
        opt_html = ""
        for i, opt in enumerate(options):
            let = opt_letters[i] if i < len(opt_letters) else str(i)
            opt_html += f"""
            <button type="button"
                    class="quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-slate-800 hover:border-indigo-500/50 transition-all text-slate-200 text-sm select-none cursor-pointer"
                    id="opt-{bid}-{let}"
                    data-qid="{bid}"
                    data-opt="{let}"
                    onclick="handleQuizAnswer('{bid}', '{let}')">
              <span class="opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0 transition-colors">{let}</span>
              <span class="opt-text leading-relaxed mt-0.5 grow">{html.escape(opt)}</span>
              <span class="opt-icon ml-2 shrink-0 font-bold text-sm hidden"></span>
            </button>
            """
            
        cit_html = ""
        if citation and citation.get("quote"):
            cit_html = f"""
            <div class="mt-3 pt-2 border-t border-slate-800 text-xs text-slate-400 italic">
              “{html.escape(clean_thai_spacing(citation.get('quote', '')))}”
              <br><a href="{citation.get('sourceUrl', '#')}" target="_blank" class="underline text-indigo-400 not-italic font-sans mt-0.5 inline-block">🔗 เอกสารอ้างอิง Anthropic</a>
            </div>
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
          
          <div class="mb-4">
            <p class="text-base font-medium text-slate-100 leading-relaxed">{html.escape(prompt)}</p>
          </div>
          
          <div class="space-y-2.5 mb-3" id="options-{bid}">
            {opt_html}
          </div>
          
          <div id="feedback-{bid}" class="hidden my-3 p-3.5 rounded-xl text-xs sm:text-sm transition-all duration-200"></div>
          
          <div id="solution-{bid}" class="hidden mt-4 pt-4 border-t border-slate-800 space-y-3">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs font-semibold uppercase text-slate-400">คำตอบที่ถูกต้อง:</span>
              <span class="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-sm">ตัวเลือก {correct_letter}</span>
            </div>
            <div class="p-4 rounded-xl bg-indigo-950/30 border border-indigo-900/50 text-xs sm:text-sm text-slate-200 space-y-2">
              <strong class="text-indigo-300 block text-xs uppercase tracking-wider">💡 คำอธิบายเฉลยภาษาไทย (Thai Explanation):</strong>
              <p class="text-slate-300 leading-relaxed text-xs sm:text-sm">{html.escape(explanation_th)}</p>
              <div class="text-[11px] text-slate-400 italic font-mono pt-1">EN: {html.escape(explanation_raw)}</div>
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

print("render_engine.py ready with interactive quiz support.")
