# Complete Thai Translation and Conceptual Synthesis for Anthropic CCDV-F and CCAR-P Blueprints

OBJECTIVE_TRANSLATIONS = {
    # Common objective patterns
    "tell a workflow from an agent": "แยกแยะความแตกต่างระหว่าง Workflow และ Agent โดยพิจารณาว่าใครเป็นผู้ตัดสินใจในขั้นตอนถัดไป (โค้ดของคุณ หรือ โมเดล)",
    "pick the lowest rung of the autonomy ladder": "เลือกใช้ขั้นต่ำที่สุดของบันไดระดับความเป็นอิสระ (Autonomy Ladder) ที่เพียงพอต่อข้อกำหนด และประเมินต้นทุนที่เพิ่มขึ้นเมื่อขยับขั้น",
    "describe how an orchestrator": "อธิบายกลไกที่ Orchestrator Agent กระจายงานไปยัง Subagents และวิธีการรับผลลัพธ์กลับมารวบรวม",
    "name the three situations where subagents beat a single agent": "ระบุ 3 สถานการณ์หลักที่การใช้ Subagents ให้ผลลัพธ์ดีกว่า Agent เดี่ยว พร้อมประเมินผลกระทบด้านโทเค็นและความหน่วง",
    "explain the agent sdk query() loop": "อธิบายวงรอบการทำงานของ query() loop ใน Claude Agent SDK การดักจับ Hooks และการจัดการสถานะ",
    "tell apart anthropic-provided client tools": "แยกแยะความแตกต่างระหว่าง Client Tools ที่ Anthropic เตรียมไว้ให้, Server Tools และ User-defined Tools",
    "decide when an agent's built-in tools are enough": "ตัดสินใจว่าเมื่อใดที่ Built-in Tools ของเอเจนต์เพียงพอแล้ว และเมื่อใดที่จำเป็นต้องเขียน Custom Tool ขึ้นมาเอง",
    "explain how a skill's progressive disclosure": "อธิบายกลไก Progressive Disclosure ของ Agent Skills ในการป้องกันไม่ให้ข้อมูลที่ยังไม่ได้ใช้เข้าไปเปลืองพื้นที่ Context Window",
    "choose mcp, a skill, or both": "เลือกใช้งานระหว่าง MCP, Agent Skills หรือการผสานทั้งสองอย่าง พร้อมประเมินผลกระทบต่อต้นทุน Context Window",
    "turn functional requirements into a claude model choice": "แปลงข้อกำหนดเชิงฟังก์ชันของระบบไปสู่การเลือกรุ่นโมเดล Claude (Haiku, Sonnet, Opus) ได้อย่างเหมาะสม",
    "design system prompts, templates, and guardrails": "ออกแบบ System Prompts, โครงสร้างแม่แบบที่นำกลับมาใช้ซ้ำได้ และวางแนวทางการป้องกัน Guardrails",
    "optimize context windows and manage token usage": "บริหารจัดการ Context Window และคำนวณงบประมาณโทเค็น (Token Budgeting) เพื่อลดต้นทุนและความหน่วง",
    "apply prompt engineering techniques": "ประยุกต์ใช้เทคนิควิศวกรรมพร้อมต์ขั้นสูง เช่น Few-shot, Chain-of-Thought และ XML Tagging",
    "design end-to-end architectures": "ออกแบบสถาปัตยกรรมโซลูชัน AI แบบครบวงจร ทั้งวงรอบประมวลผลอินพุต เอาต์พุต และลูปข้อมูลย้อนกลับ",
    "translate business problems into claude-based ai solutions": "วิเคราะห์ปัญหาทางธุรกิจและแปลงเป็นสถาปัตยกรรมโซลูชันที่ขับเคลื่อนด้วย Claude ได้อย่างตรงจุด",
    "align solutions to business value pillars": "จัดวางโซลูชันให้สอดคล้องกับเสาหลักมูลค่าทางธุรกิจ (Business Value Pillars): ต้นทุน ความเร็ว และความแม่นยำ",
}

KEY_CONCEPT_TRANSLATIONS = {
    "ownership of the control flow": "สิทธิ์การควบคุมกระบวนการ (Ownership of the Control Flow) — เส้นแบ่งสำคัญระหว่าง Workflow และ Agent คือ 'ใครเป็นผู้กำหนดขั้นตอนถัดไป' ใน Workflow โค้ดที่คุณเขียนจะกำหนดลำดับการเรียก LLM และเครื่องมือไว้อย่างตายตัว แต่ใน Agent ตัวโมเดลจะเป็นผู้ตัดสินใจเลือกลำดับขั้นตอนและเครื่องมือด้วยตัวเองขณะทำงาน (Runtime)",
    "process-first solution design": "การออกแบบโซลูชันโดยเริ่มจากกระบวนการ (Process-First Solution Design) — เริ่มต้นด้วยการทำความเข้าใจกระบวนการทำงานจริงของธุรกิจและจุดที่เป็นปัญหา (Pain Points) ก่อนเสมอ แล้วจึงเลือกให้ Claude เข้ามาช่วยเฉพาะขั้นตอนที่สร้างมูลค่าชัดเจน โดยเลือกสถาปัตยกรรมที่เรียบง่ายที่สุดเท่าที่แก้ปัญหาได้ อย่าเริ่มต้นด้วยการเลือกรุ่นโมเดลก่อนเข้าใจกระบวนการ",
    "autonomy ladder": "บันไดระดับความเป็นอิสระ (Autonomy Ladder) — เริ่มต้นจากขั้นที่เรียบง่ายที่สุดเสมอ (เช่น Single Prompt หรือ Workflow) และขยับไปสู่ Autonomous Agent เฉพาะเมื่อข้อกำหนดมีความจำเป็นจริงๆ เนื่องจากทุกขั้นที่เพิ่มความเป็นอิสระ จะต้องแลกด้วยต้นทุนโทเค็นและความหน่วงที่สูงขึ้น",
    "context isolation": "การแยกบริบทเฉพาะส่วน (Context Isolation) — เอเจนต์ย่อย (Subagents) จะช่วยเพิ่มประสิทธิภาพได้สูงสุดเมื่อการทำงานย่อยนั้นสร้างผลลัพธ์ขนาดใหญ่ การแยกห้องสนทนาจะช่วยกักกันขยะบริบท (Context Pollution) ไม่ให้ล้นเข้าสู่ Orchestrator",
}

def get_thai_objective(obj_en):
    if not obj_en: return ""
    obj_lower = obj_en.lower()
    for k, v in OBJECTIVE_TRANSLATIONS.items():
        if k in obj_lower:
            return v
    try:
        from quiz_translator import get_thai_explanation
        th = get_thai_explanation(obj_en)
        if th: return th
    except Exception:
        pass
    return obj_en

def get_thai_key_concept(kc_en):
    if not kc_en: return ""
    kc_lower = kc_en.lower()
    for k, v in KEY_CONCEPT_TRANSLATIONS.items():
        if k in kc_lower:
            return v
    try:
        from quiz_translator import get_thai_explanation
        th = get_thai_explanation(kc_en)
        if th: return th
    except Exception:
        pass
    return kc_en

print("domain_knowledge.py loaded.")
