import os, sys, json, re, html
from bs4 import BeautifulSoup
from render_engine import render_checkpoint_html, generate_section_deep_dive
from thai_synthesizer import generate_thai_section_prose
from section_translator import get_thai_heading
from domain_knowledge import get_thai_objective, get_thai_key_concept

def build_sidebar_html(catalog, current_idx, course_type):
    domains_map = {}
    for item in catalog:
        d = item["domain_no"]
        if d not in domains_map:
            domains_map[d] = {
                "title": item["domain_title"],
                "items": []
            }
        domains_map[d]["items"].append(item)
        
    html_out = ""
    for d_no, d_data in sorted(domains_map.items(), key=lambda x: int(x[0])):
        html_out += f"""
        <div class="mb-4">
          <div class="px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-slate-400 bg-slate-900/60 rounded mb-1">
            {d_data['title']}
          </div>
          <div class="space-y-0.5">
        """
        for it in d_data["items"]:
            is_active = (it["idx"] == current_idx)
            active_cls = "bg-indigo-600/30 text-indigo-300 font-semibold border-l-2 border-indigo-400 pl-2.5" if is_active else "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 pl-3"
            sub_prefix = f"<span class='text-xs opacity-75 mr-1 font-mono'>[{it['sub_no']}]</span>" if it.get("sub_no") else ""
            html_out += f"""
            <a href="{it['filename']}" class="flex items-center text-xs py-1.5 pr-2 rounded transition-colors {active_cls}">
              {sub_prefix}
              <span class="truncate">{it['title']}</span>
            </a>
            """
        html_out += """
          </div>
        </div>
        """
    return html_out

