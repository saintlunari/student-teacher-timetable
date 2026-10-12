import openpyxl, glob, os, json

folder = r'C:\Users\user\Documents\CoolMessenger Files\Received Files\5학년2학기진도표'

file_subject_map = {
    '5-2국어.xlsx': ('국어', 'grade5_korean_2'),
    '5-2수학.xlsx': ('수학', 'grade5_math_2'),
    '5-2사회.xlsx': ('사회', 'grade5_social_2'),
    '5-2과학.xlsx': ('과학', 'grade5_science_2'),
    '5-2도덕.xlsx': ('도덕', 'grade5_moral_2'),
    '5-2실과.xlsx': ('실과', 'grade5_practical_2'),
    '5-2체육.xlsx': ('체육', 'grade5_pe_2'),
    '5-2음악.xlsx': ('음악', 'grade5_music_2'),
    '5-2미술.xlsx': ('미술', 'grade5_art_2'),
    '5-2영어.xlsx': ('영어', 'grade5_english_2'),
}

parsed_db = {}
summary = {}

for fname, (subject, db_key) in file_subject_map.items():
    fpath = os.path.join(folder, fname)
    if not os.path.exists(fpath):
        print(f"ERROR: File not found: {fpath}")
        continue
    
    wb = openpyxl.load_workbook(fpath, data_only=True)
    sheet = wb.active
    items = []
    
    for r in range(1, sheet.max_row + 1):
        col1 = sheet.cell(r, 1).value # unit
        col2 = sheet.cell(r, 2).value # topic
        col3 = sheet.cell(r, 3).value # lesson
        col4 = sheet.cell(r, 4).value # totalLesson
        col5 = sheet.cell(r, 5).value # pages
        col10 = sheet.cell(r, 10).value # achievement
        
        # If entire row is empty, skip
        if col1 is None and col2 is None and col3 is None:
            continue
            
        unit = str(col1).strip() if col1 is not None else ''
        topic = str(col2).strip() if col2 is not None else ''
        
        # lesson
        if col3 is not None:
            try:
                lesson = str(int(col3))
            except:
                lesson = str(col3).strip()
        else:
            lesson = '1'
            
        # totalLesson
        if col4 is not None:
            try:
                totalLesson = int(col4)
            except:
                try:
                    totalLesson = int(float(col4))
                except:
                    totalLesson = 1
        else:
            totalLesson = 1
            
        # pages
        pages = str(col5).strip() if col5 is not None else ''
        
        # achievement
        achievement = str(col10).strip() if col10 is not None else ''
        
        item = {
            "grade": 5,
            "semester": "2학기",
            "subject": subject,
            "unit": unit,
            "topic": topic,
            "lesson": lesson,
            "totalLesson": totalLesson,
            "pages": pages,
            "achievement": achievement
        }
        items.append(item)
        
    parsed_db[db_key] = items
    summary[subject] = {
        'db_key': db_key,
        'count': len(items),
        'sample_first': items[0] if items else None,
        'sample_last': items[-1] if items else None
    }

total_count = sum(len(v) for v in parsed_db.values())
print(f"Total parsed items across all 10 subjects: {total_count}")
for s, info in summary.items():
    print(f"  {s} ({info['db_key']}): {info['count']} items")

with open('grade5_curriculum_db.json', 'w', encoding='utf-8') as f:
    json.dump(parsed_db, f, ensure_ascii=False, indent=2)

print("Saved grade5_curriculum_db.json successfully.")
