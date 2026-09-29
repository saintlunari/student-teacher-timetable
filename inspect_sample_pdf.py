import pypdf, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

target_dir = r"C:\Users\user\Desktop\과정안"
sample_pdf = os.path.join(target_dir, "2026 종합실습 교과대표수업 교수학습과정안_과학_박건일.pdf")

reader = pypdf.PdfReader(sample_pdf)
print(f"Total Pages: {len(reader.pages)}")

for idx, page in enumerate(reader.pages):
    print(f"\n=================== PAGE {idx+1} ===================")
    print(page.extract_text())
