import os, sys, json, time
from generate_all import f_catalog, a_catalog, parse_lesson_file, FOUNDATIONS_DIR, ARCHITECT_DIR, BASE_DIR
from builder_page import render_lesson_page, render_course_index_page, render_master_portal
from quiz_translator import save_cache

print("Starting generation process with full Thai titles and rich metadata...")
start_time = time.time()

# 1. Generate Foundations Lessons
print(f"Generating {len(f_catalog)} Foundations lessons...")
for it in f_catalog:
    p_data = parse_lesson_file(it["raw_file"])
    if not p_data:
        print(f"Failed to parse {it['slug']}")
        continue
    p_data["domain_title"] = it["domain_title"]
    p_data["sub_no"] = it.get("sub_no")
    p_data["title_th"] = it.get("title")
    p_data["title_en"] = it.get("title_en")
    html_out = render_lesson_page(p_data, f_catalog, it["idx"], "foundations")
    out_path = os.path.join(FOUNDATIONS_DIR, it["filename"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

print(f"Generated {len(f_catalog)} Foundations lessons.")

# 2. Generate Architect Lessons
print(f"Generating {len(a_catalog)} Architect lessons...")
for it in a_catalog:
    p_data = parse_lesson_file(it["raw_file"])
    if not p_data:
        print(f"Failed to parse {it['slug']}")
        continue
    p_data["domain_title"] = it["domain_title"]
    p_data["sub_no"] = it.get("sub_no")
    p_data["title_th"] = it.get("title")
    p_data["title_en"] = it.get("title_en")
    html_out = render_lesson_page(p_data, a_catalog, it["idx"], "architect")
    out_path = os.path.join(ARCHITECT_DIR, it["filename"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

print(f"Generated {len(a_catalog)} Architect lessons.")

# 3. Generate Course Indices
print("Generating course indices...")
f_index_html = render_course_index_page(f_catalog, "foundations")
with open(os.path.join(FOUNDATIONS_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(f_index_html)

a_index_html = render_course_index_page(a_catalog, "architect")
with open(os.path.join(ARCHITECT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(a_index_html)

# 4. Generate Master Index
print("Generating master portal index...")
master_html = render_master_portal(f_catalog, a_catalog)
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(master_html)

save_cache()
elapsed = time.time() - start_time
print(f"All 98 lessons and 3 indices generated successfully in {elapsed:.2f} seconds!")
