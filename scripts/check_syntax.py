with open('test_script.js', encoding='utf-8') as f:
    text = f.read()

stack = []
i = 0
n = len(text)
line = 1
col = 1
errors = []

while i < n:
    ch = text[i]
    if ch == '\n':
        line += 1
        col = 1
        i += 1
        continue
    elif ch == '/' and i + 1 < n and text[i+1] == '/':
        while i < n and text[i] != '\n':
            i += 1
        continue
    elif ch == '/' and i + 1 < n and text[i+1] == '*':
        i += 2
        while i + 1 < n and not (text[i] == '*' and text[i+1] == '/'):
            if text[i] == '\n':
                line += 1
                col = 1
            i += 1
        i += 2
        continue
    elif ch in ('"', "'", '`'):
        quote = ch
        i += 1
        while i < n and text[i] != quote:
            if text[i] == '\\':
                i += 2
                continue
            if text[i] == '\n':
                line += 1
                col = 1
            i += 1
        i += 1
        continue
    elif ch == '{':
        stack.append((line, col))
    elif ch == '}':
        if not stack:
            errors.append(f'Extra }} at line {line}:{col}')
        else:
            stack.pop()
    i += 1
    col += 1

print('Remaining unmatched { on stack:', len(stack))
for item in stack[-10:]:
    print(f'Unclosed {{ at line {item[0]}:{item[1]}')
for err in errors[:10]:
    print(err)
