import os, sys, io, json, re, pypdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

target_dir = r"C:\Users\user\Desktop\과정안"
pdf_files = [f for f in os.listdir(target_dir) if f.endswith('.pdf')]

extracted_db = {}

for pdf_name in pdf_files:
    pdf_path = os.path.join(target_dir, pdf_name)
    reader = pypdf.PdfReader(pdf_path)
    full_text = '\n'.join([p.extract_text() for p in reader.pages])
    
    # Extract metadata from Page 1
    p1 = reader.pages[0].extract_text()
    
    # Title
    m_title = re.search(r'([^\n]+과\s*교수·학습안)', p1)
    title = m_title.group(1).strip() if m_title else ""
    
    # Date, Period, Target, Teacher
    m_date = re.search(r'일\s*시\s*([0-9\.\(\)\s월화수목금토일교시]+?)(?=대\s*상|$)', p1)
    m_target = re.search(r'대\s*상\s*([^\n]+?)(?=수\s*업\s*자|$)', p1)
    m_teacher = re.search(r'수\s*업\s*자\s*([^\n]+)', p1)
    
    # Unit, Model, Place
    m_unit = re.search(r'단원\(차시\)\s*([^\n]+?)(?=학습\s*모형|$)', p1)
    m_model = re.search(r'학습\s*모형\s*([^\n]+?)(?=장\s*소|$)', p1)
    m_place = re.search(r'장\s*소\s*([^\n]+)', p1)
    
    # Competencies
    m_core_comp = re.search(r'핵심역량\s*([^\n]+)', p1)
    m_subj_comp = re.search(r'교과역량\s*([^\n]+)', p1)
    
    # Moral & Digital
    m_moral = re.search(r'인성교육\s*가치·덕목\s*([^\n]+)', p1)
    m_digital = re.search(r'디지털\s*활용요소\s*([^\n]+)', p1)
    
    # Achievement standard & Objective
    m_standard = re.search(r'성취기준\s*(\[[^\]]+\][^\n]+)', p1)
    m_goal = re.search(r'학습목표\s*([^\n]+)', p1)
    
    # Key steps in table
    # Check steps
    steps = re.findall(r'(문제\s*확인[^\n]*|탐구[^\n]*|발견[^\n]*|개념[^\n]*|활동\s*1[^\n]*|활동\s*2[^\n]*|활동\s*3[^\n]*|정리[^\n]*)', full_text)
    
    sub_key = pdf_name.replace('2026 종합실습 교과대표수업 교수학습과정안_', '').replace('.pdf', '')
    extracted_db[sub_key] = {
        "file": pdf_name,
        "title": title,
        "date": m_date.group(1).strip() if m_date else "",
        "target": m_target.group(1).strip() if m_target else "",
        "teacher": m_teacher.group(1).strip() if m_teacher else "",
        "unit": m_unit.group(1).strip() if m_unit else "",
        "model": m_model.group(1).strip() if m_model else "",
        "place": m_place.group(1).strip() if m_place else "",
        "core_comp": m_core_comp.group(1).strip() if m_core_comp else "",
        "subj_comp": m_subj_comp.group(1).strip() if m_subj_comp else "",
        "moral": m_moral.group(1).strip() if m_moral else "",
        "digital": m_digital.group(1).strip() if m_digital else "",
        "standard": m_standard.group(1).strip() if m_standard else "",
        "goal": m_goal.group(1).strip() if m_goal else "",
        "page_count": len(reader.pages)
    }

print(f"Extracted metadata for {len(extracted_db)} subjects.")
with open("extracted_lesson_plans_data.json", "w", encoding="utf-8") as f:
    json.dump(extracted_db, f, ensure_ascii=False, indent=2)

for k, v in list(extracted_db.items())[:6]:
    print(f"[{k}] 모형: {v['model']} | 역량: {v['core_comp']} / {v['subj_comp']} | 디지털: {v['digital'][:30]}...")
