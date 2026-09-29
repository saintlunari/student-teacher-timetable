import zipfile, xml.etree.ElementTree as ET, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

hwpx_path = r"C:\Users\user\Desktop\과정안\2026 종합실습 교과대표수업 교수학습과정안_실과_이효우.hwpx"

with zipfile.ZipFile(hwpx_path, 'r') as z:
    sec_xml = z.read("Contents/section0.xml")
    header_xml = z.read("Contents/header.xml")

root = ET.fromstring(sec_xml)

# Find all tables
tables = root.findall('.//{*}tbl')
print(f"Total tables in section0: {len(tables)}")

for idx, tbl in enumerate(tables):
    rows = tbl.findall('.//{*}tr')
    print(f"\n--- Table {idx+1}: {len(rows)} rows ---")
    for r_idx, tr in enumerate(rows[:5]):
        cells = tr.findall('.//{*}tc')
        cell_texts = []
        for tc in cells:
            p_texts = [t.text for t in tc.findall('.//{*}t') if t.text]
            cell_texts.append(' '.join(p_texts).strip())
        print(f"  Row {r_idx+1} ({len(cells)} cells): {cell_texts[:4]}")