def render_lesson_page(lesson_data, catalog, current_idx, course_type):
    p = lesson_data
    course_name = "Anthropic Claude Certified Developer – Foundations (CCDV-F)" if course_type == "foundations" else "Anthropic Claude Certified Architect – Professional (CCAR-P)"
    course_code = "CCDV-F" if course_type == "foundations" else "CCAR-P"
    course_home = "index.html"
    other_course_url = "../architect/index.html" if course_type == "foundations" else "../foundations/index.html"
    other_course_name = "สลับไปคอร์ส Architect (CCAR-P)" if course_type == "foundations" else "สลับไปคอร์ส Developer (CCDV-F)"
    
    sidebar_html = build_sidebar_html(catalog, current_idx, course_type)
    
    # Prev / Next
    prev_item = catalog[current_idx - 2] if current_idx > 1 else None
    next_item = catalog[current_idx] if current_idx < len(catalog) else None
    
    # Badges
    badges_html = ""
    for b in p.get("badges", []):
        badges_html += f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">{b}</span> '
    if p.get("sub_no"):
        badges_html = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Subdomain {p["sub_no"]}</span> ' + badges_html
        
    # Objectives (Thai)
    objs_html = ""
    if p.get("objectives"):
        objs_list = "".join(f'<li class="flex items-start gap-2.5"><span class="text-indigo-400 font-bold shrink-0 mt-0.5">✓</span><span>{get_thai_objective(obj)}</span></li>' for obj in p["objectives"])
        objs_html = f"""
        <section class="my-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6 backdrop-blur shadow-sm">
          <h2 class="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-3 flex items-center gap-2">
            <span class="text-base">🎯</span>
            <span>สิ่งที่คุณจะสามารถทำได้หลังจบบทเรียนนี้ (What you will be able to do)</span>
          </h2>
          <ul class="space-y-2.5 text-sm sm:text-[15px] text-slate-200 leading-relaxed">
            {objs_list}
          </ul>
        </section>
        """
        
    # Key concept (Thai)
    kc_html = ""
    if p.get("key_concept"):
        kc_thai = get_thai_key_concept(p["key_concept"])
        kc_html = f"""
        <section class="my-6 rounded-2xl border-l-4 border-l-amber-500 border-y border-r border-slate-800 bg-amber-950/20 p-5 sm:p-6 shadow-sm">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">
            <span class="text-base">💡</span>
            <span>แนวคิดหลักสำคัญ (Key Concept)</span>
          </div>
          <p class="text-sm sm:text-base text-slate-200 leading-relaxed font-medium">
            {kc_thai}
          </p>
        </section>
        """
        
    # TOC
    toc_links = ""
    for sec in p.get("sections", []):
        h = sec["heading"]
        th_h = get_thai_heading(h)
        clean_id = re.sub(r"[^a-zA-Z0-9]+", "-", h).lower().strip("-")
        toc_links += f'<li><a href="#{clean_id}" class="text-slate-400 hover:text-indigo-300 transition-colors flex items-center gap-2"><span class="text-indigo-500 text-xs">▸</span><span>{th_h}</span></a></li>'
    toc_html = f"""
    <nav class="my-6 rounded-2xl border border-slate-800 bg-slate-900/40 p-5 text-xs sm:text-sm">
      <div class="font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
        <span>📑</span>
        <span>หัวข้อในบทเรียนนี้ (In this lesson)</span>
      </div>
      <ul class="space-y-2 ml-1">
        {toc_links}
      </ul>
    </nav>
    """
    
    # Body sections
    blocks = p.get("blocks", {})
    questions = p.get("questions", {})
    
    sections_html = ""
    for sec in p.get("sections", []):
        h = sec["heading"]
        th_h = get_thai_heading(h)
        clean_id = re.sub(r"[^a-zA-Z0-9]+", "-", h).lower().strip("-")
        
        # Collect raw paragraphs for synthesis & English reference
        raw_paras = [it["text"] for it in sec.get("items", []) if it["type"] == "paragraph"]
        
        # Generate rich Thai prose
        thai_prose_html = generate_thai_section_prose(h, raw_paras)
        
        # Collect tables, code, exam traps, and checkpoints
        sec_elements = ""
        for it in sec.get("items", []):
            itype = it["type"]
            if itype == "exam_trap":
                sec_elements += f"""
                <aside class="my-6 rounded-2xl border-l-4 border-l-amber-500 border border-slate-800 bg-amber-950/20 p-5 text-sm sm:text-base text-slate-200 shadow-sm">
                  <div class="flex items-center gap-2 text-amber-400 font-bold mb-2 text-xs uppercase tracking-wider">
                    <span class="text-base">⚠️</span>
                    <span>จุดที่ข้อสอบชอบหลอก (Exam Trap)</span>
                  </div>
                  <p class="leading-relaxed text-sm text-amber-200/90">{it["text"]}</p>
                </aside>
                """
            elif itype == "table":
                t_headers = "".join(f'<th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-300 border-b border-slate-700 bg-slate-800/80">{th}</th>' for th in it.get("headers", []))
                t_rows = ""
                for r in it.get("rows", []):
                    cells = "".join(f'<td class="px-4 py-3 text-xs sm:text-sm text-slate-300 border-b border-slate-800/60">{td}</td>' for td in r)
                    t_rows += f'<tr class="hover:bg-slate-800/40 transition-colors">{cells}</tr>'
                cap_html = f'<figcaption class="mt-2.5 text-xs text-slate-400 italic text-center">{it["caption"]}</figcaption>' if it.get("caption") else ""
                sec_elements += f"""
                <div class="my-6 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-sm">
                  <table class="min-w-full divide-y divide-slate-800 text-left">
                    <thead><tr>{t_headers}</tr></thead>
                    <tbody>{t_rows}</tbody>
                  </table>
                  {cap_html}
                </div>
                """
            elif itype == "figure_text":
                sec_elements += f"""
                <div class="my-4 p-4 rounded-xl border border-slate-800 bg-slate-900/40 text-xs sm:text-sm text-slate-300 italic font-mono leading-relaxed">
                  {it["text"]}
                </div>
                """
            elif itype == "code":
                sec_elements += f"""
                <div class="my-5 rounded-2xl overflow-hidden border border-slate-800 bg-slate-900 shadow-md font-mono text-xs sm:text-sm">
                  <div class="flex items-center justify-between px-4 py-2.5 bg-slate-800/70 border-b border-slate-800 text-slate-400 text-xs font-semibold">
                    <span>โค้ดตัวอย่างและการตั้งค่า (Code & Schema)</span>
                  </div>
                  <pre class="p-5 text-emerald-300 overflow-x-auto leading-relaxed"><code>{html.escape(it["text"])}</code></pre>
                </div>
                """
            elif itype == "list":
                tag = "ol" if it.get("ordered") else "ul"
                cls = "list-decimal ml-5" if it.get("ordered") else "list-disc ml-5"
                lis = "".join(f'<li class="my-1.5 text-sm sm:text-base text-slate-200 leading-relaxed">{li}</li>' for li in it.get("items", []))
                sec_elements += f'<{tag} class="{cls} my-3 space-y-1">{lis}</{tag}>'
            elif itype == "checkpoint_ref":
                ckey = it["key"]
                b_data = None
                q_data = None
                if ckey.startswith("check:"):
                    bid = ckey[6:]
                    b_data = blocks.get(bid)
                elif ckey.startswith("question:"):
                    qid = ckey[9:]
                    q_data = questions.get(qid)
                sec_elements += render_checkpoint_html(ckey, b_data, q_data)
                
        # Deep Dive
        deep_dive = generate_section_deep_dive(h, sec.get("items", []), p.get("domain_title", ""))
        
        # Folded original English reference
        eng_ref_paras = "".join(f'<p class="my-2">{p_text}</p>' for p_text in raw_paras)
        eng_details_html = f"""
        <details class="my-6 rounded-xl border border-slate-800/80 bg-slate-900/30 p-4 text-xs text-slate-400">
          <summary class="cursor-pointer font-medium text-slate-400 hover:text-indigo-300 flex items-center justify-between select-none">
            <span class="flex items-center gap-1.5">
              <span>📄</span>
              <span>ดูเนื้อหาและศัพท์ต้นฉบับภาษาอังกฤษ (Original English Reference)</span>
            </span>
            <span class="text-xs transition-transform group-open:rotate-180">▼</span>
          </summary>
          <div class="mt-3 pt-3 border-t border-slate-800 space-y-2 text-slate-300 font-sans leading-relaxed text-xs">
            {eng_ref_paras}
          </div>
        </details>
        """
        
        sections_html += f"""
        <section id="{clean_id}" class="mt-14 pt-8 border-t border-slate-800/80">
          <h2 class="text-xl sm:text-2xl font-bold text-white flex items-center gap-3 mb-5 scroll-mt-24">
            <span class="w-3 h-3 rounded-full bg-indigo-500 inline-block shadow-md shadow-indigo-500/50"></span>
            <span>{th_h}</span>
          </h2>
          {thai_prose_html}
          {sec_elements}
          {deep_dive}
          {eng_details_html}
        </section>
        """
        
    # Sources
    sources_html = ""
    if p.get("sources"):
        s_lis = "".join(f'<li><a href="{s["url"]}" target="_blank" class="text-indigo-400 hover:underline flex items-center gap-2 font-mono text-xs sm:text-sm"><span>🔗</span><span>{s["title"]}</span></a></li>' for s in p["sources"])
        sources_html = f"""
        <section class="mt-14 pt-8 border-t border-slate-800">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <span>📚</span>
            <span>เอกสารอ้างอิงทางการจาก Anthropic (Official Citations)</span>
          </div>
          <ul class="space-y-2">
            {s_lis}
          </ul>
        </section>
        """
        
    # Prev / Next nav
    prev_btn = f"""
    <a href="{prev_item['filename']}" class="flex-1 flex flex-col p-4 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/40 hover:bg-slate-800/50 transition-all text-left group">
      <span class="text-xs text-slate-400 flex items-center gap-1 mb-1 group-hover:text-indigo-400">← บทเรียนก่อนหน้า</span>
      <span class="text-sm font-semibold text-slate-200 line-clamp-1">{prev_item['title']}</span>
    </a>
    """ if prev_item else '<div class="flex-1"></div>'
    
    next_btn = f"""
    <a href="{next_item['filename']}" class="flex-1 flex flex-col p-4 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/40 hover:bg-slate-800/50 transition-all text-right items-end group">
      <span class="text-xs text-indigo-400 flex items-center gap-1 mb-1">บทเรียนถัดไป →</span>
      <span class="text-sm font-semibold text-slate-200 line-clamp-1">{next_item['title']}</span>
    </a>
    """ if next_item else '<div class="flex-1"></div>'
    
    nav_footer = f"""
    <nav class="mt-16 pt-8 border-t border-slate-800 flex flex-col sm:flex-row gap-4 justify-between">
      {prev_btn}
      {next_btn}
    </nav>
    """
    
    return f"""<!DOCTYPE html>
<html lang="th" class="dark scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{p.get('title_th', p['title'])} | {course_code} คู่มือเตรียมสอบ Anthropic</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Prompt:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    body {{
      font-family: 'Prompt', 'Inter', sans-serif;
    }}
    code, pre {{
      font-family: 'JetBrains Mono', monospace;
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen selection:bg-indigo-500 selection:text-white">
  <!-- Progress Bar -->
  <div id="progress" class="fixed top-0 left-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 z-50 transition-all duration-150" style="width: 0%"></div>

  <!-- Header -->
  <header class="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <a href="../index.html" class="flex items-center gap-2 text-slate-300 hover:text-white transition">
          <span class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">A</span>
          <span class="font-bold text-sm tracking-wide hidden sm:inline">Anthropic Cert Hub</span>
        </a>
        <span class="text-slate-600">/</span>
        <a href="{course_home}" class="text-xs sm:text-sm font-medium text-indigo-400 hover:text-indigo-300 truncate max-w-[200px] sm:max-w-none">{course_name}</a>
      </div>
      <div class="flex items-center gap-2">
        <a href="{other_course_url}" class="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-300 hover:text-white transition font-medium">
          {other_course_name}
        </a>
      </div>
    </div>
  </header>

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex gap-8">
    <!-- Sidebar -->
    <aside class="hidden lg:block w-72 shrink-0">
      <div class="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-3 space-y-2">
        <div class="flex items-center justify-between pb-3 mb-2 border-b border-slate-800">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-400">สารบัญบทเรียน ({len(catalog)} บท)</span>
          <a href="{course_home}" class="text-xs text-indigo-400 hover:underline">หน้าหลักคอร์ส</a>
        </div>
        {sidebar_html}
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 min-w-0 max-w-4xl mx-auto">
      <article>
        <!-- Header -->
        <header class="mb-8">
          <div class="flex flex-wrap items-center gap-2 mb-3">
            {badges_html}
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
            {p.get('title_th', p['title'])}
          </h1>
          <p class="text-xs sm:text-sm text-indigo-400/90 mt-1.5 font-mono font-medium">
            ต้นฉบับ: {p.get('title_en', p['title'])}
          </p>
          <p class="text-xs text-slate-400 mt-1 font-mono">
            {course_name} · สรุปและขยายความตามเอกสารทางการ 100%
          </p>
        </header>

        {objs_html}
        {kc_html}
        {toc_html}
        {sections_html}
        {sources_html}
        {nav_footer}
      </article>
    </main>
  </div>

  <footer class="mt-20 border-t border-slate-800/80 bg-slate-950 py-8 text-center text-xs text-slate-500">
    <p>Anthropic Claude Certified Developer & Architect Study Hub (ภาษาไทยฉบับสมบูรณ์)</p>
    <p class="mt-1">แปล ขยายความ และรวบรวมเพื่อการเตรียมสอบ CCDV-F & CCAR-P อย่างครบถ้วนทุกบทเรียน</p>
  </footer>

  <script>
    window.addEventListener('scroll', () => {{
      const winScroll = document.documentElement.scrollTop || document.body.scrollTop;
      const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scrolled = (winScroll / height) * 100;
      document.getElementById('progress').style.width = scrolled + '%';
    }});
  </script>
</body>
</html>"""

