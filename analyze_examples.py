import pypdf, os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

target_dir = r"C:\Users\user\Desktop\과정안"
pdf_files = [f for f in os.listdir(target_dir) if f.endswith('.pdf')]

summary = []

for pdf_name in pdf_files:
    pdf_path = os.path.join(target_dir, pdf_name)
    reader = pypdf.PdfReader(pdf_path)
    text = ''
    for p in reader.pages:
        text += p.extract_text() + '\n---PAGE---\n'
    
    has_sec1 = ('단원 안내' in text) or ('단원의 안내' in text) or ('단원안내' in text)
    has_sec2 = ('본시 교수' in text) or ('본시 교수·학습' in text)
    has_sec3 = ('실태' in text) or ('학생 실태' in text)
    has_sec4 = ('참고문헌' in text) or ('참고 문헌' in text)
    has_board = ('판서 계획' in text) or ('판서계획' in text)
    has_eval = ('평가 계획' in text) or ('과정중심' in text)
    
    match = re.search(r'과정안_([^_]+)_([^\.]+)\.pdf', pdf_name)
    sub = match.group(1) if match else '?'
    tch = match.group(2) if match else '?'
    
    summary.append({
        'name': pdf_name,
        'subject': sub,
        'teacher': tch,
        'pages': len(reader.pages),
        'sec1': has_sec1,
        'sec2': has_sec2,
        'sec3': has_sec3,
        'sec4': has_sec4,
        'board': has_board,
        'eval': has_eval
    })

print(f"Total analyzed: {len(summary)}")
for s in summary:
    print(f"{s['subject']}_{s['teacher']} ({s['pages']}p): 단원안내={s['sec1']}, 본시실제={s['sec2']}, 판서={s['board']}, 평가={s['eval']}, 실태={s['sec3']}, 참고문헌={s['sec4']}")
