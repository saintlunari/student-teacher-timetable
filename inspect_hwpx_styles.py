import zipfile, xml.etree.ElementTree as ET, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

hwpx_path = r"C:\Users\user\Desktop\과정안\2026 종합실습 교과대표수업 교수학습과정안_실과_이효우.hwpx"

with zipfile.ZipFile(hwpx_path, 'r') as z:
    header_xml = z.read("Contents/header.xml")

root = ET.fromstring(header_xml)

# Fonts
fonts = [f.attrib.get('face') for f in root.findall('.//{*}font')]
print("Fonts used:", set(fonts))

# Char shapes (font size, bold, etc.)
char_shapes = root.findall('.//{*}charShape')
print(f"Total char shapes: {len(char_shapes)}")
for idx, cs in enumerate(char_shapes[:10]):
    height = int(cs.attrib.get('height', 1000)) / 100 # pt
    bold = cs.attrib.get('bold', '0')
    italic = cs.attrib.get('italic', '0')
    textColor = cs.attrib.get('textColor', '#000000')
    print(f"  CharShape {idx}: size={height}pt bold={bold} italic={italic} color={textColor}")

# Para shapes (margins, indent, line spacing, align)
para_shapes = root.findall('.//{*}paraShape')
print(f"\nTotal para shapes: {len(para_shapes)}")
for idx, ps in enumerate(para_shapes[:10]):
    align = ps.attrib.get('align', 'JUSTIFY')
    lineSpacing = ps.attrib.get('lineSpacing', '160')
    indent = ps.attrib.get('indent', '0')
    print(f"  ParaShape {idx}: align={align} lineSpacing={lineSpacing}% indent={indent}")
