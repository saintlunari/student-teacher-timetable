import json
import os

repo_dir = r"C:\Users\user\Documents\GitHub\student-teacher-timetable"
scratch_dir = r"C:\Users\user\.gemini\antigravity\scratch\student-teacher-timetable"
os.makedirs(scratch_dir, exist_ok=True)

index_file = os.path.join(repo_dir, "index.html")
test_file = os.path.join(repo_dir, "test_runner.html")
grade3_json_path = os.path.join(repo_dir, "grade3_parsed.json")

with open(grade3_json_path, "r", encoding="utf-8") as f:
    grade3_data = json.load(f)

grade3_compact_json = json.dumps(grade3_data, ensure_ascii=False)
total_g3_count = sum(len(v) for v in grade3_data.values())
total_overall_count = 745 + total_g3_count

with open(index_file, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update CURRICULUM_DB_GRADE3 in index.html
start_marker = "var CURRICULUM_DB_GRADE3 = window.CURRICULUM_DB_GRADE3 ="
s_idx = html.find(start_marker)
assert s_idx != -1, "CURRICULUM_DB_GRADE3 not found"
e_idx = html.find(";\n", s_idx)
assert e_idx != -1, "End of CURRICULUM_DB_GRADE3 line not found"

html = html[:s_idx + len(start_marker)] + " " + grade3_compact_json + html[e_idx:]

# Update comment above CURRICULUM_DB_GRADE3
old_comment = "// --- 3학년 2학기 교과 진도표 표준 데이터베이스 (국어 102차시, 사회 45차시, 도덕 16차시 - 총 163차시) ---"
new_comment = f"// --- 3학년 2학기 교과 진도표 표준 데이터베이스 (국어 102차시, 사회 45차시, 도덕 16차시, 수학 64차시, 미술 30차시 - 총 {total_g3_count}차시) ---"
if old_comment in html:
    html = html.replace(old_comment, new_comment)

# 2. Update Modal Total Badge
html = html.replace("총 908차시 탑재 (2·3학년)", f"총 {total_overall_count:,}차시 탑재 (2·3학년)")

# 3. Update gradeCounts in updateCurriculumDbControls
html = html.replace("3: 163,", f"3: {total_g3_count},")

# 4. In getCurriculumDbSourceItems, explicitly handle 수학 and 미술 for Grade 3
g3_check = "if (subject === '도덕') return db3.grade3_moral_2 || [];"
g3_addition = g3_check + "\n            if (subject === '수학') return db3.grade3_math_2 || [];\n            if (subject === '미술') return db3.grade3_art_2 || [];"
if g3_check in html and "db3.grade3_math_2" not in html:
    html = html.replace(g3_check, g3_addition)

# 5. In empty notice message in renderCurriculumDbList
old_notice = "현재 2학년(1·2학기 745차시) 및 3학년(2학기 국어·사회·도덕 163차시)이 완벽하게 등록되어 있습니다."
new_notice = f"현재 2학년(1·2학기 745차시) 및 3학년(2학기 국·사·도·수·미 {total_g3_count}차시)이 완벽하게 등록되어 있습니다."
html = html.replace(old_notice, new_notice)

# Save updated index.html
with open(index_file, "w", encoding="utf-8") as f:
    f.write(html)
with open(os.path.join(scratch_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("index.html updated and synced to scratch!")

# 6. Update test_runner.html tc16
with open(test_file, "r", encoding="utf-8") as f:
    tr = f.read()

tc16_old_title = "3학년 2학기 표준 진도표(국어·사회·도덕 163차시)"
tc16_new_title = f"3학년 2학기 표준 진도표(국·사·도·수·미 {total_g3_count}차시)"
tr = tr.replace(tc16_old_title, tc16_new_title)

old_tc16_desc = "3학년 2학기 3개 교과(국어 102차시, 사회 45차시, 도덕 16차시 - 총 163차시) 탑재 무결성"
new_tc16_desc = f"3학년 2학기 5개 교과(국어 102차시, 사회 45차시, 도덕 16차시, 수학 64차시, 미술 30차시 - 총 {total_g3_count}차시) 탑재 무결성"
tr = tr.replace(old_tc16_desc, new_tc16_desc)

old_items_check = """          const kor3Items = App.getCurriculumDbSourceItems(3, '2학기', '국어');
          const soc3Items = App.getCurriculumDbSourceItems(3, '2학기', '사회');
          const mor3Items = App.getCurriculumDbSourceItems(3, '2학기', '도덕');

          const dataCountPass = (kor3Items.length === 102) && (soc3Items.length === 45) && (mor3Items.length === 16);
          const totalGrade3Count = kor3Items.length + soc3Items.length + mor3Items.length;"""

new_items_check = f"""          const kor3Items = App.getCurriculumDbSourceItems(3, '2학기', '국어');
          const soc3Items = App.getCurriculumDbSourceItems(3, '2학기', '사회');
          const mor3Items = App.getCurriculumDbSourceItems(3, '2학기', '도덕');
          const math3Items = App.getCurriculumDbSourceItems(3, '2학기', '수학');
          const art3Items = App.getCurriculumDbSourceItems(3, '2학기', '미술');

          const dataCountPass = (kor3Items.length === 102) && (soc3Items.length === 45) && (mor3Items.length === 16) && (math3Items.length === 64) && (art3Items.length === 30);
          const totalGrade3Count = kor3Items.length + soc3Items.length + mor3Items.length + math3Items.length + art3Items.length;"""

tr = tr.replace(old_items_check, new_items_check)

old_tc16_msg = "3학년 2학기 표준 진도표 163차시(국어:102, 사회:45, 도덕:16)"
new_tc16_msg = f"3학년 2학기 표준 진도표 {total_g3_count}차시(국어:102, 사회:45, 도덕:16, 수학:64, 미술:30)"
tr = tr.replace(old_tc16_msg, new_tc16_msg)

with open(test_file, "w", encoding="utf-8") as f:
    f.write(tr)
with open(os.path.join(scratch_dir, "test_runner.html"), "w", encoding="utf-8") as f:
    f.write(tr)

print("test_runner.html updated and synced to scratch!")