def render_course_index_page(catalog, course_type):
    course_name = "Anthropic Claude Certified Developer – Foundations (CCDV-F)" if course_type == "foundations" else "Anthropic Claude Certified Architect – Professional (CCAR-P)"
    course_code = "CCDV-F" if course_type == "foundations" else "CCAR-P"
    course_desc = "คู่มือเตรียมสอบเจาะลึก 45 ตอน ครอบคลุมทั้ง 8 Domains สำหรับนักพัฒนาที่ต้องการสร้างระบบด้วย Claude API, Claude Code, Tool Use และ Agent SDK" if course_type == "foundations" else "คู่มือเตรียมสอบสถาปัตยกรรมระดับองค์กร 53 ตอน ครอบคลุมทั้ง 7 Domains สำหรับสถาปนิกที่ออกแบบ Multi-Agent, Enterprise RAG, MCP Governance และความปลอดภัย"
    other_course_url = "../architect/index.html" if course_type == "foundations" else "../foundations/index.html"
    other_course_name = "สลับไปคอร์ส Architect (CCAR-P)" if course_type == "foundations" else "สลับไปคอร์ส Developer (CCDV-F)"

    domains_map = {}
    for item in catalog:
        d = item["domain_no"]
        if d not in domains_map:
            domains_map[d] = {
                "title": item["domain_title"],
                "items": []
            }
        domains_map[d]["items"].append(item)
        
    domain_cards = ""
    for d_no, d_data in sorted(domains_map.items(), key=lambda x: int(x[0])):
        items_html = ""
        for it in d_data["items"]:
            sub_badge = f'<span class="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-indigo-300 shrink-0 font-semibold">{it["sub_no"]}</span>' if it.get("sub_no") else ""
            items_html += f"""
            <a href="{it['filename']}" class="flex items-center justify-between p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/50 hover:bg-slate-800/60 hover:border-indigo-500/40 transition-all group">
              <div class="flex items-center gap-3 min-w-0">
                {sub_badge}
                <div class="min-w-0">
                  <span class="text-sm text-slate-200 group-hover:text-indigo-300 font-medium truncate block">{it['title']}</span>
                  <span class="text-xs text-slate-500 truncate block mt-0.5 font-mono">{it.get('title_en', '')}</span>
                </div>
              </div>
              <span class="text-xs text-slate-500 group-hover:text-indigo-400 shrink-0 font-mono ml-2">อ่านบทเรียน →</span>
            </a>
            """
            
        domain_cards += f"""
        <div class="my-6 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
          <div class="flex items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
              <span>{d_data['title']}</span>
            </h2>
            <span class="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 font-mono">{len(d_data['items'])} บทเรียน</span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            {items_html}
          </div>
        </div>
        """
        
    return f"""<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{course_code} คู่มือเตรียมสอบ Anthropic ภาษาไทยฉบับสมบูรณ์</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Prompt:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    body {{ font-family: 'Prompt', 'Inter', sans-serif; }}
    code, pre {{ font-family: 'JetBrains Mono', monospace; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen">
  <header class="border-b border-slate-800/80 bg-slate-950/80 sticky top-0 z-40 backdrop-blur">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <a href="../index.html" class="flex items-center gap-2 text-slate-300 hover:text-white transition">
          <span class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">A</span>
          <span class="font-bold text-sm tracking-wide">Anthropic Cert Hub</span>
        </a>
        <span class="text-slate-600">/</span>
        <span class="text-sm font-medium text-indigo-400">{course_code}</span>
      </div>
      <div>
        <a href="{other_course_url}" class="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-300 hover:text-white transition font-medium">
          {other_course_name}
        </a>
      </div>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="text-center max-w-3xl mx-auto mb-12">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-3">
        <span>📖 สารบัญหลักสูตรเตรียมสอบทางการ</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
        {course_name}
      </h1>
      <p class="text-slate-400 text-sm sm:text-base leading-relaxed">
        {course_desc}
      </p>
      <div class="mt-6 flex flex-wrap justify-center gap-3">
        <span class="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">📚 ทั้งหมด {len(catalog)} ตอน</span>
        <span class="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">🇹🇭 แปลและขยายความภาษาไทย 100%</span>
        <span class="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">📝 ข้อสอบจำลองและเฉลยละเอียดครบทุกบท</span>
      </div>
    </div>

    <div class="space-y-6">
      {domain_cards}
    </div>
  </main>

  <footer class="mt-20 border-t border-slate-800 py-8 text-center text-xs text-slate-500">
    <p>Anthropic Claude Certified Developer & Architect Study Hub (ภาษาไทยฉบับสมบูรณ์)</p>
  </footer>
</body>
</html>"""

