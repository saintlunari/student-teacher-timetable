repo_tr = r"C:\Users\user\Documents\GitHub\student-teacher-timetable\test_runner.html"
scratch_tr = r"C:\Users\user\.gemini\antigravity\scratch\student-teacher-timetable\test_runner.html"

with open(repo_tr, "r", encoding="utf-8") as f:
    text = f.read()

count = text.count("id: 'tc16'")
print("Occurrences of tc16 in repo:", count)

if count > 1:
    idx1 = text.find("id: 'tc16'")
    idx2 = text.find("id: 'tc16'", idx1 + 1)

    start1 = text.rfind(",\n      {", 0, idx1)
    end1 = text.find("      }\n", idx1) + len("      }\n")

    new_text = text[:start1] + text[end1:]

    with open(repo_tr, "w", encoding="utf-8") as f:
        f.write(new_text)

    with open(scratch_tr, "w", encoding="utf-8") as f:
        f.write(new_text)

    print("Cleaned duplicate! New count:", new_text.count("id: 'tc16'"))
else:
    print("Already clean!")
