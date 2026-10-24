import re

# Comprehensive Technical Dictionary & Naturalization Rules for Claude Certification
TERM_RULES = [
    # 1. Multi-word specific phrases & Subagents Architecture
    (r"ผลลัพธ์จากงานย่อยหนึ่งงาน.*?(?:ขับเคลื่อนการพิจารณาในงานย่อยถัดไป|กินพื้นที่จนรบกวนกระบวนการคิด)",
     "ผลลัพธ์จาก Subtask หนึ่ง (เช่น ประวัติคำสั่งซื้อกว่า 2,000+ Tokens) เข้าไปแย่งพื้นที่ Context Window จนบดบังความสามารถในการใช้เหตุผล (Reasoning) ใน Subtask ถัดไป"),
    (r"สถานการณ์สามสถานการณ์ที่.*?(?:เอาชนะเอเจนต์ย่อยเพียงคนเดียว|เอาชนะเอเจนต์เดี่ยว|เอาชนะเอเจนต์ย่อย)",
     "3 สถานการณ์ที่สถาปัตยกรรม Subagents มีประสิทธิภาพเหนือกว่า Single Agent"),
    (r"1\.\s*LLM\s*ที่เพิ่มขึ้นเป็นบล็อกการสร้าง", "1. Augmented LLM ในฐานะ Building Block พื้นฐาน"),
    (r"LLM\s*ที่เพิ่มขึ้นเป็นบล็อกการสร้าง", "Augmented LLM ในฐานะ Building Block พื้นฐาน"),
    (r"โมเดลภาษาที่เพิ่มขึ้น", "Augmented LLM"),
    (r"บล็อกการสร้าง", "Building Block"),
    (r"ขั้นล่างสุดของบันไดอิสรภาพ|ขั้นต่ำสุดของบันไดอิสระ|บันไดระดับความเป็นอิสระ|บันไดความเป็นอิสระ|บันไดอิสระ",
     "Autonomy Ladder (ระดับความเป็นอิสระ)"),
    (r"กระแสการควบคุม", "Control Flow"),
    (r"ความฟุ่มเฟือยของความสามารถ[:\s]*", "Capability Bloat (ปัญหาเครื่องมือมากเกินไปจนลดทอนความแม่นยำ): "),
    (r"การขนานซื้อความคุ้มครอง", "Parallelism ช่วยเพิ่มความครอบคลุม (Coverage) ในการสืบค้น ไม่ใช่เรื่องความเร็ว"),
    (r"การสลายตัวช่วยให้แต่ละงานย่อย", "Task Decomposition ช่วยให้แต่ละ Subtask"),
    (r"การสลายตัว", "Task Decomposition (การแตกงานย่อย)"),
    (r"การบดอัดเกิดขึ้นในระหว่างเซสชัน", "Context Compaction เกิดขึ้นระหว่าง Session"),
    (r"หลังจากการบดอัด", "หลังจากการทำ Context Compaction"),
    (r"การบดอัด", "Context Compaction"),
    (r"คำขอดึงข้อมูล", "Pull Request (PR)"),
    (r"อัตราการสลายตัว", "Decay Rate"),
    (r"ทำไมไตรมาส\s*3\s*ถึงปั่นป่วนถึงสองเท่า", "ทำไม Churn Rate ใน Q3 ถึงเพิ่มขึ้นเป็นสองเท่า"),
    (r"เอาชนะเอเจนต์ย่อยเพียงคนเดียว|เอาชนะเอเจนต์เดี่ยว", "มีประสิทธิภาพเหนือกว่า Single Agent"),

    # 2. Messages & SDK Processing
    (r"Assistant\s*Message\s*และผู้ใช้จะห่อข้อความ\s*API\s*ดิบ",
     "AssistantMessage และ UserMessage จะ Wrap ข้อความ Raw API Message ไว้ข้างใน"),
    (r"ข้อความตัวช่วยและผู้ใช้จะห่อข้อความ\s*API\s*ดิบ",
     "AssistantMessage และ UserMessage จะ Wrap ข้อความ Raw API Message ไว้ข้างใน"),
    (r"ข้อความตัวช่วย", "AssistantMessage"),
    (r"ข้อความผู้ช่วย", "AssistantMessage"),
    (r"ข้อความผู้ใช้", "UserMessage"),
    (r"ข้อความผลลัพธ์", "ResultMessage"),
    (r"UI\s*แบบสด", "Live UI (UI แบบเรียลไทม์)"),
    (r"งานแบบ(?:แบตช์|แบทช์)", "งานแบบ Batch"),
    (r"การประมวลผลแบบ(?:แบตช์|แบทช์)", "Batch Processing"),

    # 3. Hooks & Callbacks
    (r"ตะขอของเพื่อนร่วมทีม", "Hooks ของเพื่อนร่วมทีม"),
    (r"ตะขอของ\s*SessionEnd", "SessionEnd Hook"),
    (r"ตะขอ\s*PreToolUse", "PreToolUse Hook"),
    (r"ตะขอ\s*PostToolUse", "PostToolUse Hook"),
    (r"ตะขอ\s*StopHook", "StopHook"),
    (r"ตะขอระบบไฟล์", "Filesystem Hooks"),
    (r"ผลลัพธ์ของตะขอ", "ผลลัพธ์ของ Hook"),
    (r"เพิ่มตะขอ", "เพิ่ม Hooks"),
    (r"กฎตะขอ|กฎของตะขอ", "Hook Rules"),
    (r"ตะขอ", "Hooks"),
    (r"เปลือกหอย", "Shell"),

    # 4. API Calls & Tool Use
    (r"การโทรหาเครื่องมือ|การเรียกเครื่องมือ|การโทรเครื่องมือ", "Tool Call"),
    (r"การโทร\s*API", "API Call"),
    (r"การโทรกลับ", "Callback"),
    (r"การโทรซ้ำ", "Retry Call"),
    (r"การโทรใดๆ|การโทรใด\s*ๆ", "API Call ใดๆ"),
    (r"การโทรทั้งหมด", "API Calls ทั้งหมด"),
    (r"ทุกการโทร", "ทุก API Call"),
    (r"การโทรแต่ละครั้ง", "แต่ละ API Call"),
    (r"การโทรสำเร็จ", "API Call สำเร็จ"),
    (r"การโทรล้มเหลว", "API Call ล้มเหลว"),
    (r"การโทรถูกบล็อก", "API Call ถูกบล็อก"),
    (r"การโทรแบบต่อเนื่อง", "Sequential API Calls"),
    (r"การโทรเพียงครั้งเดียว|การโทรครั้งเดียว", "API Call ครั้งเดียว"),
    (r"การโทร", "API Call"),

    # 5. Model Pinning & Lifecycle
    (r"รหัสรุ่นคือพิน", "Model Version คือการ Pin เวอร์ชันโมเดลที่แน่นอน"),
    (r"หมุดจะกำหนดน้ำหนัก", "การ Pin เวอร์ชันจะล็อก Model Weights ไว้อย่างแน่นอน"),
    (r"หมุดยังคงสามารถเปลี่ยนแปลงได้", "แต่ Infrastructure การให้บริการรอบๆ ยังคงสามารถเปลี่ยนแปลงได้"),
    (r"หาก\s*ID\s*ที่ปักหมุดเริ่มทำงานแตกต่างออกไป", "หาก Model ID ที่ Pin ไว้เริ่มทำงานแตกต่างออกไป"),
    (r"ปักหมุดเมื่อคุณต้องการความสามารถในการทำซ้ำแบบไบต์ต่อไบต์",
     "Pin เวอร์ชันเมื่อต้องการความสามารถในการทำซ้ำระดับ Byte-to-Byte (Bit-for-Bit Determinism)"),
    (r"ปักหมุดเวอร์ชัน|เวอร์ชันที่ปักหมุด", "Pin เวอร์ชันโมเดล (Pinned Version)"),
    (r"การปักหมุด", "การ Pin เวอร์ชัน (Model Pinning)"),
    (r"ปักหมุด", "Pin เวอร์ชัน"),
    (r"(?<![ก-๙])หมุด(?![ก-๙])", "Pinned Version"),
    (r"สแน็ปช็อต", "Snapshot"),

    # 6. Context Window & Memory
    (r"Context\s*Pollution\s*\(บริบทปนเปื้อน\)\s*\(Context\s*Pollution\)", "Context Pollution (ปัญหาบริบทปนเปื้อน)"),
    (r"มลภาวะจากบริบท|มลภาวะในบริบท|มลภาวะต่อบริบท|การปนเปื้อนบริบท", "Context Pollution (บริบทปนเปื้อน)"),
    (r"หน้าต่างบริบท|หน้าต่างของบริบท", "Context Window"),
    (r"งบประมาณบริบท|งบประมาณของหน้าต่างบริบท", "Context Window Budget"),
    (r"การแยกบริบท", "Context Isolation (การแยก Context ระหว่าง Subagents)"),
    (r"การแคชพร้อมท์|การแคชการแจ้งเตือน|แคชพร้อมท์", "Prompt Caching"),
    (r"แคชตี|ตีแคช", "Cache Hit"),
    (r"แคชพลาด", "Cache Miss"),
    (r"การตัดทอนผลลัพธ์เครื่องมือ", "Tool Output Pruning (การตัดทอนผลลัพธ์ Tool)"),
    (r"คํานําหน้าพร|คำนำหน้าพร้อมท์", "Prompt Prefix"),
    (r"เวลาที่จะมีชีวิตอยู่|เวลาในการมีชีวิต", "TTL (Time to Live)"),

    # 7. Prompting & Messages
    (r"งานวิศวกรรมการแจ้งเตือน|วิศวกรรมการแจ้งเตือน|วิศวกรรมพร้อมต์", "Prompt Engineering"),
    (r"การแจ้งเตือนระบบ|พร้อมท์ระบบ", "System Prompt"),
    (r"การแจ้งเตือนแบบ\s*zero-shot|การกระตุ้นแบบ\s*zero-shot|การกระตุ้นแบบไม่มีตัวอย่าง", "Zero-shot Prompting"),
    (r"การแจ้งเตือนแบบ\s*few-shot|การกระตุ้นแบบ\s*few-shot|การกระตุ้นแบบไม่กี่ครั้ง|การกระตุ้นแบบตัวอย่างน้อย", "Few-shot Prompting"),
    (r"ลูกโซ่พร้อมท์|ลูกโซ่พรอมต์|การเชื่อมต่อแบบลูกโซ่", "Prompt Chaining"),
    (r"ข้อความแจ้งเตือน|การแจ้งเตือน(?!\s*(?:อีเมล|เตือนภัย|ไลน์|สแลค|โทรศัพท์))", "Prompt"),
    (r"พร้อมท์", "Prompt"),
    (r"การกระตุ้น(?!\s*(?:หัวใจ|เศรษฐกิจ))", "Prompting"),

    # 8. Agents & Subagents
    (r"เจ้าหน้าที่\s*SDK|ตัวแทน\s*SDK", "Agent SDK"),
    (r"SDK\s*ของลูกค้า|SDK\s*ของไคลเอ็นต์|SDK\s*ของไคลเอนต์", "Client SDK"),
    (r"ลูปเจ้าหน้าที่|ลูปเอเจนต์|ลูปตัวแทน", "Agent Loop"),
    (r"เจ้าหน้าที่ชั้นรอง|เจ้าหน้าที่ย่อย|ตัวแทนย่อย", "Subagents"),
    (r"เจ้าหน้าที่เพียงคนเดียว|เจ้าหน้าที่คนเดียว|ตัวแทนเดี่ยว|ฝ่ายเดียว", "Single Agent"),
    (r"ตัวแทนหลัก|เจ้าหน้าที่หลัก", "Lead Agent"),
    (r"ตัวแทนหลายราย|ตัวแทนหลายคน|เจ้าหน้าที่หลายคน", "หลาย Subagents (Multiple Subagents)"),
    (r"ตัวแทนที่มีการจัดการ", "Managed Agents"),
    (r"ระบบเจ้าหน้าที่|ระบบตัวแทน", "ระบบ Agent"),
    (r"นักดนตรีประสานเสียง|ผู้เรียบเรียง", "Orchestrator"),
    (r"ผู้ควบคุมระบบและเอเจนต์ย่อย", "Orchestrator และ Subagents"),
    (r"ผู้ควบคุมระบบ", "Orchestrator"),
    (r"เครื่องมือวิ่ง", "Tool Runner"),
    (r"เจ้าหน้าที่(?!\s*(?:ตำรวจ|รัฐ|ความปลอดภัยในอาคาร))", "Agent"),
    (r"ตัวแทน(?!\s*(?:จำหน่าย|ประกัน|ขาย))", "Agent"),
    (r"เอเจนต์ย่อย", "Subagents"),
    (r"เอเจนต์เดี่ยว", "Single Agent"),
    (r"เอเจนต์", "Agent"),

    # 9. Security & Guardrails
    (r"การฉีดการแจ้งเตือนและการเจลเบรก", "Prompt Injection และ Jailbreak"),
    (r"การฉีดการแจ้งเตือน|การฉีดคำสั่ง", "Prompt Injection"),
    (r"การแหกคุก|การเจลเบรก", "Jailbreak"),
    (r"ขอบเขตความน่าเชื่อถือ", "Trust Boundary"),
    (r"กล่องทราย|การกักกัน", "Sandbox"),
    (r"คนในลูป|มนุษย์ในวง(?:\s*รอบ)?|มนุษย์ในลำดับการอนุญาต", "Human-in-the-Loop (HITL)"),
    (r"ลายน้ําที่มองไม่เห็น|ลายน้ำที่มองไม่เห็น", "Invisible Watermark"),

    # 10. Workflows, Search & Thinking
    (r"เวิร์กโฟลว์การกระจายงาน", "Routing Workflow"),
    (r"วงรอบการประเมินและปรับปรุง", "Evaluator-Optimizer Loop"),
    (r"การขนาน", "Parallelization (การประมวลผลคู่ขนาน)"),
    (r"การประมวลผลแบบขนาน|การทํางานแบบขนาน", "Parallelization (การประมวลผลคู่ขนาน)"),
    (r"การดึงข้อมูลแบบทันเวลา", "Just-in-Time (JIT) Retrieval"),
    (r"การค้นหาแบบผสมผสาน", "Hybrid Search (BM25 + Semantic Search)"),
    (r"การฝังเวกเตอร์|เวกเตอร์ฝังตัว", "Vector Embeddings"),
    (r"คอร์ปัส", "Corpus"),
    (r"การคิดแบบขยาย|การคิดเชิงลึก", "Extended Thinking"),
    (r"งบประมาณการคิด|งบประมาณโทเค็นสำหรับการคิด|โทเค็นงบประมาณ", "Thinking Budget"),
    (r"โหมดเร็ว", "Fast Mode"),
    (r"คําถามความพยายาม|การตั้งค่าความพยายาม", "พารามิเตอร์ Thinking Effort"),
    (r"ความพยายามแลกเปลี่ยน", "Thinking Effort แลกเปลี่ยน"),

    # 11. Clean badges, traps & duplicates
    (r"Exam\s*Trap::", "จุดที่ข้อสอบชอบหลอก (Exam Trap):"),
    (r"Exam\s*Trap:\s*\(จุดที่ข้อสอบชอบหลอก\):", "จุดที่ข้อสอบชอบหลอก (Exam Trap):"),
    (r"Exam\s*Trap:\s*จุดที่ข้อสอบชอบหลอก:", "จุดที่ข้อสอบชอบหลอก (Exam Trap):"),
    (r"กับดักการสอบ", "จุดที่ข้อสอบชอบหลอก (Exam Trap):"),
    (r"หลุมพรางการสอบ", "จุดที่ข้อสอบชอบหลอก (Exam Trap):"),
    (r"Predict\s*First::", "คาดการณ์ก่อนตอบ (Predict First):"),
    (r"Predict\s*First:\s*คาดการณ์ก่อนตอบ:", "คาดการณ์ก่อนตอบ (Predict First):"),
    (r"คาดการณ์ก่อน", "คาดการณ์ก่อนตอบ (Predict First):")
]

def naturalize_text(text):
    if not text:
        return ""
    res = text
    for pat, rep in TERM_RULES:
        res = re.sub(pat, rep, res)
    return res

if __name__ == "__main__":
    test = "ใน Claude Agent SDK query() คือลูปเจ้าหน้าที่ คุณส่งผ่านพร้อมท์และตัวเลือก และการโทรเพียงครั้งเดียวมีมากกว่าข้อความของผู้ใช้ ตะขอของเพื่อนร่วมทีม"
    print("Original:", test)
    print("Naturalized:", naturalize_text(test))
