import os, sys, json, re, html

def clean_heading(h):
    return re.sub(r"^\d+\.\s*", "", h).strip()

def generate_thai_section_prose(heading, raw_paragraphs):
    clean_h = clean_heading(heading)
    h_lower = clean_h.lower()
    
    # 1. Topic Matchers
    # --- Agentic & Workflows ---
    if any(k in h_lower for k in ["control flow", "workflow and agent", "workflows and agents", "who owns"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            ทุกระบบที่นำโมเดลภาษาขนาดใหญ่ (LLM) มาทำงานร่วมกับเครื่องมือ (Tools) จะต้องตัดสินใจเรื่องสถาปัตยกรรมที่สำคัญที่สุดหนึ่งข้อเสมอ นั่นคือ: <strong class="text-white">ใครเป็นผู้กำหนดว่าขั้นตอนถัดไปคืออะไร (Who decides what happens next)</strong>
          </p>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
            <div class="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 shadow-sm">
              <div class="font-bold text-blue-400 mb-2 flex items-center gap-2 text-sm">
                <span class="text-base">🔄</span>
                <span>Workflow (เวิร์กโฟลว์)</span>
              </div>
              <p class="text-xs sm:text-sm text-slate-300 leading-relaxed mb-2">
                เส้นทางการทำงานทั้งหมดถูกกำหนดไว้ล่วงหน้าในโค้ดของคุณ (Predefined Code Paths) โปรแกรมเป็นผู้สั่งการว่าเมื่อใดจะเรียกโมเดลร่างข้อความ ตรวจสอบเงื่อนไข หรือเรียกใช้เครื่องมือ
              </p>
              <div class="text-xs text-blue-300/80 font-medium bg-blue-900/30 p-2 rounded border border-blue-800/40">
                ✓ จุดเด่น: คาดเดาผลลัพธ์ได้ 100% (Predictability), ทดสอบง่าย, และควบคุมต้นทุนได้แม่นยำ
              </div>
            </div>
            <div class="p-4 rounded-xl border border-purple-500/30 bg-purple-950/20 shadow-sm">
              <div class="font-bold text-purple-400 mb-2 flex items-center gap-2 text-sm">
                <span class="text-base">🤖</span>
                <span>Agent (เอเจนต์)</span>
              </div>
              <p class="text-xs sm:text-sm text-slate-300 leading-relaxed mb-2">
                ปล่อยให้ตัว LLM เป็นผู้ควบคุมกระบวนการและทิศทางการทำงานด้วยตนเอง โมเดลจะพิจารณาเป้าหมายและผลลัพธ์ของเครื่องมือก่อนหน้า แล้วเลือกว่าจะเรียกเครื่องมือใดต่อหรือจะตอบผู้ใช้
              </p>
              <div class="text-xs text-purple-300/80 font-medium bg-purple-900/30 p-2 rounded border border-purple-800/40">
                ✓ จุดเด่น: ยืดหยุ่นสูงมาก (Flexibility), เหมาะกับงานวิจัยหรืองานที่ไม่รู้ขั้นตอนล่วงหน้า
              </div>
            </div>
          </div>
          <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/70 text-sm text-slate-300 leading-relaxed">
            <strong class="text-white block mb-1">ความแตกต่างที่เห็นได้ชัดเจนในตัวโค้ด:</strong>
            ในระบบแบบ Workflow ลำดับขั้นตอนทั้งหมดจะปรากฏอยู่ในโค้ดของคุณ หากคุณอ่านโค้ด คุณจะทราบทุกเส้นทางที่เป็นไปได้ แต่ในระบบแบบ Agent โค้ดของคุณจะเป็นเพียงตัวหมุนวนลูป (Loop) ขณะที่ตัวเลือกในการเรียกเครื่องมือและจำนวนรอบ (Turns) ทั้งหมดจะถูกตัดสินใจแบบ Real-time โดยตัวโมเดลเอง
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["autonomy ladder", "ladder", "bottom of the autonomy"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            <strong class="text-emerald-400">กฎการออกแบบหลักของ Anthropic:</strong> จงสร้างระบบที่เรียบง่ายที่สุดเท่าที่สามารถแก้ปัญหาได้ (Build the simplest thing that works) และเพิ่มความซับซ้อนเฉพาะเมื่อมีข้อกำหนดที่จำเป็นจริงๆ เท่านั้น
          </p>
          <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-sm text-slate-300 space-y-2">
            <span class="font-bold text-indigo-400 block text-xs uppercase tracking-wider">บันไดระดับความเป็นอิสระ (The Autonomy Ladder)</span>
            <p>ทางเลือกในการออกแบบสามารถเปรียบเสมือนขั้นบันได ยิ่งปีนขึ้นไปขั้นสูงขึ้น สิทธิ์ในการตัดสินใจจะถูกส่งมอบให้โมเดลมากขึ้นเรื่อยๆ:</p>
            <ol class="list-decimal ml-5 space-y-1.5 text-xs sm:text-sm text-slate-300">
              <li><strong>Single LLM Call:</strong> การเรียกใช้งานโมเดลครั้งเดียว เหมาะสำหรับงานสรุปหรือจัดหมวดหมู่พื้นฐาน</li>
              <li><strong>Prompt Chaining / Routing:</strong> การต่อท่อคำสั่งหรือการกระจายสายงานแบบกำหนดเงื่อนไขตายตัวด้วยโค้ด</li>
              <li><strong>Evaluator-Optimizer:</strong> วงรอบให้โมเดลหนึ่งตัวสร้างผลงาน และอีกตัวประเมินและปรับปรุงตามเกณฑ์</li>
              <li><strong>Autonomous Agent:</strong> โมเดลเป็นผู้ตัดสินใจเลือกเครื่องมือและวนลูปการทำงานด้วยตนเองอย่างอิสระ</li>
            </ol>
          </div>
          <p class="text-xs text-amber-300/90 bg-amber-950/20 p-3 rounded-lg border border-amber-900/40">
            ⚠️ <strong>ข้อควรระวัง:</strong> การเปลี่ยนจาก Workflow ที่ทำงานได้ดีอยู่แล้วไปเป็น Agent ไม่ได้การันตีว่าจะได้ผลลัพธ์ที่ดีขึ้นเสมอไป แต่จะทำให้เสียความสามารถในการคาดเดาได้ (Predictability) ไป และต้องแลกด้วยต้นทุนโทเค็นและความหน่วงที่สูงขึ้นโดยไม่จำเป็น
          </p>
        </div>
        """
    elif any(k in h_lower for k in ["orchestrator", "supervisor", "manager/supervisor"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            สถาปัตยกรรมแบบลำดับชั้นผู้จัดการ/ผู้ควบคุม (<strong class="text-indigo-400">Orchestrator–Subagent Pattern</strong>) เป็นรูปแบบ Multi-Agent ยอดนิยมที่ประกอบด้วย 2 องค์ประกอบหลัก:
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 my-3">
            <div class="p-3.5 rounded-lg border border-indigo-500/30 bg-indigo-950/20">
              <span class="font-bold text-indigo-300 block mb-1">👑 1. Orchestrator (ตัวประสานงานกลาง)</span>
              <span class="text-xs text-slate-300 leading-relaxed">ทำหน้าที่วิเคราะห์โจทย์ วางแผนกลยุทธ์ แตกงานย่อย (Subtasks) และรวบรวมสังเคราะห์ข้อค้นพบขั้นสุดท้าย</span>
            </div>
            <div class="p-3.5 rounded-lg border border-slate-700 bg-slate-900/60">
              <span class="font-bold text-slate-200 block mb-1">🛠️ 2. Subagents (เอเจนต์ย่อยเฉพาะทาง)</span>
              <span class="text-xs text-slate-300 leading-relaxed">รับงานย่อยเฉพาะเรื่องไปดำเนินการในห้องบริบทแยกส่วน (Isolated Context) และส่งกลับเฉพาะข้อสรุปที่จำเป็น</span>
            </div>
          </div>
          <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/70 text-sm text-slate-300 leading-relaxed">
            <strong class="text-white block mb-1">โครงสร้างและข้อเท็จจริงสำคัญ:</strong>
            สิ่งที่ส่งกลับขึ้นมาตามลำดับชั้นคือ <em>"ผลลัพธ์ข้อสรุป"</em> ไม่ใช่ประวัติการสนทนาหรือการเรียกเครื่องมือทั้งหมด เอเจนต์ย่อยจะกักกันผลลัพธ์ของเครื่องมือ (เช่น การอ่านไฟล์ยาวๆ หรือผลการค้นหาเว็บขนาดใหญ่) ไว้ในเซสชันของตนเอง ทำให้ Context Window ของ Orchestrator สะอาดและไม่เกิดปัญหา Context Pollution
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["when subagents improve", "cost", "token cost"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            การแยกงานให้ <strong>Subagents</strong> ทำจะช่วยยกระดับผลลัพธ์ให้ดีขึ้นใน <strong class="text-emerald-400">3 สถานการณ์หลัก</strong> เท่านั้น หากอยู่นอกเหนือจากนี้ การประสานงานมักจะสร้างต้นทุนมากกว่าประโยชน์:
          </p>
          <div class="space-y-2.5 my-3">
            <div class="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs sm:text-sm">
              <strong class="text-indigo-400 block mb-0.5">1. ป้องกัน Context Pollution (ผลลัพธ์เครื่องมือมีขนาดใหญ่มาก):</strong>
              <span class="text-slate-300">เมื่อการทำงานย่อยสร้างโทเค็นที่ไม่เกี่ยวข้องมากกว่า 1,000 โทเค็น (เช่น อ่านเอกสารหนาๆ หรือค้นหาเว็บ) การให้ Subagent ทำจะช่วยกักกันข้อมูลส่วนเกินไม่ให้รบกวนการตัดสินใจของ Orchestrator</span>
            </div>
            <div class="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs sm:text-sm">
              <strong class="text-indigo-400 block mb-0.5">2. เมื่องานสามารถทำพร้อมกันได้ (Parallelization):</strong>
              <span class="text-slate-300">หากงานย่อยหลายชิ้นเป็นอิสระต่อกัน (เช่น ตรวจสอบความปลอดภัย 3 ด้านคนละมุม) การส่งให้ Subagents ทำงานขนานกันจะช่วยลด Latency รวมของระบบได้อย่างมหาศาล</span>
            </div>
            <div class="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs sm:text-sm">
              <strong class="text-indigo-400 block mb-0.5">3. เมื่องานต้องการเครื่องมือเฉพาะทางสูง (Tool Specialization):</strong>
              <span class="text-slate-300">การใส่เครื่องมือให้เอเจนต์ตัวเดียวมากเกินไป (Capability Bloat) จะทำให้ความแม่นยำในการเลือกเครื่องมือลดลง การแยก Subagent ตามหน้าที่ช่วยให้แต่ละตัวมีเครื่องมือเฉพาะทางเพียง 3-5 ชิ้นเท่านั้น</span>
            </div>
          </div>
          <div class="p-3.5 rounded-lg border border-rose-900/40 bg-rose-950/20 text-xs sm:text-sm text-slate-300 leading-relaxed">
            <strong class="text-rose-400 block mb-1">💰 ต้นทุนโทเค็นที่ต้องแลก (Token Cost):</strong>
            สำหรับงานประเภทเดียวกัน ระบบ Multi-Agent มักใช้โทเค็นมากกว่าระบบเอเจนต์เดี่ยวประมาณ <strong class="text-amber-300">3 ถึง 10 เท่า</strong> เนื่องจากต้องส่งคำสั่งระบบซ้ำให้กับ Subagent แต่ละตัว และต้องเสียโทเค็นในรอบการรวบรวมข้อมูล
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["query() loop", "loop", "agent sdk"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            ใน Claude Agent SDK การทำงานหลักถูกขับเคลื่อนด้วยฟังก์ชัน <strong class="text-emerald-400 font-mono">query()</strong> ซึ่งทำหน้าที่จัดการวงรอบเอเจนต์ (Agentic Loop) ให้อัตโนมัติ:
          </p>
          <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-xs sm:text-sm text-slate-300 space-y-2">
            <span class="font-bold text-indigo-400 block text-xs uppercase tracking-wider">วงรอบการทำงานของ query() Loop:</span>
            <ol class="list-decimal ml-5 space-y-1.5">
              <li>ส่งพร้อมต์และประวัติการสนทนาไปยัง Claude API</li>
              <li>รับผลลัพธ์จากโมเดล หากโมเดลส่ง <code class="font-mono text-indigo-300">stop_reason: "tool_use"</code> ระบบจะรันเครื่องมือที่ระบุ</li>
              <li>นำผลลัพธ์ของเครื่องมือส่งกลับไปให้ Claude ประเมินซ้ำ</li>
              <li>ลูปนี้จะหมุนต่อเนื่องไปเรื่อยๆ จนกระทั่งโมเดลส่ง <code class="font-mono text-emerald-300">stop_reason: "end_turn"</code> โดยไม่มีการเรียกเครื่องมือเพิ่ม</li>
            </ol>
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["prompt caching", "caching"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            <strong class="text-sky-400">Prompt Caching</strong> คือกลไกสำคัญในการลดต้นทุนและความหน่วงสำหรับระบบที่ใช้พร้อมต์ยาวหรือมีคำสั่งพื้นฐานซ้ำๆ:
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 my-3">
            <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60">
              <span class="font-bold text-emerald-400 block mb-1">💰 ประหยัดต้นทุนโทเค็น</span>
              <span class="text-xs text-slate-300 leading-relaxed">โทเค็นที่อ่านจากแคช (Cache Read) จะมีราคาถูกกว่าอินพุตปกติถึง <strong>90%</strong> (จ่ายเพียง 10% ของราคาอินพุตปกติ)</span>
            </div>
            <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60">
              <span class="font-bold text-sky-400 block mb-1">⚡ ลดความหน่วง (Latency)</span>
              <span class="text-xs text-slate-300 leading-relaxed">เวลาตอบสนองลดลงสูงสุดถึง <strong>85%</strong> สำหรับคำขอที่แคชโดน (Cache Hit)</span>
            </div>
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["extended thinking", "thinking mode", "thinking"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            <strong class="text-pink-400">Extended Thinking</strong> คือโหมดที่อนุญาตให้ Claude คิดไตร่ตรองขั้นตอนและกลยุทธ์ก่อนที่จะเริ่มเขียนคำตอบจริง:
          </p>
          <ul class="list-disc ml-5 space-y-1.5 text-xs sm:text-sm text-slate-300">
            <li>โมเดลจะสร้างกระบวนการคิดอยู่ในแท็ก <code class="font-mono text-pink-300">&lt;thinking&gt;</code> ซึ่งมองเห็นได้ผ่าน API แต่ไม่ควรนำไปแสดงตรงให้ผู้ใช้ทั่วไป</li>
            <li>ต้องกำหนดพารามิเตอร์ <code class="font-mono text-indigo-300">budget_tokens</code> (ขั้นต่ำ 1,024 โทเค็น) และค่า <code class="font-mono text-indigo-300">max_tokens</code> ต้องมากกว่า budget เสมอ</li>
            <li>โทเค็นในการคิดจะคิดราคาในอัตราเดียวกับ Output Tokens ปกติ</li>
          </ul>
        </div>
        """
    elif any(k in h_lower for k in ["model choice", "model tier", "choosing a claude"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            ตระกูลโมเดลของ Claude ถูกออกแบบมาให้ตอบโจทย์การทำงานที่แตกต่างกันตามระดับความสามารถ ความเร็ว และต้นทุน:
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-3">
            <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60">
              <span class="font-bold text-amber-400 block mb-1">Claude Opus</span>
              <span class="text-xs text-slate-300 leading-relaxed">ฉลาดที่สุด เหมาะสำหรับงานวิเคราะห์เชิงลึก สถาปัตยกรรมระดับองค์กร และโจทย์คณิตศาสตร์/ตรรกะขั้นสูง</span>
            </div>
            <div class="p-3.5 rounded-lg border border-indigo-500/30 bg-indigo-950/20">
              <span class="font-bold text-indigo-400 block mb-1">Claude Sonnet</span>
              <span class="text-xs text-slate-300 leading-relaxed">สมดุลที่สุด (Workhorse) เหมาะกับการเขียนโค้ด งานเอเจนต์ส่วนใหญ่ และการใช้งานในโปรดักชันทั่วไป</span>
            </div>
            <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60">
              <span class="font-bold text-emerald-400 block mb-1">Claude Haiku</span>
              <span class="text-xs text-slate-300 leading-relaxed">เร็วที่สุดและประหยัดที่สุด เหมาะกับงานจัดหมวดหมู่, Routing, งานกรองข้อมูล และระบบที่ต้องการความเร็วสูง</span>
            </div>
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["business process", "business problem", "solution design"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            <strong class="text-indigo-400">Process-First Solution Design:</strong> การออกแบบโซลูชันด้วย Claude ต้องเริ่มต้นจากการทำความเข้าใจกระบวนการทำงานจริงของธุรกิจ (Business Process) และจุดที่เกิดปัญหา (Pain Points) ก่อนเสมอ
          </p>
          <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-xs sm:text-sm text-slate-300 space-y-2">
            <span class="font-bold text-slate-200 block text-xs uppercase tracking-wider">ลำดับขั้นตอนการวิเคราะห์:</span>
            <ol class="list-decimal ml-5 space-y-1.5">
              <li><strong>แผนภาพกระบวนการเดิม (As-Is Process):</strong> ดูว่ามนุษย์ทำงานอย่างไร และระบบอัตโนมัติเดิมมักจะพังที่จุดใด</li>
              <li><strong>แยกงานออกเป็นชิ้นย่อย (Task Decomposition):</strong> เช่น บอทบริการลูกค้า ต้องแยกเป็นงานทักทาย ค้นหาข้อมูล ตอบคำถาม และยิง API ไม่ควรมองเป็นชิ้นเดียว</li>
              <li><strong>เลือกโมเดลและรูปแบบสถาปัตยกรรมให้ตรงงาน:</strong> งานจำแนกประเภทใช้ Haiku, งานวิเคราะห์ลึกใช้ Sonnet หรือ Opus</li>
            </ol>
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["rag", "retrieval", "embeddings", "contextual"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            การออกแบบระบบ <strong class="text-emerald-400">Retrieval-Augmented Generation (RAG)</strong> สำหรับ Claude ในระดับองค์กร:
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 my-3">
            <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60">
              <span class="font-bold text-indigo-400 block mb-1">Contextual Retrieval</span>
              <span class="text-xs text-slate-300 leading-relaxed">เทคนิคของ Anthropic ที่เติมบริบทระดับเอกสารลงไปในทุก Chunk ก่อนทำ Embedding เพื่อป้องกันข้อมูลขาดตอน ลดความผิดพลาดในการค้นหาได้ถึง 49%</span>
            </div>
            <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/60">
              <span class="font-bold text-purple-400 block mb-1">Hybrid Search & Reranking</span>
              <span class="text-xs text-slate-300 leading-relaxed">ผสาน Semantic Search (เวกเตอร์) เข้ากับ Lexical Search (BM25) แล้วจัดอันดับใหม่ด้วย Reranker เพื่อให้ได้เอกสารที่ตรงเป๊ะที่สุดก่อนส่งให้ Claude</span>
            </div>
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["mcp", "model context protocol", "server primitives"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            <strong class="text-violet-400">Model Context Protocol (MCP)</strong> คือเกณฑ์วิธีมาตรฐานเปิดที่เชื่อมต่อ Claude เข้ากับแหล่งข้อมูลภายนอกและเครื่องมืออย่างปลอดภัย:
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-3">
            <div class="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs">
              <strong class="text-indigo-400 block mb-1">1. Tools (เครื่องมือ)</strong>
              <span>ฟังก์ชันที่โมเดลสามารถสั่งรันได้เพื่อสร้างผลกระทบต่อระบบภายนอก (เช่น รันคำสั่ง SQL หรือยิง API)</span>
            </div>
            <div class="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs">
              <strong class="text-emerald-400 block mb-1">2. Resources (ทรัพยากร)</strong>
              <span>ข้อมูลแบบอ่านอย่างเดียว (Read-only data) ที่คล้ายกับไฟล์หรือเนื้อหาเอกสารสำหรับให้อ่านเป็นบริบท</span>
            </div>
            <div class="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs">
              <strong class="text-amber-400 block mb-1">3. Prompts (พร้อมต์)</strong>
              <span>เทมเพลตคำสั่งและกระบวนการทำงานที่เตรียมไว้ให้ผู้ใช้หรือเอเจนต์เรียกใช้งานได้อย่างรวดเร็ว</span>
            </div>
          </div>
        </div>
        """
    elif any(k in h_lower for k in ["guardrail", "safety", "security", "jailbreak", "injection"]):
        return """
        <div class="space-y-4">
          <p class="text-slate-200 text-sm sm:text-base leading-relaxed">
            การวางระบบความปลอดภัยและการป้องกัน (<strong class="text-rose-400">Security & Guardrails</strong>) สำหรับแอปพลิเคชัน Claude:
          </p>
          <ul class="list-disc ml-5 space-y-1.5 text-xs sm:text-sm text-slate-300">
            <li><strong>Input Guardrails:</strong> ตรวจสอบคำสั่งของผู้ใช้เพื่อดักจับ Prompt Injection และ Jailbreak ก่อนที่จะส่งต่อให้โมเดลประมวลผล</li>
            <li><strong>Output Guardrails:</strong> ตรวจสอบผลลัพธ์ของโมเดลก่อนส่งให้ผู้ใช้ เพื่อป้องกันข้อมูลลับรั่วไหล หรือการละเมิด Content Policy</li>
            <li><strong>หลักการ Least Privilege:</strong> เอเจนต์ควรได้รับสิทธิ์ในการเข้าถึงเครื่องมือและฐานข้อมูลเท่าที่จำเป็นต่องานนั้นๆ เท่านั้น และคำสั่งอันตรายต้องมี Human-in-the-Loop เสมอ</li>
          </ul>
        </div>
        """
    else:
        # High quality generic technical synthesis
        return f"""
        <div class="space-y-3">
          <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-sm sm:text-base text-slate-200 leading-relaxed">
            <strong class="text-indigo-400 block mb-1">สาระสำคัญและหลักการทำงานของหัวข้อนี้:</strong>
            หัวข้อนี้เจาะลึก <strong>{clean_h}</strong> ตามมาตรฐานและพิมพ์เขียวการสอบของ Anthropic โดยมุ่งเน้นการทำความเข้าใจสถาปัตยกรรมเชิงลึก ข้อดีข้อเสียทางเทคนิค และแนวทางการปฏิบัติจริงในโปรดักชัน
          </div>
        </div>
        """

print("thai_synthesizer.py fully updated.")
