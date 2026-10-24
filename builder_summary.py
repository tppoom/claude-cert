import os, sys, json, re, html
from rich_formatter import highlight_tech_terms, split_thai_sentences
from section_translator import get_thai_heading
from domain_knowledge import get_thai_objective, get_thai_key_concept
from quiz_translator import get_thai_explanation, clean_thai_spacing
from exam_summary import score_sentence, parse_trap_text

BASE_DIR = "/Users/tppoom/Desktop/claude cert"
TRANS_DIR = os.path.join(BASE_DIR, "high_quality_translations")

def extract_lesson_cram_data(item, course_type):
    fn = item["filename"]
    json_path = os.path.join(TRANS_DIR, course_type, fn.replace(".html", ".json"))
    
    d = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as fp:
                d = json.load(fp)
        except Exception:
            pass

    title_th = d.get("title") or item.get("title", "")
    title_en = item.get("title_en", "")
    key_concept = d.get("key_concept") or item.get("key_concept", "")
    sub_no = item.get("sub_no", "")
    domain_no = item.get("domain_no", "")
    domain_title = item.get("domain_title", "")
    
    # Collect Traps
    traps = []
    # Collect Key Takeaways
    takeaways = []
    # Collect Tables
    tables = []

    sections = d.get("sections", [])
    for sec in sections:
        sec_h = sec.get("heading", "")
        for it in sec.get("items", []):
            itype = it.get("type")
            if itype == "exam_trap":
                raw_t = it.get("text", "")
                if raw_t:
                    # Could contain multiple traps separated by newlines
                    lines = [ln.strip() for ln in raw_t.split("\n\n") if ln.strip()]
                    for ln in lines:
                        t_q, t_ans = parse_trap_text(ln)
                        if t_q:
                            traps.append({"question": t_q, "reality": t_ans or ln})
            elif itype == "paragraph":
                p_text = it.get("text", "")
                sents = split_thai_sentences(p_text)
                for s in sents:
                    s_clean = re.sub(r'^[:–—\s\.\d\)]+', '', s.strip()).strip()
                    s_clean = re.sub(r'^(?:ดังนั้น|ทั้งนี้|อย่างไรก็ตาม|ในทางกลับกัน|ในขณะเดียวกัน|นอกจากนี้)\s*', '', s_clean).strip()
                    sc = score_sentence(s_clean)
                    if sc >= 3 and len(s_clean) >= 30:
                        takeaways.append((sc, s_clean))
            elif itype == "table":
                cap = it.get("caption", "")
                headers = it.get("headers", [])
                rows = it.get("rows", [])
                if rows and len(rows) <= 6:
                    tables.append({
                        "caption": cap,
                        "headers": headers,
                        "rows": rows
                    })

    # Sort takeaways
    takeaways.sort(key=lambda x: x[0], reverse=True)
    unique_pts = []
    for sc, txt in takeaways:
        if txt not in unique_pts and len(unique_pts) < 3:
            unique_pts.append(txt)

    return {
        "filename": fn,
        "title_th": clean_thai_spacing(title_th),
        "title_en": title_en,
        "key_concept": clean_thai_spacing(key_concept),
        "sub_no": sub_no,
        "domain_no": domain_no,
        "domain_title": domain_title,
        "traps": traps,
        "takeaways": unique_pts,
        "tables": tables[:1] # Keep at most 1 representative table per card to prevent bloating
    }

