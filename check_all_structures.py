import pypdf, os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

target_dir = r"C:\Users\user\Desktop\과정안"
pdf_files = [f for f in os.listdir(target_dir) if f.endswith('.pdf')]

for pdf_name in pdf_files:
    pdf_path = os.path.join(target_dir, pdf_name)
    reader = pypdf.PdfReader(pdf_path)
    text = '\n'.join([p.extract_text() for p in reader.pages])
    
    # Extract main headings
    headings = re.findall(r'(\d+\.\s*[^\n]+)', text)
    filtered = [h.strip() for h in headings if any(k in h for k in ['교수', '개요', '과정', '판서', '평가', '실태', '단원', '지도'])]
    
    # Check top table fields
    has_target = '일    시' in text or '일시' in text
    has_model = '학습 모형' in text or '학습모형' in text
    has_competency = '핵심역량' in text and '교과역량' in text
    has_moral = '인성교육 가치' in text or '인성교육' in text
    has_digital = '디지털 활용요소' in text or '디지털' in text
    has_focus = '수업 주안점' in text or '수업주안점' in text
    has_board = '판서 계획' in text or '판서' in text
    has_eval_guide = '평가시 유의점' in text or '평가 시 유의점' in text
    
    print(f"[{pdf_name[:25]}] Pgs:{len(reader.pages)} | 일시:{has_target} 모형:{has_model} 역량:{has_competency} 인성:{has_moral} 디지털:{has_digital} 주안점:{has_focus} 판서:{has_board} 유의점:{has_eval_guide}")
