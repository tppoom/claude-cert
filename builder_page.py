import os, sys, json, re, html
from bs4 import BeautifulSoup
from render_engine import render_checkpoint_html, render_predict_first_html
from thai_synthesizer import generate_thai_section_prose
from section_translator import get_thai_heading
from domain_knowledge import get_thai_objective, get_thai_key_concept
from quiz_translator import get_thai_explanation, clean_thai_spacing
from rich_formatter import format_readable_content, highlight_tech_terms

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
            <a href="{it['filename']}" class="flex items-center justify-between text-xs py-1.5 pr-2 rounded transition-colors {active_cls}">
              <div class="flex items-center min-w-0 pr-1">
                {sub_prefix}
                <span class="truncate">{it['title']}</span>
              </div>
              <span class="lesson-check-icon shrink-0 text-emerald-400 font-bold ml-1 text-xs hidden" data-filename="{it['filename']}">✓</span>
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
    lesson_filename = p.get('filename', f"lesson-{current_idx:02d}.html")
    lesson_key = f"{course_code}_{lesson_filename}"
    
    sidebar_html = build_sidebar_html(catalog, current_idx, course_type)
    
    # Prev / Next
    prev_item = catalog[current_idx - 2] if current_idx > 1 else None
    next_item = catalog[current_idx] if current_idx < len(catalog) else None
    
    # Badges
    badges_html = ""
    for b in p.get("badges", []):
        badges_html += f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">{clean_thai_spacing(b)}</span> '
    if p.get("sub_no"):
        badges_html = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Subdomain {p["sub_no"]}</span> ' + badges_html
        
    # Objectives (Thai)
    objs_html = ""
    if p.get("objectives"):
        objs_list = "".join(f'<li class="flex items-start gap-3 p-2.5 rounded-xl border border-slate-800/60 bg-slate-900/40 hover:border-indigo-500/30 transition-colors"><span class="text-indigo-400 font-bold shrink-0 mt-0.5">✓</span><span class="text-slate-200">{highlight_tech_terms(clean_thai_spacing(get_thai_objective(obj)))}</span></li>' for obj in p["objectives"])
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
        kc_thai = clean_thai_spacing(get_thai_key_concept(p["key_concept"]))
        kc_html = f"""
        <section class="my-6 rounded-2xl border-l-4 border-l-amber-500 border-y border-r border-slate-800 bg-amber-950/20 p-5 sm:p-6 shadow-sm">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">
            <span class="text-base">💡</span>
            <span>แนวคิดหลักสำคัญ (Key Concept)</span>
          </div>
          <p class="text-sm sm:text-base text-slate-200 leading-relaxed font-medium">
            {highlight_tech_terms(kc_thai)}
          </p>
        </section>
        """
        
    # TOC
    toc_links = ""
    for sec in p.get("sections", []):
        h = sec["heading"]
        th_h = clean_thai_spacing(get_thai_heading(h))
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
        th_h = clean_thai_spacing(get_thai_heading(h))
        clean_id = re.sub(r"[^a-zA-Z0-9]+", "-", h).lower().strip("-")
        
        # Collect raw paragraphs for synthesis & English reference
        raw_paras = [clean_thai_spacing(it["text"]) for it in sec.get("items", []) if it["type"] == "paragraph"]
        
        # Generate rich Thai prose
        thai_prose_html = generate_thai_section_prose(h, raw_paras)
        
        # Render section elements in original narrative order
        sec_elements = ""
        para_idx = 0
        for i, it in enumerate(sec.get("items", [])):
            itype = it["type"]
            if itype == "paragraph":
                p_raw = it["text"]
                p_th = get_thai_explanation(p_raw)
                sec_elements += format_readable_content(p_th, p_raw, is_first_para=(para_idx == 0))
                para_idx += 1
            elif itype == "predict_first":
                sec_elements += render_predict_first_html(it, i)
            elif itype == "exam_trap":
                trap_raw = it["text"]
                trap_th = get_thai_explanation(trap_raw)
                trap_hl = highlight_tech_terms(trap_th)
                sec_elements += f"""
                <aside class="my-6 rounded-2xl border-l-4 border-l-amber-500 border border-slate-800 bg-amber-950/25 p-5 sm:p-6 text-sm sm:text-base text-slate-200 shadow-sm">
                  <div class="flex items-center gap-2 text-amber-400 font-bold mb-2.5 text-xs uppercase tracking-wider">
                    <span class="text-base">⚠️</span>
                    <span>จุดที่ข้อสอบชอบหลอก & จุดสังเกต (Exam Trap & Key Insight)</span>
                  </div>
                  <p class="leading-relaxed sm:leading-loose text-sm sm:text-base text-white font-medium">{html.escape(clean_thai_spacing(trap_raw))}</p>
                  <div class="mt-3 pt-2.5 border-t border-amber-900/40 text-xs sm:text-sm text-amber-200/90 leading-relaxed">
                    <span class="text-amber-400 font-bold mr-1">คำอธิบายเจาะลึก:</span>
                    <span>{trap_hl}</span>
                  </div>
                </aside>
                """
            elif itype == "table":
                t_headers = "".join(f'<th class="px-3.5 py-3 border-b border-slate-700 bg-slate-800/90 break-words align-top"><div class="text-slate-100 font-bold">{html.escape(clean_thai_spacing(get_thai_explanation(th)))}</div><div class="text-[10px] text-slate-400 font-normal font-mono mt-0.5">EN: {html.escape(clean_thai_spacing(th))}</div></th>' for th in it.get("headers", []))
                t_rows = ""
                for r in it.get("rows", []):
                    cells = "".join(f'<td class="px-3.5 py-3 border-b border-slate-800/60 break-words align-top leading-relaxed"><div class="font-medium text-slate-200">{html.escape(clean_thai_spacing(get_thai_explanation(td)))}</div><div class="text-[11px] text-slate-400 font-mono mt-1 pt-1 border-t border-slate-800/40">EN: {html.escape(clean_thai_spacing(td))}</div></td>' for td in r)
                    t_rows += f'<tr class="hover:bg-slate-800/40 transition-colors">{cells}</tr>'
                caption = clean_thai_spacing(it.get("caption", ""))
                cap_html = f'<figcaption class="mt-2.5 text-xs text-slate-400 italic text-center">{clean_thai_spacing(get_thai_explanation(caption))}</figcaption>' if caption else ""
                sec_elements += f"""
                <div class="my-6 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-sm overflow-x-auto no-scrollbar">
                  <table class="w-full border-collapse text-left text-xs sm:text-sm">
                    <thead><tr>{t_headers}</tr></thead>
                    <tbody>{t_rows}</tbody>
                  </table>
                  {cap_html}
                </div>
                """
            elif itype == "figure_text":
                fig_text = clean_thai_spacing(it["text"])
                fig_th = get_thai_explanation(fig_text)
                fig_hl = highlight_tech_terms(fig_th)
                sec_elements += f"""
                <div class="my-4 p-4 rounded-xl border border-slate-800 bg-slate-900/40 text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
                  <div class="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mb-1.5">
                    <span>📌</span>
                    <span>บริบทประกอบ (Context Note):</span>
                  </div>
                  <p class="text-slate-200 font-medium leading-relaxed">{fig_hl}</p>
                  <p class="text-[11px] text-slate-400 mt-1 font-mono">EN: {html.escape(fig_text)}</p>
                </div>
                """
            elif itype == "code":
                caption = clean_thai_spacing(it.get("caption", ""))
                caption = re.sub(r'\s*python$', '', caption, flags=re.I).strip()
                if caption:
                    cap_th = get_thai_explanation(caption)
                    cap_header = f"""
                    <div class="px-4 py-2.5 bg-slate-800/80 border-b border-slate-800 space-y-0.5">
                      <div class="text-xs font-semibold text-slate-200">{html.escape(cap_th)}</div>
                      <div class="text-[11px] text-slate-400 font-mono">EN: {html.escape(caption)}</div>
                    </div>
                    """
                else:
                    cap_header = """
                    <div class="flex items-center justify-between px-4 py-2 bg-slate-800/60 border-b border-slate-800 text-slate-400 text-xs font-semibold">
                      <span>โค้ดตัวอย่างและการตั้งค่า (Code & Schema)</span>
                    </div>
                    """
                sec_elements += f"""
                <div class="my-5 rounded-2xl overflow-hidden border border-slate-800 bg-slate-900 shadow-md font-mono text-xs sm:text-sm">
                  {cap_header}
                  <pre class="p-5 text-emerald-300 overflow-x-auto leading-relaxed"><code>{html.escape(it["text"])}</code></pre>
                </div>
                """
            elif itype == "list":
                tag = "ol" if it.get("ordered") else "ul"
                is_ord = it.get("ordered", False)
                lis = ""
                for l_idx, li in enumerate(it.get("items", [])):
                    li_th = clean_thai_spacing(get_thai_explanation(li))
                    li_hl = highlight_tech_terms(li_th)
                    if is_ord:
                        badge = f'<span class="inline-flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-600/30 text-indigo-300 text-xs font-mono font-bold shrink-0 mt-0.5">{l_idx+1}</span>'
                    else:
                        badge = '<span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-bold shrink-0 mt-0.5">▸</span>'
                    lis += f"""
                    <li class="flex items-start gap-3 p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 text-slate-200 text-sm sm:text-base leading-relaxed hover:border-indigo-500/30 transition-colors shadow-sm">
                      {badge}
                      <div class="grow">{li_hl}</div>
                    </li>
                    """
                sec_elements += f'<{tag} class="space-y-2.5 my-4">{lis}</{tag}>'
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
        
        # Folded original English reference
        eng_ref_paras = "".join(f'<p class="my-2">{html.escape(p_text)}</p>' for p_text in raw_paras)
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
          {eng_details_html}
        </section>
        """
        
    # Sources
    sources_html = ""
    if p.get("sources"):
        s_lis = "".join(f'<li><a href="{s["url"]}" target="_blank" class="text-indigo-400 hover:underline flex items-center gap-2 font-mono text-xs sm:text-sm"><span>🔗</span><span>{clean_thai_spacing(s["title"])}</span></a></li>' for s in p["sources"])
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
        
    # Completion Banner
    completion_box = f"""
    <div class="my-12 p-6 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-950 text-center space-y-4 shadow-xl">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-500/20 text-2xl text-indigo-300 mb-1">
        🎓
      </div>
      <h3 class="text-lg sm:text-xl font-bold text-white">คุณได้ศึกษาเนื้อหาบทเรียนนี้ครบถ้วนแล้ว!</h3>
      <p class="text-slate-300 text-xs sm:text-sm max-w-lg mx-auto leading-relaxed">
        บันทึกความคืบหน้าของคุณลงใน LocalStorage เพื่อติดตามบทเรียนและแบบฝึกหัดที่ทำสำเร็จในหลักสูตร
      </p>
      <div class="pt-2 flex flex-wrap items-center justify-center gap-3">
        <button id="btn-toggle-complete-bottom"
                onclick="toggleLessonComplete()"
                class="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all shadow-md bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer">
          <span>✓</span>
          <span>ทำเครื่องหมายว่าเรียนจบบทนี้แล้ว (Mark Complete)</span>
        </button>
      </div>
    </div>
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
    {completion_box}
    <nav class="mt-8 pt-8 border-t border-slate-800 flex flex-col sm:flex-row gap-4 justify-between">
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
    .no-scrollbar::-webkit-scrollbar {{
      display: none;
    }}
    .no-scrollbar {{
      -ms-overflow-style: none;
      scrollbar-width: none;
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen selection:bg-indigo-500 selection:text-white">
  <!-- Progress Bar -->
  <div id="progress" class="fixed top-0 left-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 z-50 transition-all duration-150" style="width: 0%"></div>

  <!-- Header -->
  <header class="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3 min-w-0">
        <a href="../index.html" class="flex items-center gap-2 text-slate-300 hover:text-white transition shrink-0">
          <span class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">A</span>
          <span class="font-bold text-sm tracking-wide hidden md:inline">Anthropic Cert Hub</span>
        </a>
        <span class="text-slate-600 hidden sm:inline">/</span>
        <a href="{course_home}" class="text-xs sm:text-sm font-medium text-indigo-400 hover:text-indigo-300 truncate max-w-[180px] sm:max-w-xs">{course_name}</a>
      </div>
      
      <!-- Right actions: Progress & Toggle Completed -->
      <div class="flex items-center gap-3 shrink-0">
        <div class="hidden sm:flex items-center gap-2 text-xs text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <span class="text-slate-400">คอร์ส:</span>
          <span id="course-progress-text" class="font-bold text-indigo-400 font-mono">0/{len(catalog)}</span>
          <div class="w-16 bg-slate-800 h-2 rounded-full overflow-hidden shrink-0">
            <div id="course-progress-bar" class="bg-indigo-500 h-full w-0 transition-all duration-300"></div>
          </div>
          <span id="course-progress-pct" class="font-mono text-indigo-300 font-semibold">0%</span>
        </div>
        
        <button id="btn-toggle-complete-top"
                onclick="toggleLessonComplete()"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1.5 transition cursor-pointer">
          <span>○</span>
          <span>ทำเครื่องหมายว่าเรียนจบ</span>
        </button>
        
        <a href="{other_course_url}" class="hidden lg:inline-flex text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-300 hover:text-white transition font-medium">
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
          <div class="flex items-center gap-4 mt-2 text-xs text-slate-400 font-mono">
            <span>{course_name} · สรุปและขยายความตามเอกสารทางการ 100%</span>
            <span id="lesson-quiz-stats" class="text-indigo-400 font-semibold"></span>
          </div>
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

  <!-- Interactive Quiz & LocalStorage Engine -->
  <script>
    const COURSE_CODE = "{course_code}";
    const LESSON_FILENAME = "{lesson_filename}";
    const LESSON_KEY = COURSE_CODE + "_" + LESSON_FILENAME;

    // 1. Interactive Quiz Answer Handler
    function handleQuizAnswer(qid, opt) {{
      const card = document.getElementById('quiz-' + qid);
      if (!card) return;
      
      const correctRaw = card.getAttribute('data-correct') || '';
      const correctAnswers = correctRaw.split(',').map(s => s.trim());
      const isCorrect = correctAnswers.includes(opt);
      
      const fb = document.getElementById('feedback-' + qid);
      const sol = document.getElementById('solution-' + qid);
      const statusBadge = document.getElementById('status-badge-' + qid);
      
      if (isCorrect) {{
        // Reset previously clicked buttons inside this quiz
        card.querySelectorAll('.quiz-opt-btn').forEach(btn => {{
          btn.className = "quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 text-slate-200 text-sm select-none transition-all";
          const b = btn.querySelector('.opt-badge');
          if (b) b.className = "opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0";
          const ic = btn.querySelector('.opt-icon');
          if (ic) ic.classList.add('hidden');
        }});
        
        // Highlight correct option
        const btn = document.getElementById('opt-' + qid + '-' + opt);
        if (btn) {{
          btn.className = "quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-emerald-500/80 bg-emerald-950/40 text-emerald-200 ring-2 ring-emerald-500/30 select-none cursor-pointer transition-all";
          const badge = btn.querySelector('.opt-badge');
          if (badge) badge.className = "opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-emerald-500 text-xs font-bold text-white shrink-0";
          const icon = btn.querySelector('.opt-icon');
          if (icon) {{
            icon.textContent = "✓ ถูกต้อง";
            icon.className = "opt-icon ml-2 shrink-0 font-bold text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300";
            icon.classList.remove('hidden');
          }}
        }}
        
        // Success banner
        if (fb) {{
          fb.className = "my-3 p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-200 text-xs sm:text-sm flex items-center justify-between";
          fb.innerHTML = '<div class="flex items-center gap-2"><span class="text-base">🎉</span><span><strong>ถูกต้องยอดเยี่ยม!</strong> คุณเลือกคำตอบที่ถูกต้องแล้ว</span></div><span class="text-[11px] bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded font-mono">บันทึกผลแล้ว</span>';
          fb.classList.remove('hidden');
        }}
        
        if (statusBadge) statusBadge.classList.remove('hidden');
        if (sol) sol.classList.remove('hidden');
        
        // Save to LocalStorage
        try {{
          const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
          quizProgress[qid] = {{ solved: true, selected: opt, updatedAt: Date.now() }};
          localStorage.setItem('claude_cert_quiz_progress', JSON.stringify(quizProgress));
        }} catch(e) {{}}
        
        updateQuizStats();
      }} else {{
        // Reset previously highlighted buttons inside this quiz
        card.querySelectorAll('.quiz-opt-btn').forEach(btn => {{
          btn.className = "quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-slate-800 text-slate-300 text-sm select-none cursor-pointer transition-all";
          const b = btn.querySelector('.opt-badge');
          if (b) b.className = "opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-xs font-bold text-slate-300 shrink-0";
          const ic = btn.querySelector('.opt-icon');
          if (ic) ic.classList.add('hidden');
        }});

        // Highlight wrong option (can retry immediately)
        const btn = document.getElementById('opt-' + qid + '-' + opt);
        if (btn) {{
          btn.className = "quiz-opt-btn w-full text-left flex items-start gap-3 p-3.5 rounded-xl border border-rose-500/70 bg-rose-950/30 text-rose-200 select-none cursor-pointer transition-all";
          const badge = btn.querySelector('.opt-badge');
          if (badge) badge.className = "opt-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-rose-500 text-xs font-bold text-white shrink-0";
          const icon = btn.querySelector('.opt-icon');
          if (icon) {{
            icon.textContent = "✗ ยังไม่ใช่";
            icon.className = "opt-icon ml-2 shrink-0 font-bold text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300";
            icon.classList.remove('hidden');
          }}
        }}
        
        // Gentle retry message
        if (fb) {{
          fb.className = "my-3 p-3.5 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-200 text-xs sm:text-sm flex items-center justify-between";
          fb.innerHTML = '<div class="flex items-center gap-2"><span class="text-base">❌</span><span><strong>ยังไม่ถูกต้อง:</strong> ตัวเลือกนี้ยังไม่ใช่คำตอบที่ตรงตามเอกสารทางการ คุณสามารถกดเลือกตัวเลือกอื่นใหม่ได้ทันที</span></div><span class="text-[11px] bg-rose-900/60 text-rose-300 px-2 py-0.5 rounded font-mono">ลองใหม่</span>';
          fb.classList.remove('hidden');
        }}

        // Hide statusBadge and solution on wrong answer
        if (statusBadge) statusBadge.classList.add('hidden');
        if (sol) sol.classList.add('hidden');

        // Remove from LocalStorage so incomplete state is accurate
        try {{
          const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
          if (quizProgress[qid]) {{
            delete quizProgress[qid];
            localStorage.setItem('claude_cert_quiz_progress', JSON.stringify(quizProgress));
          }}
        }} catch(e) {{}}
        updateQuizStats();
      }}
    }}

    function toggleSolutionManual(qid) {{
      const sol = document.getElementById('solution-' + qid);
      if (sol) sol.classList.toggle('hidden');
    }}

    function markQuizSolved(qid) {{
      try {{
        const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
        quizProgress[qid] = {{ solved: true, selected: 'REVEALED', updatedAt: Date.now() }};
        localStorage.setItem('claude_cert_quiz_progress', JSON.stringify(quizProgress));
        const statusBadge = document.getElementById('status-badge-' + qid);
        if (statusBadge) statusBadge.classList.remove('hidden');
        updateQuizStats();
      }} catch(e) {{}}
    }}

    // --- MATCHING CHALLENGE ENGINE ---
    const matchSelectedTerm = {{}};
    const matchPairsState = {{}};

    function handleMatchSelectTerm(bid, termIdx) {{
      matchSelectedTerm[bid] = termIdx;
      
      const card = document.getElementById('quiz-' + bid);
      if (!card) return;
      
      card.querySelectorAll('.match-term-btn').forEach(btn => {{
        if (!btn.classList.contains('pointer-events-none')) {{
          btn.className = "match-term-btn w-full text-left p-3.5 rounded-xl border border-slate-700 bg-slate-800/60 text-slate-200 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-2.5";
        }}
      }});
      
      const activeBtn = document.getElementById('match-term-' + bid + '-' + termIdx);
      if (activeBtn && !activeBtn.classList.contains('pointer-events-none')) {{
        activeBtn.className = "match-term-btn w-full text-left p-3.5 rounded-xl border border-indigo-500 bg-indigo-950/50 text-indigo-100 ring-2 ring-indigo-500/40 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-2.5";
      }}
      
      const fb = document.getElementById('feedback-' + bid);
      if (fb) {{
        fb.className = "my-3 p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-indigo-200 text-xs sm:text-sm";
        fb.innerHTML = '👉 <strong>เลือกคำศัพท์ข้อ ' + (termIdx + 1) + ' แล้ว:</strong> คลิกเลือกคำอธิบายฝั่งขวาที่คิดว่าตรงกัน';
        fb.classList.remove('hidden');
      }}
    }}

    function handleMatchSelectDef(bid, targetIdx, totalPairs) {{
      if (matchSelectedTerm[bid] === undefined || matchSelectedTerm[bid] === null) {{
        const fb = document.getElementById('feedback-' + bid);
        if (fb) {{
          fb.className = "my-3 p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs sm:text-sm";
          fb.innerHTML = '⚠️ <strong>กรุณาเลือกคำศัพท์ฝั่งซ้ายก่อน:</strong> คลิกข้อ 1, 2, ... ฝั่งซ้าย แล้วจึงเลือกคำอธิบายฝั่งขวา';
          fb.classList.remove('hidden');
        }}
        return;
      }}
      
      const selectedTerm = matchSelectedTerm[bid];
      const isCorrect = (selectedTerm === targetIdx);
      const fb = document.getElementById('feedback-' + bid);
      
      if (isCorrect) {{
        matchPairsState[bid] = matchPairsState[bid] || new Set();
        matchPairsState[bid].add(targetIdx);
        
        const termBtn = document.getElementById('match-term-' + bid + '-' + targetIdx);
        const defBtn = document.getElementById('match-def-' + bid + '-' + targetIdx);
        const termBadge = document.getElementById('match-badge-term-' + bid + '-' + targetIdx);
        const defBadge = document.getElementById('match-badge-def-' + bid + '-' + targetIdx);
        
        if (termBtn) {{
          termBtn.className = "match-term-btn w-full text-left p-3.5 rounded-xl border border-emerald-500/60 bg-emerald-950/40 text-emerald-200 text-xs sm:text-sm transition opacity-90 select-none pointer-events-none flex items-start gap-2.5";
        }}
        if (termBadge) {{
          termBadge.className = "inline-flex items-center justify-center w-6 h-6 rounded-lg bg-emerald-500 text-white font-bold text-xs shrink-0 mt-0.5";
          termBadge.textContent = "✓";
        }}
        if (defBtn) {{
          defBtn.className = "match-def-btn w-full text-left p-3.5 rounded-xl border border-emerald-500/60 bg-emerald-950/40 text-emerald-200 text-xs sm:text-sm transition opacity-90 select-none pointer-events-none flex items-start gap-2.5";
        }}
        if (defBadge) {{
          defBadge.className = "inline-flex items-center justify-center w-6 h-6 rounded-lg bg-emerald-500 text-white font-bold text-xs shrink-0 mt-0.5";
          defBadge.textContent = "✓ " + (targetIdx + 1);
        }}
        
        matchSelectedTerm[bid] = null;
        
        const count = matchPairsState[bid].size;
        const counterEl = document.getElementById('match-counter-' + bid);
        if (counterEl) counterEl.textContent = 'จับคู่ได้ ' + count + '/' + totalPairs;
        
        if (count === totalPairs) {{
          if (fb) {{
            fb.className = "my-3 p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-500/60 text-emerald-200 text-xs sm:text-sm flex items-center justify-between";
            fb.innerHTML = '<div class="flex items-center gap-2"><span class="text-base">🎉</span><span><strong>ยอดเยี่ยมมาก!</strong> คุณจับคู่ความสัมพันธ์ได้ถูกต้องครบถ้วนสมบูรณ์</span></div><span class="text-[11px] bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded font-mono">ผ่านแล้ว</span>';
            fb.classList.remove('hidden');
          }}
          const sol = document.getElementById('solution-' + bid);
          if (sol) sol.classList.remove('hidden');
          const statusBadge = document.getElementById('status-badge-' + bid);
          if (statusBadge) statusBadge.classList.remove('hidden');
          markQuizSolved(bid);
        }} else {{
          if (fb) {{
            fb.className = "my-3 p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-200 text-xs sm:text-sm";
            fb.innerHTML = '✓ <strong>จับคู่สำเร็จ (' + count + '/' + totalPairs + '):</strong> คลิกเลือกคำศัพท์ข้อถัดไปเพื่อจับคู่ต่อ';
            fb.classList.remove('hidden');
          }}
        }}
      }} else {{
        const defBtn = document.getElementById('match-def-' + bid + '-' + targetIdx);
        if (defBtn) {{
          defBtn.classList.add('border-rose-500', 'bg-rose-950/40');
          setTimeout(() => {{
            defBtn.classList.remove('border-rose-500', 'bg-rose-950/40');
          }}, 800);
        }}
        if (fb) {{
          fb.className = "my-3 p-3 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-200 text-xs sm:text-sm";
          fb.innerHTML = '❌ <strong>ยังไม่ตรงคู่กัน:</strong> คำอธิบายนี้ไม่ใช่ของข้อ ' + (selectedTerm + 1) + ' ลองเลือกคู่ความสัมพันธ์ใหม่อีกครั้ง';
          fb.classList.remove('hidden');
        }}
      }}
    }}

    function resetMatchGame(bid) {{
      delete matchSelectedTerm[bid];
      if (matchPairsState[bid]) matchPairsState[bid].clear();
      
      const card = document.getElementById('quiz-' + bid);
      if (!card) return;
      
      const totalPairs = parseInt(card.getAttribute('data-total-pairs') || '0', 10);
      const counterEl = document.getElementById('match-counter-' + bid);
      if (counterEl) counterEl.textContent = 'จับคู่ได้ 0/' + totalPairs;
      
      card.querySelectorAll('.match-term-btn').forEach((btn, idx) => {{
        btn.className = "match-term-btn w-full text-left p-3.5 rounded-xl border border-slate-700 bg-slate-800/60 hover:border-indigo-400 hover:bg-slate-800/80 text-slate-200 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-2.5";
        const badge = btn.querySelector('span');
        if (badge) {{
          badge.className = "inline-flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-300 font-bold text-xs shrink-0 mt-0.5";
          badge.textContent = idx + 1;
        }}
      }});
      
      card.querySelectorAll('.match-def-btn').forEach(btn => {{
        btn.className = "match-def-btn w-full text-left p-3.5 rounded-xl border border-slate-700 bg-slate-800/60 hover:border-indigo-400 hover:bg-slate-800/80 text-slate-200 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-2.5";
        const badge = btn.querySelector('span');
        if (badge) {{
          badge.className = "inline-flex items-center justify-center w-6 h-6 rounded-lg bg-slate-700 text-slate-300 font-bold text-xs shrink-0 mt-0.5";
          badge.textContent = "?";
        }}
      }});
      
      const fb = document.getElementById('feedback-' + bid);
      if (fb) fb.classList.add('hidden');
    }}

    // --- STEP ORDERING ENGINE ---
    const orderSelections = {{}};

    function handleOrderStepClick(bid, origIdx, totalSteps) {{
      orderSelections[bid] = orderSelections[bid] || [];
      const currentList = orderSelections[bid];
      
      if (currentList.includes(origIdx)) return;
      
      currentList.push(origIdx);
      const rank = currentList.length;
      
      const btn = document.getElementById('order-step-' + bid + '-' + origIdx);
      const badge = document.getElementById('order-badge-' + bid + '-' + origIdx);
      
      if (btn) {{
        btn.className = "order-step-btn w-full text-left p-3.5 rounded-xl border border-indigo-500/70 bg-indigo-950/40 text-indigo-100 text-xs sm:text-sm select-none transition flex items-start gap-3 pointer-events-none";
      }}
      if (badge) {{
        badge.className = "order-badge inline-flex items-center justify-center w-auto px-2 h-7 rounded-lg bg-indigo-600 text-white font-bold text-xs shrink-0 mt-0.5";
        badge.textContent = "ลำดับที่ " + rank;
      }}
      
      const counterEl = document.getElementById('order-counter-' + bid);
      if (counterEl) counterEl.textContent = 'เรียงแล้ว ' + rank + '/' + totalSteps;
      
      if (rank === totalSteps) {{
        let isCorrect = true;
        for (let i = 0; i < totalSteps; i++) {{
          if (currentList[i] !== i) {{
            isCorrect = false;
            break;
          }}
        }}
        
        const fb = document.getElementById('feedback-' + bid);
        const sol = document.getElementById('solution-' + bid);
        const statusBadge = document.getElementById('status-badge-' + bid);
        
        if (isCorrect) {{
          for (let i = 0; i < totalSteps; i++) {{
            const b = document.getElementById('order-badge-' + bid + '-' + i);
            const card = document.getElementById('order-step-' + bid + '-' + i);
            if (b) {{
              b.className = "order-badge inline-flex items-center justify-center w-auto px-2 h-7 rounded-lg bg-emerald-500 text-white font-bold text-xs shrink-0 mt-0.5";
              b.textContent = "✓ ขั้นที่ " + (i + 1);
            }}
            if (card) {{
              card.className = "order-step-btn w-full text-left p-3.5 rounded-xl border border-emerald-500/60 bg-emerald-950/40 text-emerald-200 text-xs sm:text-sm select-none flex items-start gap-3";
            }}
          }}
          if (fb) {{
            fb.className = "my-3 p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-500/60 text-emerald-200 text-xs sm:text-sm flex items-center justify-between";
            fb.innerHTML = '<div class="flex items-center gap-2"><span class="text-base">🎉</span><span><strong>ถูกต้องยอดเยี่ยม!</strong> ลำดับขั้นตอนถูกต้องตามพิมพ์เขียวของ Anthropic</span></div><span class="text-[11px] bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded font-mono">บันทึกผลแล้ว</span>';
            fb.classList.remove('hidden');
          }}
          if (sol) sol.classList.remove('hidden');
          if (statusBadge) statusBadge.classList.remove('hidden');
          markQuizSolved(bid);
        }} else {{
          for (let i = 0; i < totalSteps; i++) {{
            const card = document.getElementById('order-step-' + bid + '-' + currentList[i]);
            if (card) {{
              card.className = "order-step-btn w-full text-left p-3.5 rounded-xl border border-rose-500/60 bg-rose-950/30 text-rose-200 text-xs sm:text-sm select-none flex items-start gap-3";
            }}
          }}
          if (fb) {{
            fb.className = "my-3 p-3.5 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-200 text-xs sm:text-sm flex items-center justify-between";
            fb.innerHTML = '<div class="flex items-center gap-2"><span class="text-base">❌</span><span><strong>ลำดับยังไม่ถูกต้อง:</strong> ขั้นตอนที่จัดวางยังไม่ตรงกับหลักการ กรุณากดปุ่ม "รีเซ็ตลำดับเพื่อลองใหม่"</span></div><button type="button" class="order-retry-btn px-2.5 py-1 rounded bg-rose-900/60 text-rose-300 hover:bg-rose-900 text-xs font-semibold cursor-pointer">ลองใหม่</button>';
            const retryBtn = fb.querySelector('.order-retry-btn');
            if (retryBtn) retryBtn.onclick = () => resetOrderGame(bid);
            fb.classList.remove('hidden');
          }}
        }}
      }}
    }}

    function resetOrderGame(bid) {{
      delete orderSelections[bid];
      const card = document.getElementById('quiz-' + bid);
      if (!card) return;
      
      const totalSteps = parseInt(card.getAttribute('data-total-steps') || '0', 10);
      const counterEl = document.getElementById('order-counter-' + bid);
      if (counterEl) counterEl.textContent = 'เรียงแล้ว 0/' + totalSteps;
      
      card.querySelectorAll('.order-step-btn').forEach(btn => {{
        btn.className = "order-step-btn w-full text-left p-3.5 rounded-xl border border-slate-700 bg-slate-800/60 hover:border-indigo-400 hover:bg-slate-800 text-slate-200 text-xs sm:text-sm cursor-pointer transition select-none flex items-start gap-3";
        const badge = btn.querySelector('.order-badge');
        if (badge) {{
          badge.className = "order-badge inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-700 text-slate-300 font-bold text-xs shrink-0 mt-0.5";
          badge.textContent = "○";
        }}
      }});
      
      const fb = document.getElementById('feedback-' + bid);
      if (fb) fb.classList.add('hidden');
    }}

    // 2. Lesson Completion Handling
    function toggleLessonComplete() {{
      try {{
        const completed = JSON.parse(localStorage.getItem('claude_cert_completed_lessons') || '{{}}');
        const isNowComplete = !completed[LESSON_KEY];
        completed[LESSON_KEY] = isNowComplete;
        localStorage.setItem('claude_cert_completed_lessons', JSON.stringify(completed));
        updateLessonUI(isNowComplete);
        updateSidebarProgress();
      }} catch(e) {{}}
    }}

    function updateLessonUI(isComplete) {{
      const topBtn = document.getElementById('btn-toggle-complete-top');
      const bottomBtn = document.getElementById('btn-toggle-complete-bottom');
      
      if (isComplete) {{
        if (topBtn) {{
          topBtn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm flex items-center gap-1.5 transition cursor-pointer";
          topBtn.innerHTML = '<span>✓</span><span>เรียนจบแล้ว</span>';
        }}
        if (bottomBtn) {{
          bottomBtn.className = "inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all shadow-md bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer";
          bottomBtn.innerHTML = '<span>✓</span><span>เรียนจบแล้ว (คลิกเพื่อยกเลิก)</span>';
        }}
      }} else {{
        if (topBtn) {{
          topBtn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1.5 transition cursor-pointer";
          topBtn.innerHTML = '<span>○</span><span>ทำเครื่องหมายว่าเรียนจบ</span>';
        }}
        if (bottomBtn) {{
          bottomBtn.className = "inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all shadow-md bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer";
          bottomBtn.innerHTML = '<span>✓</span><span>ทำเครื่องหมายว่าเรียนจบบทนี้แล้ว (Mark Complete)</span>';
        }}
      }}
    }}

    // 3. Hydrate state on page load
    document.addEventListener('DOMContentLoaded', () => {{
      // Scroll Progress Bar
      window.addEventListener('scroll', () => {{
        const winScroll = document.documentElement.scrollTop || document.body.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        document.getElementById('progress').style.width = scrolled + '%';
      }});

      // Restore completed status
      try {{
        const completed = JSON.parse(localStorage.getItem('claude_cert_completed_lessons') || '{{}}');
        if (completed[LESSON_KEY]) {{
          updateLessonUI(true);
        }}
      }} catch(e) {{}}
      
      // Restore quiz answers
      try {{
        const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
        document.querySelectorAll('.quiz-card').forEach(card => {{
          const qid = card.getAttribute('data-qid');
          if (quizProgress[qid] && quizProgress[qid].solved) {{
            const opt = quizProgress[qid].selected;
            if (opt === 'REVEALED' || card.getAttribute('data-correct') === 'MATCH' || card.getAttribute('data-correct') === 'ORDER') {{
              const sol = document.getElementById('solution-' + qid);
              if (sol) sol.classList.remove('hidden');
              const statusBadge = document.getElementById('status-badge-' + qid);
              if (statusBadge) statusBadge.classList.remove('hidden');
            }} else {{
              handleQuizAnswer(qid, opt);
            }}
          }}
        }});
      }} catch(e) {{}}
      
      updateSidebarProgress();
      updateQuizStats();
    }});

    function updateQuizStats() {{
      const cards = document.querySelectorAll('.quiz-card');
      if (!cards.length) return;
      let solved = 0;
      try {{
        const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
        cards.forEach(card => {{
          const qid = card.getAttribute('data-qid');
          if (quizProgress[qid] && quizProgress[qid].solved) solved++;
        }});
      }} catch(e) {{}}
      
      const el = document.getElementById('lesson-quiz-stats');
      if (el) {{
        el.textContent = `แบบฝึกหัดบทนี้: ${{solved}}/${{cards.length}} ข้อ`;
      }}
    }}

    function updateSidebarProgress() {{
      try {{
        const completed = JSON.parse(localStorage.getItem('claude_cert_completed_lessons') || '{{}}');
        let count = 0;
        const checks = document.querySelectorAll('.lesson-check-icon');
        checks.forEach(chk => {{
          const fn = chk.getAttribute('data-filename');
          const key = COURSE_CODE + "_" + fn;
          if (completed[key]) {{
            chk.classList.remove('hidden');
            count++;
          }} else {{
            chk.classList.add('hidden');
          }}
        }});
        
        const total = {len(catalog)};
        if (total > 0) {{
          const pct = Math.round((count / total) * 100);
          const txt = document.getElementById('course-progress-text');
          const pctEl = document.getElementById('course-progress-pct');
          const bar = document.getElementById('course-progress-bar');
          if (txt) txt.textContent = `${{count}}/${{total}}`;
          if (pctEl) pctEl.textContent = `${{pct}}%`;
          if (bar) bar.style.width = `${{pct}}%`;
        }}
      }} catch(e) {{}}
    }}
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
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-slate-200 group-hover:text-indigo-300 font-medium truncate block">{it['title']}</span>
                    <span class="badge-completed hidden text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0" data-filename="{it['filename']}">✓ จบแล้ว</span>
                  </div>
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
<html lang="th" class="dark scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{course_name} | Anthropic Cert Hub (ภาษาไทย)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Prompt:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    body {{
      font-family: 'Prompt', 'Inter', sans-serif;
    }}
    code, pre {{
      font-family: 'JetBrains Mono', monospace;
    }}
    .no-scrollbar::-webkit-scrollbar {{
      display: none;
    }}
    .no-scrollbar {{
      -ms-overflow-style: none;
      scrollbar-width: none;
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen">
  <!-- Header -->
  <header class="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <a href="../index.html" class="flex items-center gap-2 text-slate-300 hover:text-white transition">
          <span class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">A</span>
          <span class="font-bold text-sm tracking-wide">Anthropic Cert Hub</span>
        </a>
        <span class="text-slate-600">/</span>
        <span class="text-xs sm:text-sm font-semibold text-white">{course_code}</span>
      </div>
      <div>
        <a href="{other_course_url}" class="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-300 hover:text-white transition font-medium">
          {other_course_name}
        </a>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
    <div class="mb-10 text-center max-w-3xl mx-auto">
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 mb-4 font-mono">
        {course_code} · 100% Complete Syllabus
      </span>
      <h1 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-3">
        {course_name}
      </h1>
      <p class="text-slate-400 text-sm sm:text-base leading-relaxed mb-6">
        {course_desc}
      </p>
      
      <!-- Live Progress Summary Card -->
      <div class="p-6 rounded-2xl border border-indigo-500/30 bg-slate-900/70 backdrop-blur shadow-xl text-left">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div>
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">ความคืบหน้าการเรียนของคุณ (Local Storage)</span>
            <div class="text-2xl font-extrabold text-white">
              <span id="idx-completed-count" class="text-indigo-400 font-mono">0</span> / {len(catalog)} บทเรียน
              <span id="idx-completed-pct" class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono ml-2">0%</span>
            </div>
          </div>
          <div class="text-sm text-slate-300">
            <span class="block text-xs text-slate-400 uppercase tracking-wider mb-1">แบบฝึกหัดที่ทำสำเร็จ</span>
            <span id="idx-quiz-count" class="text-xl font-bold text-emerald-400 font-mono">0</span> ข้อ
          </div>
        </div>
        <div class="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
          <div id="idx-progress-bar" class="bg-indigo-500 h-full w-0 transition-all duration-300"></div>
        </div>
      </div>
    </div>

    <!-- Domain Sections -->
    <div class="space-y-4">
      {domain_cards}
    </div>
  </main>

  <footer class="mt-20 border-t border-slate-800/80 bg-slate-950 py-8 text-center text-xs text-slate-500">
    <p>Anthropic Claude Certified Developer & Architect Study Hub (ภาษาไทยฉบับสมบูรณ์)</p>
    <p class="mt-1">แปล ขยายความ และรวบรวมเพื่อการเตรียมสอบ CCDV-F & CCAR-P อย่างครบถ้วนทุกบทเรียน</p>
  </footer>

  <script>
    const COURSE_CODE = "{course_code}";
    const TOTAL_LESSONS = {len(catalog)};

    document.addEventListener('DOMContentLoaded', () => {{
      try {{
        const completed = JSON.parse(localStorage.getItem('claude_cert_completed_lessons') || '{{}}');
        let count = 0;
        document.querySelectorAll('.badge-completed').forEach(badge => {{
          const fn = badge.getAttribute('data-filename');
          const key = COURSE_CODE + "_" + fn;
          if (completed[key]) {{
            badge.classList.remove('hidden');
            count++;
          }}
        }});
        
        const pct = Math.round((count / TOTAL_LESSONS) * 100);
        document.getElementById('idx-completed-count').textContent = count;
        document.getElementById('idx-completed-pct').textContent = pct + '%';
        document.getElementById('idx-progress-bar').style.width = pct + '%';
      }} catch(e) {{}}
      
      try {{
        const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
        const solvedCount = Object.values(quizProgress).filter(x => x && x.solved).length;
        document.getElementById('idx-quiz-count').textContent = solvedCount;
      }} catch(e) {{}}
    }});
  </script>
</body>
</html>"""


def render_master_portal(f_cat, a_cat):
    total_all = len(f_cat) + len(a_cat)
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
        <span class="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">ฉบับภาษาไทยสมบูรณ์ 100%</span>
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
      รวบรวมเนื้อหาการสอบทั้ง 2 หลักสูตร แปลและขยายความเชิงลึก พร้อมแบบฝึกหัดที่กดเลือกตอบได้จนกว่าจะถูกต้อง และบันทึกความคืบหน้าลงใน LocalStorage
    </p>
    
    <!-- Global Progress Banner -->
    <div class="mt-8 max-w-2xl mx-auto p-5 rounded-2xl border border-indigo-500/30 bg-slate-900/60 backdrop-blur text-left">
      <div class="flex items-center justify-between gap-4 mb-3">
        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">ความคืบหน้ารวมของคุณ:</span>
        <span id="portal-progress-text" class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">0 / {total_all} บทเรียน (0%)</span>
      </div>
      <div class="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
        <div id="portal-progress-bar" class="bg-gradient-to-r from-indigo-500 to-purple-500 h-full w-0 transition-all duration-300"></div>
      </div>
      <div class="mt-3 flex items-center justify-between text-xs text-slate-400">
        <span>ทำแบบฝึกหัดสำเร็จแล้ว: <span id="portal-quiz-count" class="font-bold text-emerald-400 font-mono">0</span> ข้อ</span>
        <button onclick="resetAllProgress()" class="hover:text-rose-400 underline cursor-pointer text-[11px]">รีเซ็ตข้อมูลความคืบหน้า</button>
      </div>
    </div>
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

  <script>
    const TOTAL_ALL = {total_all};

    function updatePortalProgress() {{
      try {{
        const completed = JSON.parse(localStorage.getItem('claude_cert_completed_lessons') || '{{}}');
        const count = Object.values(completed).filter(Boolean).length;
        const pct = Math.round((count / TOTAL_ALL) * 100);
        document.getElementById('portal-progress-text').textContent = `${{count}} / ${{TOTAL_ALL}} บทเรียน (${{pct}}%)`;
        document.getElementById('portal-progress-bar').style.width = pct + '%';
      }} catch(e) {{}}
      
      try {{
        const quizProgress = JSON.parse(localStorage.getItem('claude_cert_quiz_progress') || '{{}}');
        const solvedCount = Object.values(quizProgress).filter(x => x && x.solved).length;
        document.getElementById('portal-quiz-count').textContent = solvedCount;
      }} catch(e) {{}}
    }}

    function resetAllProgress() {{
      if (confirm('คุณต้องการรีเซ็ตข้อมูลความคืบหน้าการเรียนและแบบฝึกหัดทั้งหมดใช่หรือไม่?')) {{
        localStorage.removeItem('claude_cert_completed_lessons');
        localStorage.removeItem('claude_cert_quiz_progress');
        updatePortalProgress();
      }}
    }}

    document.addEventListener('DOMContentLoaded', updatePortalProgress);
  </script>
</body>
</html>"""