def render_summary_page(catalog, course_type):
    is_foundations = (course_type == "foundations")
    course_code = "CCDV-F" if is_foundations else "CCAR-P"
    course_name = "Anthropic Claude Certified Developer – Foundations (CCDV-F)" if is_foundations else "Anthropic Claude Certified Architect – Professional (CCAR-P)"
    course_home = "index.html"
    other_course_url = "../architect/summary.html" if is_foundations else "../foundations/summary.html"
    other_course_name = "สรุปคอร์ส Architect (CCAR-P)" if is_foundations else "สรุปคอร์ส Developer (CCDV-F)"
    
    last_item = catalog[-1]
    last_lesson_url = last_item["filename"]
    last_lesson_title = last_item["title"]

    # Group by domain
    domains_map = {}
    for item in catalog:
        d_no = item["domain_no"]
        if d_no not in domains_map:
            domains_map[d_no] = {
                "title": item["domain_title"],
                "items": []
            }
        data = extract_lesson_cram_data(item, course_type)
        domains_map[d_no]["items"].append(data)

    total_lessons = len(catalog)
    total_traps = sum(len(it["traps"]) for d in domains_map.values() for it in d["items"])
    total_domains = len(domains_map)

    # Domain Navigation Tabs
    domain_nav_html = """
    <button onclick="filterDomain('all')" class="domain-tab active px-3.5 py-1.5 rounded-lg text-xs font-semibold transition bg-indigo-600 text-white shadow-xs cursor-pointer" data-domain="all">
      ทั้งหมด ({total_lessons} บท)
    </button>
    """.format(total_lessons=total_lessons)

    for d_no, d_data in sorted(domains_map.items(), key=lambda x: int(x[0])):
        d_title_short = d_data["title"].split("(")[0].strip()
        cnt = len(d_data["items"])
        domain_nav_html += f"""
        <button onclick="filterDomain('{d_no}')" class="domain-tab px-3.5 py-1.5 rounded-lg text-xs font-semibold transition bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 cursor-pointer" data-domain="{d_no}">
          Domain {d_no} ({cnt})
        </button>
        """

    # Domain Sections
    domains_content_html = ""
    for d_no, d_data in sorted(domains_map.items(), key=lambda x: int(x[0])):
        lesson_cards_html = ""
        for it in d_data["items"]:
            # 1. Key Concept
            kc_html = ""
            if it["key_concept"]:
                kc_html = f"""
                <div class="cram-kc p-4 rounded-xl border-l-4 border-l-amber-500 border-y border-r border-amber-500/30 bg-amber-950/20 space-y-1">
                  <div class="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-amber-400">
                    <span>💡</span>
                    <span>แก่นสถาปัตยกรรม (Core Architectural Law)</span>
                  </div>
                  <p class="text-xs sm:text-[13px] text-slate-200 leading-relaxed font-sans">
                    {highlight_tech_terms(it['key_concept'])}
                  </p>
                </div>
                """

            # 2. Exam Traps
            traps_html = ""
            if it["traps"]:
                trap_items = ""
                for t in it["traps"]:
                    q = html.escape(t["question"])
                    ans = highlight_tech_terms(clean_thai_spacing(t["reality"]))
                    trap_items += f"""
                    <div class="p-3 rounded-lg border border-rose-500/30 bg-rose-950/20 space-y-1.5 text-xs">
                      <div class="flex items-start gap-2 text-rose-300 font-semibold leading-relaxed">
                        <span class="text-rose-400 font-bold shrink-0">❌ เข้าใจผิด:</span>
                        <span>{q}</span>
                      </div>
                      <div class="flex items-start gap-2 text-slate-200 border-t border-rose-900/40 pt-1.5 leading-relaxed font-sans">
                        <span class="text-emerald-400 font-bold shrink-0">✓ ความจริง:</span>
                        <span>{ans}</span>
                      </div>
                    </div>
                    """
                traps_html = f"""
                <div class="cram-traps space-y-2">
                  <div class="text-[11px] font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                    <span>⚠️</span>
                    <span>จุดที่ข้อสอบชอบหลอก (Exam Traps & Key Insights)</span>
                  </div>
                  <div class="space-y-2">
                    {trap_items}
                  </div>
                </div>
                """

            # 3. Takeaways
            takeaways_html = ""
            if it["takeaways"]:
                pts_lis = "".join(f'<li class="flex items-start gap-2 text-slate-300 text-xs sm:text-[13px] leading-relaxed"><span class="text-indigo-400 font-bold shrink-0 mt-0.5">•</span><span class="grow">{highlight_tech_terms(p)}</span></li>' for p in it["takeaways"])
                takeaways_html = f"""
                <div class="cram-points space-y-1.5">
                  <div class="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                    <span>📌</span>
                    <span>สรุปสาระสำคัญประจำหัวข้อ (High-Yield Takeaways)</span>
                  </div>
                  <ul class="space-y-1.5 pl-0.5">
                    {pts_lis}
                  </ul>
                </div>
                """

            # 4. Tables
            table_html = ""
            if it["tables"]:
                t = it["tables"][0]
                th_cells = "".join(f'<th class="px-3 py-2 border-b border-slate-700 bg-slate-800 text-white font-semibold text-[11px] text-left">{html.escape(h)}</th>' for h in t["headers"])
                tr_rows = ""
                for r in t["rows"]:
                    tds = "".join(f'<td class="px-3 py-2 border-b border-slate-800 text-slate-300 text-xs">{highlight_tech_terms(clean_thai_spacing(td))}</td>' for td in r)
                    tr_rows += f'<tr class="hover:bg-slate-800/40 transition">{tds}</tr>'
                cap = f'<div class="text-[11px] font-bold text-slate-400 mb-1.5">📊 {html.escape(t["caption"])}</div>' if t["caption"] else ""
                table_html = f"""
                <div class="cram-table overflow-x-auto rounded-lg border border-slate-800 mt-2">
                  {cap}
                  <table class="w-full border-collapse text-left">
                    <thead><tr>{th_cells}</tr></thead>
                    <tbody>{tr_rows}</tbody>
                  </table>
                </div>
                """

            sub_badge = f'<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">[{it["sub_no"]}]</span>' if it["sub_no"] else ""

            search_blob = html.escape(f"{it['sub_no']} {it['title_th']} {it['title_en']} {it['key_concept']} {' '.join(t['question'] + ' ' + t['reality'] for t in it['traps'])}").lower()

            lesson_cards_html += f"""
            <article class="cram-card rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6 shadow-sm hover:border-indigo-500/40 transition-all space-y-4" data-domain="{d_no}" data-search="{search_blob}">
              <div class="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
                <div class="space-y-1 min-w-0">
                  <div class="flex items-center gap-2">
                    {sub_badge}
                    <span class="text-slate-400 text-xs font-medium">Domain {d_no}</span>
                  </div>
                  <h3 class="text-base sm:text-lg font-bold text-white hover:text-indigo-300 transition-colors">
                    <a href="{it['filename']}" class="hover:underline flex items-center gap-1.5">
                      <span>{it['title_th']}</span>
                      <span class="text-slate-500 text-xs font-normal font-sans">↗</span>
                    </a>
                  </h3>
                  <div class="text-xs text-slate-400 font-mono line-clamp-1">{html.escape(it['title_en'])}</div>
                </div>
                <a href="{it['filename']}" class="shrink-0 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition flex items-center gap-1">
                  <span>อ่านบทเต็ม</span>
                  <span>→</span>
                </a>
              </div>

              {kc_html}
              {traps_html}
              {takeaways_html}
              {table_html}
            </article>
            """

        domains_content_html += f"""
        <section class="domain-group space-y-5" data-domain="{d_no}" id="domain-{d_no}">
          <div class="sticky top-20 z-10 py-3 bg-slate-950/90 backdrop-blur border-b border-slate-800 flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <span class="w-3 h-3 rounded-full bg-indigo-500 shadow-md shadow-indigo-500/50"></span>
              <h2 class="text-lg sm:text-xl font-bold text-white tracking-wide">
                Domain {d_no}: {d_data['title']}
              </h2>
            </div>
            <span class="text-xs text-slate-400 font-mono font-medium">{len(d_data['items'])} บทเรียน</span>
          </div>

          <div class="grid grid-cols-1 gap-5">
            {lesson_cards_html}
          </div>
        </section>
        """

    # Assemble Full HTML
    page_html = f"""<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>สรุปสำคัญทุก Domain ก่อนสอบ | {course_code} คู่มือเตรียมสอบ Anthropic</title>
  <meta name="description" content="รวมสรุปสาระสำคัญ แก่นสถาปัตยกรรม และกับดักข้อสอบ (Exam Traps) ครบทุก Domain สำหรับเตรียมสอบ {course_name}">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Fira+Code:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  
  <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
  <style type="text/tailwindcss">
    @theme {{
      --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-thai: 'Chakra Petch', sans-serif;
      --font-mono: 'Fira Code', monospace;
    }}
  </style>

  <style>
    body {{
      font-family: var(--font-thai);
    }}
    code, pre {{
      font-family: var(--font-mono);
    }}
    @media print {{
      header, nav, aside, .no-print, button {{
        display: none !important;
      }}
      body {{
        background: #ffffff !important;
        color: #000000 !important;
      }}
      .cram-card {{
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        color: #0f172a !important;
        page-break-inside: avoid;
        margin-bottom: 1.5rem;
      }}
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-indigo-500 selection:text-white">

  <!-- Top Sticky Bar -->
  <header class="sticky top-0 z-40 bg-slate-900/90 backdrop-blur border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <a href="{course_home}" class="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition font-bold text-sm">
          <span>←</span>
          <span>หน้าหลักคอร์ส</span>
        </a>
        <span class="text-slate-600">/</span>
        <span class="text-slate-300 font-semibold text-xs sm:text-sm truncate">
          {course_code} Final Cram Sheet
        </span>
      </div>

      <div class="flex items-center gap-2">
        <a href="{other_course_url}" class="hidden sm:inline-flex text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition font-medium">
          {other_course_name}
        </a>
        <button onclick="window.print()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1.5 transition cursor-pointer">
          <span>🖨️</span>
          <span>พิมพ์ / PDF</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="border-b border-slate-800 bg-gradient-to-b from-indigo-950/40 via-slate-950 to-slate-950 py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto space-y-6 text-center sm:text-left">
      <div class="flex flex-wrap items-center justify-center sm:justify-start gap-2">
        <span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
          <span>⚡</span>
          <span>สรุปภาพรวมสำคัญก่อนสอบ (Final Exam Cram Sheet)</span>
        </span>
        <span class="px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          {total_domains} Domains · {total_lessons} บทเรียน · {total_traps}+ กับดักข้อสอบ
        </span>
      </div>

      <div>
        <h1 class="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
          รวมสรุปเนื้อหาสำคัญทุก Domain สำหรับทบทวนก่อนสอบ {course_code}
        </h1>
        <p class="text-sm sm:text-base text-slate-300 mt-2 max-w-3xl leading-relaxed">
          คัดกรองเฉพาะแก่นสถาปัตยกรรม (Core Architectural Laws), ข้อกำหนดทางเทคนิค, และกับดักที่ข้อสอบมักลวง (Exam Traps) จัดหมวดหมู่ให้อ่านทบทวนได้อย่างรวดเร็วและครบถ้วนที่สุด
        </p>
      </div>

      <!-- Quick Filter & Search Bar -->
      <div class="pt-2 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div class="relative flex-1">
          <input type="text"
                 id="cram-search"
                 onkeyup="filterContent()"
                 placeholder="ค้นหาตาม Keyword (เช่น query(), CLAUDE.md, Worktree, Headless, Stop reason, Hooks)..."
                 class="w-full px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-900/90 text-white placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition">
          <span class="absolute right-3 top-2.5 text-slate-500 text-xs">🔍</span>
        </div>

        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button onclick="setFilterMode('all')" class="mode-btn active px-3 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white transition cursor-pointer shrink-0" data-mode="all">
            ทั้งหมด
          </button>
          <button onclick="setFilterMode('traps')" class="mode-btn px-3 py-2 rounded-lg text-xs font-bold bg-slate-800 text-rose-300 hover:bg-slate-700 border border-rose-500/30 transition cursor-pointer shrink-0" data-mode="traps">
            ⚠️ เฉพาะกับดักข้อสอบ
          </button>
          <button onclick="setFilterMode('rules')" class="mode-btn px-3 py-2 rounded-lg text-xs font-bold bg-slate-800 text-amber-300 hover:bg-slate-700 border border-amber-500/30 transition cursor-pointer shrink-0" data-mode="rules">
            💡 เฉพาะแก่นกฎเหล็ก
          </button>
        </div>
      </div>

      <!-- Domain Jump Pills -->
      <div class="pt-1 flex flex-wrap items-center gap-1.5">
        <span class="text-xs text-slate-400 font-semibold mr-1">เลือก Domain:</span>
        {domain_nav_html}
      </div>
    </div>
  </section>

  <!-- Main Cram Sheet Body -->
  <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1 space-y-12">
    {domains_content_html}

    <!-- Completion / Navigation Card -->
    <div class="my-12 p-6 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-950 text-center space-y-4 shadow-xl">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500/20 text-2xl text-emerald-300 mb-1">
        🎉
      </div>
      <h3 class="text-lg sm:text-xl font-bold text-white">คุณได้ทบทวนสรุปสำคัญครบทุก Domain แล้ว!</h3>
      <p class="text-slate-300 text-xs sm:text-sm max-w-lg mx-auto leading-relaxed">
        คุณพร้อมเข้าสู่การสอบ {course_name} ด้วยความมั่นใจในทุกแง่มุมสถาปัตยกรรมและรายละเอียดทางเทคนิค
      </p>
      <div class="pt-2 flex flex-wrap items-center justify-center gap-3">
        <a href="{last_lesson_url}" class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs transition border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200">
          <span>← ย้อนกลับไปบทสุดท้าย ({last_item.get('sub_no', 'บทสุดท้าย')})</span>
        </a>
        <a href="{course_home}" class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs transition shadow-md bg-indigo-600 hover:bg-indigo-500 text-white">
          <span>🏠 กลับหน้าหลักคอร์ส</span>
        </a>
      </div>
    </div>
  </main>

  <footer class="border-t border-slate-800 bg-slate-950 py-8 text-center text-xs text-slate-500">
    <p>© 2026 Anthropic Claude Certification Study Companion. All rights reserved.</p>
  </footer>

  <script>
    let currentDomain = 'all';
    let currentMode = 'all';

    function filterDomain(domainId) {{
      currentDomain = domainId;
      document.querySelectorAll('.domain-tab').forEach(btn => {{
        if (btn.getAttribute('data-domain') === domainId) {{
          btn.classList.add('bg-indigo-600', 'text-white');
          btn.classList.remove('bg-slate-800/80', 'text-slate-300');
        }} else {{
          btn.classList.remove('bg-indigo-600', 'text-white');
          btn.classList.add('bg-slate-800/80', 'text-slate-300');
        }}
      }});
      filterContent();
    }}

    function setFilterMode(mode) {{
      currentMode = mode;
      document.querySelectorAll('.mode-btn').forEach(btn => {{
        if (btn.getAttribute('data-mode') === mode) {{
          btn.classList.add('bg-indigo-600', 'text-white');
          btn.classList.remove('bg-slate-800');
        }} else {{
          btn.classList.remove('bg-indigo-600', 'text-white');
          btn.classList.add('bg-slate-800');
        }}
      }});

      // Apply mode visibility
      document.querySelectorAll('.cram-card').forEach(card => {{
        const kc = card.querySelector('.cram-kc');
        const traps = card.querySelector('.cram-traps');
        const pts = card.querySelector('.cram-points');
        const tbl = card.querySelector('.cram-table');

        if (mode === 'traps') {{
          if (kc) kc.style.display = 'none';
          if (traps) traps.style.display = 'block';
          if (pts) pts.style.display = 'none';
          if (tbl) tbl.style.display = 'none';
        }} else if (mode === 'rules') {{
          if (kc) kc.style.display = 'block';
          if (traps) traps.style.display = 'none';
          if (pts) pts.style.display = 'none';
          if (tbl) tbl.style.display = 'none';
        }} else {{
          if (kc) kc.style.display = 'block';
          if (traps) traps.style.display = 'block';
          if (pts) pts.style.display = 'block';
          if (tbl) tbl.style.display = 'block';
        }}
      }});

      filterContent();
    }}

    function filterContent() {{
      const query = (document.getElementById('cram-search').value || '').trim().toLowerCase();

      document.querySelectorAll('.domain-group').forEach(grp => {{
        const dNo = grp.getAttribute('data-domain');
        let anyVisibleInGroup = false;

        grp.querySelectorAll('.cram-card').forEach(card => {{
          const cardDomain = card.getAttribute('data-domain');
          const searchBlob = card.getAttribute('data-search') || '';

          const matchDomain = (currentDomain === 'all' || currentDomain === cardDomain);
          const matchQuery = (!query || searchBlob.includes(query));

          if (matchDomain && matchQuery) {{
            card.style.display = 'block';
            anyVisibleInGroup = true;
          }} else {{
            card.style.display = 'none';
          }}
        }});

        if (anyVisibleInGroup) {{
          grp.style.display = 'block';
        }} else {{
          grp.style.display = 'none';
        }}
      }});
    }}
  </script>
</body>
</html>
"""
    return page_html

if __name__ == "__main__":
    from generate_all import f_catalog, a_catalog
    print("Generating Foundations Cram Sheet (summary.html)...", flush=True)
    f_html = render_summary_page(f_catalog, "foundations")
    with open(os.path.join(BASE_DIR, "foundations", "summary.html"), "w", encoding="utf-8") as f:
        f.write(f_html)
    print("Foundations summary.html written successfully!")

    print("Generating Architect Cram Sheet (summary.html)...", flush=True)
    a_html = render_summary_page(a_catalog, "architect")
    with open(os.path.join(BASE_DIR, "architect", "summary.html"), "w", encoding="utf-8") as f:
        f.write(a_html)
    print("Architect summary.html written successfully!")
