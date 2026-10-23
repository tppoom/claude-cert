import os, sys, json, re, html

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
    # Apply term map if not inside code
    for pat, rep in TERM_MAP:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return res

def generate_section_deep_dive(heading, items, domain_title):
    """
    Generates in-depth technical expansion explaining:
    1. Operational mechanics under the hood
    2. Architecture tradeoffs & token consumption
    3. Crucial certification takeaways & pitfalls
    """
    clean_h = re.sub(r"^\d+\.\s*", "", heading).strip()
    return f"""
<div class="my-6 rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-5 shadow-sm">
  <div class="flex items-center gap-2 font-bold text-indigo-400 mb-2 text-sm">
    <svg class="w-5 h-5 text-indigo-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    <span>🔍 อธิบายขยายความเชิงลึก & จุดสังเกตสำหรับข้อสอบ (In-Depth Technical Insights)</span>
  </div>
  <div class="text-slate-300 text-sm leading-relaxed space-y-2">
    <p>
      <strong>กลไกการทำงานเบื้องหลัง (Under the Hood):</strong> ในหัวข้อ <em>"{clean_h}"</em> หัวใจสำคัญตามแนวทางของ Anthropic คือการมองเห็นความแตกต่างระหว่าง <strong>Predefined Code Logic (Deterministic)</strong> กับ <strong>Model Autonomy (Stochastic)</strong> ระบบที่ควบคุมด้วยโค้ดจะให้ผลลัพธ์ที่คาดเดาได้ (Predictability) สูงกว่า ใช้โทเค็นน้อยกว่า และวัดผลได้ง่ายกว่าเสมอ
    </p>
    <p>
      <strong>ผลกระทบต่อต้นทุนและประสิทธิภาพ (Cost & Token Trade-offs):</strong> การเพิ่มระดับความเป็นอิสระ (Autonomy) หรือการแยกงานเป็น Multi-Agent จะทำให้การใช้โทเค็นเพิ่มขึ้นประมาณ <strong>3x ถึง 10x</strong> เนื่องจากต้องส่ง Context ซ้ำในแต่ละ Subagent และต้องใช้รอบข้อความ (Turns) เพิ่มขึ้นในการสรุปข้อมูลกลับสู่ Orchestrator
    </p>
    <p class="text-amber-300/90 font-medium">
      💡 <strong>จุดที่ข้อสอบเน้นย้ำ:</strong> หากโจทย์ระบุว่ากระบวนการทำงานมีขั้นตอนที่แน่นอนตายตัว (Fixed sequence) หรือประเภทงานแบ่งกลุ่มชัดเจน (Predictable paths) ให้เลือก <strong>Workflow (เช่น Chaining หรือ Routing)</strong> เสมอ อย่าเลือก Autonomous Agent เพียงเพราะต้องการความทันสมัย!
    </p>
  </div>
</div>
"""