def render_master_portal(f_cat, a_cat):
    return f"""<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Anthropic Claude Certified Developer & Architect Study Hub (ภาษาไทย)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Prompt:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    body {{ font-family: 'Prompt', 'Inter', sans-serif; }}
    code, pre {{ font-family: 'JetBrains Mono', monospace; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen">
  <!-- Header -->
  <header class="border-b border-slate-800/80 bg-slate-950/80 sticky top-0 z-40 backdrop-blur">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">A</span>
        <span class="font-bold text-base tracking-wide text-white">Anthropic Certification Hub</span>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <span class="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">ฉบับภาษาไทยสมบูรณ์</span>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 text-center">
    <div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-4">
      <span>🚀 คู่มือเตรียมสอบรับรองมาตรฐานระดับโลกจาก Anthropic</span>
    </div>
    <h1 class="text-4xl sm:text-5xl font-black text-white tracking-tight leading-tight mb-4">
      Anthropic Claude Certified <br><span class="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Developer & Architect Hub</span>
    </h1>
    <p class="text-slate-400 text-base sm:text-lg max-w-3xl mx-auto leading-relaxed">
      รวบรวมเนื้อหาการสอบทั้ง 2 หลักสูตร แปล ขยายความเชิงลึก และจัดทำแบบฝึกหัดพร้อมข้อสอบจำลองเฉลยละเอียดภาษาไทยครบถ้วน 100% ไม่ข้ามเนื้อหาแม้แต่หัวข้อเดียว
    </p>
  </section>

  <!-- Courses Grid -->
  <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- CCDV-F Card -->
      <div class="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 backdrop-blur hover:border-indigo-500/50 transition-all flex flex-col justify-between shadow-lg">
        <div>
          <div class="flex items-center justify-between gap-2 mb-4">
            <span class="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-bold font-mono">CCDV-F</span>
            <span class="text-xs text-slate-400 font-mono">45 ตอน · 8 Domains</span>
          </div>
          <h2 class="text-2xl font-bold text-white mb-2">Claude Certified Developer – Foundations</h2>
          <p class="text-slate-400 text-sm leading-relaxed mb-6">
            สำหรับนักพัฒนาซอฟต์แวร์ที่สร้างแอปพลิเคชันด้วย Claude Messages API, Claude Code, Tool Use, Prompt Engineering และ Agent SDK พร้อมแบบฝึกหัดจำลองการสอบครบทุกหัวข้อ
          </p>
          <div class="space-y-2 mb-8 text-xs text-slate-300">
            <div class="flex items-center gap-2"><span class="text-blue-400">✓</span><span>Domain 1: Agents and Workflows (สถาปัตยกรรมเอเจนต์)</span></div>
            <div class="flex items-center gap-2"><span class="text-blue-400">✓</span><span>Domain 2: Applications and Integration (Messages API, Sync/Async)</span></div>
            <div class="flex items-center gap-2"><span class="text-blue-400">✓</span><span>Domain 3: Claude Code Operation (CLAUDE.md, Settings)</span></div>
            <div class="flex items-center gap-2"><span class="text-blue-400">✓</span><span>Domain 4-8: Eval, Model Selection, Prompts, Safety, MCPs</span></div>
          </div>
        </div>
        <a href="foundations/index.html" class="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition shadow-lg shadow-indigo-600/30">
          <span>เข้าสู่บทเรียน CCDV-F (45 ตอน)</span>
          <span>→</span>
        </a>
      </div>

      <!-- CCAR-P Card -->
      <div class="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 backdrop-blur hover:border-purple-500/50 transition-all flex flex-col justify-between shadow-lg">
        <div>
          <div class="flex items-center justify-between gap-2 mb-4">
            <span class="px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-bold font-mono">CCAR-P</span>
            <span class="text-xs text-slate-400 font-mono">53 ตอน · 7 Domains</span>
          </div>
          <h2 class="text-2xl font-bold text-white mb-2">Claude Certified Architect – Professional</h2>
          <p class="text-slate-400 text-sm leading-relaxed mb-6">
            สำหรับสถาปนิกและผู้นำทางเทคนิคที่ออกแบบโซลูชันระดับองค์กร ครอบคลุม Multi-Agent Orchestration, Enterprise RAG, MCP Governance, HIPAA/Compliance และ Cost/Latency Optimization
          </p>
          <div class="space-y-2 mb-8 text-xs text-slate-300">
            <div class="flex items-center gap-2"><span class="text-purple-400">✓</span><span>Domain 1: Agentic Architectures & Decompositions</span></div>
            <div class="flex items-center gap-2"><span class="text-purple-400">✓</span><span>Domain 2: Strategic Model Selection & Token Budgeting</span></div>
            <div class="flex items-center gap-2"><span class="text-purple-400">✓</span><span>Domain 3: Tools, Contextual RAG & MCP Security</span></div>
            <div class="flex items-center gap-2"><span class="text-purple-400">✓</span><span>Domain 4-7: Telemetry, Guardrails, Stakeholders, Deployment</span></div>
          </div>
        </div>
        <a href="architect/index.html" class="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm transition shadow-lg shadow-purple-600/30">
          <span>เข้าสู่บทเรียน CCAR-P (53 ตอน)</span>
          <span>→</span>
        </a>
      </div>
    </div>
  </section>

  <!-- Summary Stats -->
  <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="rounded-2xl border border-slate-800 bg-slate-900/30 p-8 grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
      <div>
        <div class="text-3xl font-black text-indigo-400 font-mono">98</div>
        <div class="text-xs text-slate-400 mt-1 uppercase tracking-wide">บทเรียนทั้งหมด</div>
      </div>
      <div>
        <div class="text-3xl font-black text-purple-400 font-mono">15</div>
        <div class="text-xs text-slate-400 mt-1 uppercase tracking-wide">Domains รวมทั้งสองคอร์ส</div>
      </div>
      <div>
        <div class="text-3xl font-black text-emerald-400 font-mono">100%</div>
        <div class="text-xs text-slate-400 mt-1 uppercase tracking-wide">ความครบถ้วนตามเอกสารทางการ</div>
      </div>
      <div>
        <div class="text-3xl font-black text-amber-400 font-mono">ภาษาไทย</div>
        <div class="text-xs text-slate-400 mt-1 uppercase tracking-wide">แปล & ขยายความเจาะลึก</div>
      </div>
    </div>
  </section>

  <footer class="mt-16 border-t border-slate-800 py-8 text-center text-xs text-slate-500">
    <p>Anthropic Claude Certified Developer & Architect Study Hub</p>
    <p class="mt-1">แหล่งเรียนรู้และเตรียมสอบมาตรฐานระดับมืออาชีพสำหรับเทคโนโลยี Claude และ Anthropic</p>
  </footer>
</body>
</html>"""

print("builder_page.py completely updated.")
