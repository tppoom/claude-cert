import re

# Comprehensive Thai translation dictionaries for Headings and Sections
HEADING_THAI = {
    # Foundations Domain 1
    "workflows and agents differ in who owns the control flow": "ความแตกต่างระหว่าง Workflow และ Agent: ใครเป็นผู้ถือสิทธิ์ควบคุมกระบวนการ (Control Flow)",
    "start at the bottom of the autonomy ladder": "เริ่มต้นจากขั้นต่ำสุดของบันไดระดับความเป็นอิสระ (Autonomy Ladder)",
    "manager/supervisor hierarchies: an orchestrator and its subagents": "สถาปัตยกรรมลำดับชั้นแบบผู้จัดการ: Orchestrator และ Subagents",
    "when subagents improve the result, and what they cost": "เมื่อใดที่การใช้ Subagents ให้ผลลัพธ์ดีกว่า และต้นทุนที่ต้องแลกคืออะไร",
    "the agent sdk query() loop, hooks and subagents": "การทำงานของ query() loop, Hooks และ Subagents ใน Claude Agent SDK",
    "ways to build and host a claude agent": "แนวทางการสร้างและโฮสต์ Claude Agent: Build Paths และ Managed Options",
    "agent patterns and frameworks: workflows, subagents, and memory": "รูปแบบเอเจนต์และเฟรมเวิร์ก: เวิร์กโฟลว์, เอเจนต์ย่อย และการจัดการหน่วยความจำ",

    # Foundations Domain 2
    "turning functional requirements into a claude model choice": "การแปลงข้อกำหนดเชิงฟังก์ชันสู่การเลือกรุ่นโมเดล Claude ที่เหมาะสม",
    "infrastructure requirements: platform, data residency, zdr and capacity": "ข้อกำหนดโครงสร้างพื้นฐาน: แพลตฟอร์ม, การจัดเก็บข้อมูล (Data Residency), ZDR และ Capacity",
    "claude model lifecycle: deprecation, retirement and migration": "วงจรชีวิตโมเดล Claude: การยกเลิก (Deprecation), การปลดระวาง (Retirement) และการย้ายระบบ",
    "evaluating, versioning and rolling out changes to claude systems": "การประเมินผล การกำหนดเวอร์ชัน และการ Rollout ระบบ Claude สู่การใช้งานจริง",
    "claude messages api mechanics: requests, state, tools, streaming and vision": "กลไก Claude Messages API: โครงสร้างคำขอ, State, Tools, Streaming และ Vision",
    "message batches api and choosing batch over realtime calls": "Message Batches API: การเลือกใช้งานแบบ Batch เทียบกับ Realtime เพื่อลดต้นทุน 50%",
    "calling the claude api: rest, json and sync vs async patterns": "การเรียกใช้งาน Claude API ผ่าน REST, JSON และรูปแบบ Sync เทียบกับ Async",
    "claude code in git, ci, code review and refactoring": "การใช้งาน Claude Code ร่วมกับ Git, ระบบ CI, Code Review และการ Refactor โค้ด",
    "claude application design: surfaces, instruction placement and output schemas": "การออกแบบแอปพลิเคชัน: พื้นผิวการโต้ตอบ, การจัดวางคำสั่ง และการกำหนด Output Schema",
    "session hygiene and plugin management in claude code": "การดูแลสุขอนามัยของเซสชันและการจัดการปลั๊กอินใน Claude Code",
    "configuration management for claude: claude.md, settings, model and prompt pinning": "การจัดการการตั้งค่าสำหรับ Claude: CLAUDE.md, settings.json และการตรึงเวอร์ชันโมเดล/พร้อมต์",

    # Foundations Domain 3-8
    "claude code project configuration: claude.md, rules, auto memory and settings.json": "การตั้งค่าโปรเจกต์ Claude Code: CLAUDE.md, Rules, Auto Memory และ settings.json",
    "running claude code: skills, subagents, sessions, headless and auto mode": "การรัน Claude Code: Skills, Subagents, Sessions, Headless Mode และ Auto Mode",
    "claude api error types and recovery strategies": "ประเภทข้อผิดพลาดของ Claude API และกลยุทธ์การกู้คืนระบบ (Error Recovery)",
    "tracing claude failures to the integration or the model": "การสืบค้นความล้มเหลว: ปัญหาจากชั้น Integration เทียบกับ Model Output",
    "how llms work: tokens, context windows and sampling": "กลไกการทำงานของ LLM: โทเค็น, Context Window และพารามิเตอร์การสุ่ม (Sampling)",
    "calling the claude api over rest: endpoints, headers and sdks": "การเรียก Claude API ผ่าน REST: Endpoints, Headers สำคัญ และ Official SDKs",
    "choosing a claude model: tiers, effort and fast mode": "การเลือกรุ่น Claude Model: ลำดับชั้นโมเดล, ระดับ Thinking Effort และ Fast Mode",
    "claude token pricing, token counting and usage tracking": "โครงสร้างราคาโทเค็น Claude, การนับโทเค็น (Token Counting) และการติดตามการใช้งาน",
    "context window budget and tool output pruning": "การจัดสรรงบประมาณ Context Window และการตัดทอนผลลัพธ์เครื่องมือ (Pruning)",
    "prompt engineering for claude: clarity, examples, placement and format": "วิศวกรรมพร้อมต์สำหรับ Claude: ความชัดเจน, ตัวอย่าง Few-shot, การจัดวาง และฟอร์แมต XML",
    "structured outputs and strict tool use": "การสร้าง Structured Outputs และ Strict Tool Use เพื่อให้ได้ผลลัพธ์ JSON ที่แม่นยำ 100%",
    "prompt injection and jailbreak defense for claude applications": "การป้องกัน Prompt Injection และ Jailbreak สำหรับแอปพลิเคชัน Claude",
    "guardrail layering and content policy for claude applications": "การวาง Guardrail หลายชั้นและนโยบายเนื้อหา (Content Policy) สำหรับ Claude",
    "claude code hook events, matchers and handler types": "เหตุการณ์ Claude Code Hooks, Matchers และประเภทของ Handlers",
    "claude api keys: identity, storage, rotation and leak response": "คีย์ Claude API: ข้อมูลประจำตัว, การจัดเก็บปลอดภัย, การหมุนเวียนคีย์ และการรับมือคีย์รั่วไหล",
    "defining claude tools: schemas, descriptions, and tool set design": "การนิยามเครื่องมือ Claude Tools: โครงสร้าง Schema, คำอธิบาย และการออกแบบชุดเครื่องมือ",
    "mcp server primitives: tools, resources, and prompts": "องค์ประกอบพื้นฐานของ MCP Server: Tools, Resources และ Prompts",
    "built-in tools, custom tools, skills and mcp: choosing how to extend claude": "เปรียบเทียบ Built-in Tools, Custom Tools, Skills และ MCP: การเลือกวิธีขยายขีดความสามารถ",

    # Architect Domain 1-7
    "translating business problems into claude solutions": "การแปลงโจทย์ปัญหาทางธุรกิจสู่การออกแบบโซลูชันด้วย Claude",
    "end-to-end agent architecture: the loop, tool execution and feedback": "สถาปัตยกรรมเอเจนต์แบบ End-to-End: วงรอบการทำงาน, การประมวลผลเครื่องมือ และลูปข้อมูลย้อนกลับ",
    "workflow, agent and augmented llm patterns for claude": "รูปแบบสถาปัตยกรรมสำหรับ Claude: เวิร์กโฟลว์, เอเจนต์เดี่ยว และ Augmented LLM",
    "multi-agent design: when to split and how to brief subagents": "การออกแบบระบบ Multi-Agent: เกณฑ์การแบ่งงานและวิธีกำหนดบทบาทของ Subagents",
    "task decomposition patterns: chaining, routing, parallelization and orchestrator-workers": "รูปแบบการย่อยงาน (Task Decomposition): Chaining, Routing, Parallelization และ Orchestrator-Workers",
    "business value pillars for claude solutions": "เสาหลักมูลค่าทางธุรกิจสำหรับโซลูชัน Claude: ต้นทุน, ประสิทธิภาพ, ความแม่นยำ และเวลา",
    "choosing a claude model: lineup, starting point and cost per task": "การเลือกรุ่นโมเดล Claude เชิงกลยุทธ์: ตระกูลโมเดล, จุดเริ่มต้นการเลือก และต้นทุนต่องาน",
    "system prompts and reusable prompt templates for claude": "การออกแบบ System Prompts และโครงสร้างแม่แบบที่นำกลับมาใช้ซ้ำได้สำหรับ Claude",
    "few-shot and chain-of-thought prompting for claude": "เทคนิคการสั่งการขั้นสูง: Few-shot และ Chain-of-Thought สำหรับ Claude",
    "context window budgeting: what counts and how to measure it": "การบริหารงบประมาณ Context Window: อะไรบ้างที่นับโทเค็นและวิธีวัดผลอย่างแม่นยำ",
    "capability bloat in agent tool configurations": "ปัญหา Capability Bloat: เหตุผลที่การใส่เครื่องมือมากเกินไปทำให้เอเจนต์ทำงานแย่ลง",
    "mcp authorization: discovery, client registration and scoped tokens": "การยืนยันสิทธิ์ใน MCP: การค้นพบ, การลงทะเบียนไคลเอนต์ และการผูกโทเค็นแบบจำกัดสิทธิ์",
    "accuracy-latency trade-offs: effort, fast mode, streaming and justified configs": "การประนีประนอมความแม่นยำและความหน่วง: ระดับ Effort, Fast Mode, Streaming และการตั้งค่าที่เหมาะสม",
    "run-level telemetry and tagging for claude agent fleets": "การตรวจวัดการทำงาน (Telemetry) และการติดแท็กระดับ Run-Level สำหรับกองทัพเอเจนต์ Claude",
    "rag ingestion: chunking, embeddings and contextual indexing": "กระบวนการนำเข้าข้อมูล RAG: การตัดแบ่งข้อความ (Chunking), เวกเตอร์ฝังตัว และ Contextual Indexing",
    "retrieval strategies matched to data shape and query pattern": "การจับคู่กลยุทธ์การค้นคืนข้อมูลให้สอดคล้องกับลักษณะข้อมูลและรูปแบบคำค้นหา",
    "evaluation metrics for claude systems: accuracy, latency, cost, safety and security": "ตัวชี้วัดการประเมินผลระบบ Claude: ความแม่นยำ, ความหน่วง, ต้นทุน, ความปลอดภัย และความมั่นคง",
    "a/b testing prompts: baselines, segments and versioned rollout": "การทำ A/B Testing สำหรับพร้อมต์: ค่ามาตรฐานอ้างอิง, การแบ่งกลุ่มทดสอบ และการ Rollout แบบเวอร์ชัน",
    "human approval checkpoints in claude code and the agent sdk": "จุดตรวจการอนุมัติโดยมนุษย์ (Human Approval Checkpoints) ใน Claude Code และ Agent SDK",
    "hipaa, baas and zero data retention for claude": "การปฏิบัติตามกฎหมาย HIPAA, ข้อตกลง BAA และนโยบายไม่เก็บรักษาข้อมูล (Zero Data Retention)",
    "structured discovery and requirement gathering for claude solutions": "การค้นหาความต้องการและการรวบรวมข้อกำหนดเชิงโครงสร้างสำหรับโซลูชัน Claude",
}

def get_thai_heading(h_en):
    h_clean = re.sub(r"^\d+\.\s*", "", h_en).strip().lower()
    for k, v in HEADING_THAI.items():
        if k in h_clean:
            # preserve original prefix number if present
            num_match = re.match(r"^(\d+\.)\s*", h_en)
            prefix = num_match.group(1) + " " if num_match else ""
            return prefix + v
    try:
        from quiz_translator import get_thai_explanation
        num_match = re.match(r"^(\d+\.)\s*", h_en)
        prefix = num_match.group(1) + " " if num_match else ""
        raw_core = re.sub(r"^\d+\.\s*", "", h_en).strip()
        th_core = get_thai_explanation(raw_core)
        if th_core and th_core != raw_core:
            return prefix + th_core
    except Exception:
        pass
    return h_en

print("section_translator.py loaded.")