def render_checkpoint_html(key, block_data, question_data):
    if question_data:
        q = question_data
        stem = q.get("question", "")
        options = q.get("options", [])
        correct_answers = q.get("correct_answers", ["A"])
        explanations = q.get("explanations", [])
        
        # Build options HTML
        opt_letters = ["A", "B", "C", "D", "E"]
        opt_html = ""
        for i, opt in enumerate(options):
            let = opt_letters[i] if i < len(opt_letters) else str(i)
            is_correct = let in correct_answers
            opt_html += f"""
            <div class="flex items-start gap-3 p-3 rounded-lg border border-slate-800 bg-slate-800/40 text-slate-300 text-sm">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded bg-slate-700 text-xs font-bold text-slate-300 shrink-0">{let}</span>
              <span class="leading-relaxed">{html.escape(opt)}</span>
            </div>
            """
            
        exp_html = ""
        for exp in explanations:
            let = exp.get("option", "")
            e_text = exp.get("explanation", "")
            is_c = let in correct_answers
            color_cls = "text-emerald-400 font-bold" if is_c else "text-slate-400"
            badge = '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-xs">ถูกต้อง</span>' if is_c else '<span class="px-2 py-0.5 rounded bg-red-500/20 text-red-300 text-xs">ไม่ถูกต้อง</span>'
            exp_html += f"""
            <div class="border-b border-slate-800/80 pb-2.5 last:border-0 last:pb-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-bold text-slate-200">ตัวเลือก {let}:</span>
                {badge}
              </div>
              <p class="text-slate-300 text-xs leading-relaxed">{html.escape(e_text)}</p>
            </div>
            """
            
        return f"""
        <div class="my-8 rounded-xl border border-indigo-500/40 bg-slate-900/90 p-6 shadow-lg backdrop-blur">
          <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
            <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-indigo-400 uppercase">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300">📝</span>
              <span>ข้อสอบจำลองทางการ (Official Exam Question)</span>
            </div>
            <span class="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">ID: {q.get('id', '')}</span>
          </div>
          <p class="text-base font-medium text-slate-100 mb-4 leading-relaxed">{html.escape(stem)}</p>
          <div class="space-y-2 mb-5">
            {opt_html}
          </div>
          <details class="group mt-4 pt-4 border-t border-slate-800">
            <summary class="cursor-pointer text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center justify-between select-none">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                คลิกดูเฉลยคำตอบพร้อมคำอธิบายแบบเจาะลึก (Reveal Answer & Detailed Analysis)
              </span>
              <span class="transition-transform group-open:rotate-180 text-xs">▼</span>
            </summary>
            <div class="mt-4 p-4 rounded-lg bg-indigo-950/40 border border-indigo-900/60 text-sm text-slate-300 space-y-3">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">คำตอบที่ถูกต้อง:</span>
                <span class="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-sm">ตัวเลือก {', '.join(correct_answers)}</span>
              </div>
              <div class="space-y-3 pt-2">
                {exp_html}
              </div>
            </div>
          </details>
        </div>
        """
    elif block_data:
        b = block_data
        prompt = b.get("prompt", "")
        options = b.get("options", [])
        ans_idx = b.get("answerIndex")
        explanation = b.get("explanation", "")
        citation = b.get("citation", {})
        
        opt_html = ""
        opt_letters = ["A", "B", "C", "D", "E"]
        for i, opt in enumerate(options):
            let = opt_letters[i] if i < len(opt_letters) else str(i)
            opt_html += f"""
            <div class="flex items-start gap-3 p-3 rounded-lg border border-slate-800 bg-slate-800/40 text-slate-300 text-sm">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded bg-slate-700 text-xs font-bold text-slate-300 shrink-0">{let}</span>
              <span class="leading-relaxed">{html.escape(opt)}</span>
            </div>
            """
            
        correct_letter = opt_letters[ans_idx] if ans_idx is not None and ans_idx < len(opt_letters) else "N/A"
        
        cit_html = ""
        if citation and citation.get("quote"):
            cit_html = f"""
            <div class="mt-3 pt-2 border-t border-slate-800 text-xs text-slate-400 italic">
              “{html.escape(citation.get('quote', ''))}”
              <br><a href="{citation.get('sourceUrl', '#')}" target="_blank" class="underline text-indigo-400 not-italic font-sans mt-0.5 inline-block">🔗 เอกสารอ้างอิง Anthropic</a>
            </div>
            """
            
        return f"""
        <div class="my-8 rounded-xl border border-indigo-500/30 bg-slate-900/80 p-6 shadow-md backdrop-blur">
          <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
            <div class="flex items-center gap-2 text-xs font-bold tracking-wider text-indigo-400 uppercase">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300">✓</span>
              <span>แบบฝึกหัดตรวจสอบความเข้าใจ (Checkpoint Practice)</span>
            </div>
            <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">Check</span>
          </div>
          <p class="text-base font-medium text-slate-100 mb-4 leading-relaxed">{html.escape(prompt)}</p>
          <div class="space-y-2 mb-4">
            {opt_html}
          </div>
          <details class="group mt-4 pt-3 border-t border-slate-800">
            <summary class="cursor-pointer text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center justify-between select-none">
              <span>คลิกดูเฉลยคำตอบพร้อมคำอธิบาย (Click to view answer & explanation)</span>
              <span class="transition-transform group-open:rotate-180 text-xs">▼</span>
            </summary>
            <div class="mt-3 p-4 rounded-lg bg-indigo-950/30 border border-indigo-900/50 text-sm text-slate-300 space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold uppercase text-slate-400">คำตอบที่ถูกต้อง:</span>
                <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-xs">ตัวเลือก {correct_letter}</span>
              </div>
              <p class="text-slate-300 leading-relaxed text-xs">{html.escape(explanation)}</p>
              {cit_html}
            </div>
          </details>
        </div>
        """
    return ""

print("Loaded render engine module.")
