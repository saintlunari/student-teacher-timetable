import json
import os

repo_dir = r'C:\Users\user\Documents\GitHub\student-teacher-timetable'
index_path = os.path.join(repo_dir, 'index.html')
grade3_json_path = os.path.join(repo_dir, 'grade3_parsed.json')

with open(index_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(grade3_json_path, 'r', encoding='utf-8') as f:
    grade3_data = json.load(f)

grade3_compact_json = json.dumps(grade3_data, ensure_ascii=False)

# 1. Step 2 Button Update
old_btn = '📚 2학년 교과 DB 불러오기'
new_btn = '📚 표준 교과 DB 불러오기 (1~6학년)'
assert old_btn in html, "old_btn not found"
html = html.replace(old_btn, new_btn)

# 2. Add CURRICULUM_DB_GRADE3 and CURRICULUM_DATABASES right after CURRICULUM_DB_GRADE2
grade2_marker = 'var CURRICULUM_DB_GRADE2 = window.CURRICULUM_DB_GRADE2 ='
grade2_pos = html.find(grade2_marker)
assert grade2_pos != -1, "CURRICULUM_DB_GRADE2 not found"
# find the semicolon or end of line for CURRICULUM_DB_GRADE2
line_end = html.find('\n', grade2_pos)

grade3_insertion = '\n    // --- 3학년 2학기 교과 진도표 표준 데이터베이스 (국어 102차시, 사회 45차시, 도덕 16차시 - 총 163차시) ---\n'
grade3_insertion += f'    var CURRICULUM_DB_GRADE3 = window.CURRICULUM_DB_GRADE3 = {grade3_compact_json};\n\n'
grade3_insertion += '    // --- 초등학교 1~6학년 교과 진도표 통합 데이터베이스 레지스트리 ---\n'
grade3_insertion += '    var CURRICULUM_DATABASES = window.CURRICULUM_DATABASES = {\n'
grade3_insertion += '      1: null,\n'
grade3_insertion += '      2: CURRICULUM_DB_GRADE2,\n'
grade3_insertion += '      3: CURRICULUM_DB_GRADE3,\n'
grade3_insertion += '      4: null,\n'
grade3_insertion += '      5: null,\n'
grade3_insertion += '      6: null\n'
grade3_insertion += '    };\n'

html = html[:line_end] + grade3_insertion + html[line_end:]

# 3. Modal HTML Markup update
old_modal_controls_start = '<div id="modal-curriculum-db"'
old_modal_controls_end = '<tbody id="curriculum-db-tbody"'
m_start = html.find(old_modal_controls_start)
m_end = html.find(old_modal_controls_end)
assert m_start != -1 and m_end != -1, "Modal markup section not found"

new_modal_markup = '''<div id="modal-curriculum-db" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl max-w-4xl w-full p-6 space-y-4 shadow-2xl flex flex-col max-h-[90vh]">
      <!-- Modal Header -->
      <div class="flex items-center justify-between pb-3 border-b border-slate-200">
        <div class="flex items-center gap-2.5">
          <div class="p-2 rounded-xl bg-amber-100 text-amber-700">
            <i data-lucide="database" class="w-5 h-5"></i>
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>표준 교과 진도표 데이터베이스</span>
              <span id="curriculum-db-total-badge" class="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-semibold border border-amber-200">총 908차시 탑재 (2·3학년)</span>
            </h3>
            <p class="text-xs text-slate-500">1~6학년 표준 교과 진도표 중 원하는 학년·학기·교과의 단원 차시를 검색하여 진도표에 즉시 추가할 수 있습니다.</p>
          </div>
        </div>
        <button onclick="App.closeCurriculumDbModal()" class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Controls: 학년 / 학기 / 교과 / 단원 / 검색어 -->
      <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2.5">
        <!-- Row 1: 학년 선택 + 학기 선택 + 일괄 선택 액션 -->
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-3 text-xs">
            <!-- 학년 탭 -->
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-slate-700 flex items-center gap-1">
                <i data-lucide="graduation-cap" class="w-3.5 h-3.5 text-amber-600"></i> 학년:
              </span>
              <div class="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 gap-0.5" id="db-grade-tabs">
                <!-- JS dynamically renders 1~6학년 buttons -->
              </div>
            </div>

            <div class="h-4 w-px bg-slate-200 hidden sm:block"></div>

            <!-- 학기 탭 -->
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-slate-700">학기:</span>
              <div class="inline-flex rounded-lg border border-slate-200 bg-white p-0.5" id="db-semester-tabs">
                <button type="button" onclick="App.setCurriculumDbSemester('1학기')" id="db-sem-1" class="px-3 py-1 rounded-md font-bold text-sky-700 bg-sky-100 shadow-xs">1학기</button>
                <button type="button" onclick="App.setCurriculumDbSemester('2학기')" id="db-sem-2" class="px-3 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900">2학기</button>
              </div>
            </div>
          </div>

          <!-- 일괄 선택 액션 버튼군 -->
          <div class="flex items-center gap-1.5 text-xs">
            <button type="button" onclick="App.toggleAllCurriculumDb(true)" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg text-slate-700 font-semibold transition">
              전체 선택
            </button>
            <button type="button" onclick="App.toggleAllCurriculumDb(false)" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg text-slate-700 font-medium transition">
              선택 해제
            </button>
          </div>
        </div>

        <!-- Row 2: 교과 탭 -->
        <div class="flex items-center gap-2 text-xs pt-1 border-t border-slate-200/60">
          <span class="font-bold text-slate-700 shrink-0">교과:</span>
          <div class="inline-flex flex-wrap rounded-lg border border-slate-200 bg-white p-0.5 gap-0.5 flex-1" id="db-subject-tabs">
            <!-- JS dynamically renders subject buttons based on grade and semester -->
          </div>
        </div>

        <!-- Row 3: 단원 선택 & 검색창 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          <div>
            <select id="db-unit-select" onchange="App.onCurriculumDbUnitChange(this.value)" class="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white font-medium text-slate-800">
              <option value="">(전체 단원 보기)</option>
            </select>
          </div>
          <div class="relative">
            <input type="text" id="db-search-input" oninput="App.onCurriculumDbSearch(this.value)" placeholder="학습내용 또는 쪽수 검색 (예: 독서, 문화, 6~9)..." class="w-full px-3 py-1.5 pl-8 border border-slate-300 rounded-lg bg-white text-xs">
            <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5"></i>
          </div>
        </div>
      </div>

      <!-- Table View (Scrollable) -->
      <div class="overflow-y-auto border border-slate-200 rounded-xl flex-1 max-h-[420px]">
        <table class="w-full text-xs text-left">
          <thead class="text-slate-600 bg-slate-100 border-b border-slate-200 sticky top-0 z-10 font-bold">
            <tr>
              <th class="py-2 px-3 w-10 text-center">선택</th>
              <th class="py-2 px-2.5 w-12 text-center">순번</th>
              <th class="py-2 px-2.5 w-16 text-center">교과</th>
              <th class="py-2 px-3 w-36">단원</th>
              <th class="py-2 px-3">학습내용</th>
              <th class="py-2 px-2.5 w-20 text-center">차시</th>
              <th class="py-2 px-2.5 w-24 text-center">쪽수</th>
            </tr>
          </thead>
          '''

html = html[:m_start] + new_modal_markup + html[m_end:]

# 4. JavaScript Logic Replacement
js_start_marker = '// 2학년 교과 진도표 데이터베이스 (DB 불러오기 & 모달)'
js_end_marker = 'openCurriculumBatchModal() {'
j_start = html.find(js_start_marker)
j_end = html.find(js_end_marker)
assert j_start != -1 and j_end != -1, "JS section markers not found"

new_js = '''// 1~6학년 교과 진도표 데이터베이스 (DB 불러오기 & 모달)
      // -----------------------------------------------------------------------
      getCurriculumDb(grade = 2) {
        if (grade === 3) return CURRICULUM_DB_GRADE3;
        return CURRICULUM_DB_GRADE2;
      },
      curriculumDbState: {
        grade: 2,
        semester: '1학기',
        subject: '국어',
        unit: '',
        search: '',
        selectedIndices: new Set()
      },

      openCurriculumDbModal() {
        this.curriculumDbState.selectedIndices.clear();
        // 기본 학급 정보의 학년(예: '3학년 1반' -> 3) 자동 감지
        const gradeMatch = (this.config && this.config.gradeClass) ? String(this.config.gradeClass).match(/([1-6])학년/) : null;
        if (gradeMatch) {
          const g = parseInt(gradeMatch[1], 10);
          this.curriculumDbState.grade = g;
          if (g === 3 && (!this.curriculumDbState.semester || this.curriculumDbState.semester === '1학기')) {
            this.curriculumDbState.semester = '2학기';
          }
        }
        this.updateCurriculumDbControls();
        this.renderCurriculumDbList();
        document.getElementById('modal-curriculum-db').classList.remove('hidden');
        lucide.createIcons();
      },

      closeCurriculumDbModal() {
        document.getElementById('modal-curriculum-db').classList.add('hidden');
      },

      setCurriculumDbGrade(grade) {
        this.curriculumDbState.grade = grade;
        this.curriculumDbState.unit = '';
        this.curriculumDbState.selectedIndices.clear();

        // 3학년의 경우 2학기 데이터(국어, 사회, 도덕) 우선 안내
        if (grade === 3) {
          if (this.curriculumDbState.semester !== '2학기') {
            this.curriculumDbState.semester = '2학기';
          }
          if (!['국어', '사회', '도덕'].includes(this.curriculumDbState.subject)) {
            this.curriculumDbState.subject = '국어';
          }
        } else if (grade === 1 || grade === 2) {
          if (!['국어', '수학', '통합', '바생', '슬생', '즐생'].includes(this.curriculumDbState.subject)) {
            this.curriculumDbState.subject = '국어';
          }
        } else {
          this.curriculumDbState.subject = '국어';
        }

        this.updateCurriculumDbControls();
        this.renderCurriculumDbList();
      },

      setCurriculumDbSemester(sem) {
        this.curriculumDbState.semester = sem;
        this.curriculumDbState.unit = '';
        this.curriculumDbState.selectedIndices.clear();
        this.updateCurriculumDbControls();
        this.renderCurriculumDbList();
      },

      setCurriculumDbSubject(sub) {
        this.curriculumDbState.subject = sub;
        this.curriculumDbState.unit = '';
        this.curriculumDbState.selectedIndices.clear();
        this.updateCurriculumDbControls();
        this.renderCurriculumDbList();
      },

      onCurriculumDbUnitChange(unit) {
        this.curriculumDbState.unit = unit;
        this.renderCurriculumDbList();
      },

      onCurriculumDbSearch(query) {
        this.curriculumDbState.search = query.trim().toLowerCase();
        this.renderCurriculumDbList();
      },

      getCurriculumDbSourceItems(arg1, arg2, arg3) {
        let grade, semester, subject;
        if (arg3 !== undefined) {
          grade = arg1;
          semester = arg2;
          subject = arg3;
        } else if (arg2 !== undefined) {
          grade = this.curriculumDbState.grade || 2;
          semester = arg1;
          subject = arg2;
        } else {
          grade = this.curriculumDbState.grade || 2;
          semester = this.curriculumDbState.semester;
          subject = this.curriculumDbState.subject;
        }

        if (grade === 2) {
          const db2 = window.CURRICULUM_DB_GRADE2 || {};
          if (subject === '국어') {
            return db2[semester === '1학기' ? 'grade2_korean_1' : 'grade2_korean_2'] || [];
          }
          if (subject === '수학') {
            return db2[semester === '1학기' ? 'grade2_math_1' : 'grade2_math_2'] || [];
          }
          const integKey = (semester === '1학기') ? 'grade2_integrated_1' : 'grade2_integrated_2';
          return db2[integKey] || [];
        }

        if (grade === 3) {
          const db3 = window.CURRICULUM_DB_GRADE3 || {};
          if (semester === '2학기') {
            if (subject === '국어') return db3.grade3_korean_2 || [];
            if (subject === '사회') return db3.grade3_social_2 || [];
            if (subject === '도덕') return db3.grade3_moral_2 || [];
          } else if (semester === '1학기') {
            if (subject === '국어') return db3.grade3_korean_1 || [];
            if (subject === '사회') return db3.grade3_social_1 || [];
            if (subject === '도덕') return db3.grade3_moral_1 || [];
          }
          const semNum = (semester === '1학기') ? '1' : '2';
          const subKeyMap = {
            '국어': 'korean', '사회': 'social', '도덕': 'moral', '수학': 'math',
            '과학': 'science', '음악': 'music', '미술': 'art', '체육': 'pe', '영어': 'english'
          };
          const key = `grade3_${subKeyMap[subject] || subject}_${semNum}`;
          return db3[key] || [];
        }

        // 1, 4, 5, 6학년 확장 대응
        const dbRegistry = window.CURRICULUM_DATABASES || {};
        const db = dbRegistry[grade];
        if (!db) return [];
        const semNum = (semester === '1학기') ? '1' : '2';
        return db[`grade${grade}_${subject}_${semNum}`] || [];
      },

      updateCurriculumDbControls() {
        const { grade, semester, subject } = this.curriculumDbState;

        // 1. 학년 탭 렌더링
        const gradeTabs = document.getElementById('db-grade-tabs');
        if (gradeTabs) {
          const gradeCounts = {
            1: 0,
            2: 745,
            3: 163,
            4: 0,
            5: 0,
            6: 0
          };
          let gradeHtml = '';
          [1, 2, 3, 4, 5, 6].forEach(g => {
            const isActive = (g === grade);
            const cnt = gradeCounts[g];
            const badge = cnt > 0
              ? ` <span class="text-[10px] ${isActive ? 'text-amber-100 font-bold' : 'text-slate-400'}">(${cnt})</span>`
              : ` <span class="text-[10px] ${isActive ? 'text-amber-100' : 'text-slate-300'}">(0)</span>`;
            const activeCls = 'px-3 py-1 rounded-md font-bold text-white bg-amber-500 shadow-xs text-xs flex items-center gap-0.5 cursor-pointer';
            const inactiveCls = 'px-2.5 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 text-xs flex items-center gap-0.5 cursor-pointer';
            gradeHtml += `<button type="button" onclick="App.setCurriculumDbGrade(${g})" id="db-grade-${g}" class="${isActive ? activeCls : inactiveCls}">${g}학년${badge}</button>`;
          });
          gradeTabs.innerHTML = gradeHtml;
        }

        // 2. 학기 탭 활성화 상태
        const sem1Btn = document.getElementById('db-sem-1');
        const sem2Btn = document.getElementById('db-sem-2');
        if (sem1Btn && sem2Btn) {
          if (semester === '1학기') {
            sem1Btn.className = 'px-3 py-1 rounded-md font-bold text-sky-700 bg-sky-100 shadow-xs cursor-pointer';
            sem2Btn.className = 'px-3 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900 cursor-pointer';
          } else {
            sem2Btn.className = 'px-3 py-1 rounded-md font-bold text-sky-700 bg-sky-100 shadow-xs cursor-pointer';
            sem1Btn.className = 'px-3 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900 cursor-pointer';
          }
        }

        // 3. 교과 탭 동적 구성
        const subjectTabs = document.getElementById('db-subject-tabs');
        if (subjectTabs) {
          let subjects = [];
          if (grade <= 2) {
            subjects = [
              { id: '국어', label: '국어' },
              { id: '수학', label: '수학' },
              { id: '통합', label: '통합(전체)' },
              { id: '바생', label: '바생' },
              { id: '슬생', label: '슬생' },
              { id: '즐생', label: '즐생' }
            ];
          } else if (grade <= 4) {
            subjects = [
              { id: '국어', label: '국어' },
              { id: '사회', label: '사회' },
              { id: '도덕', label: '도덕' },
              { id: '수학', label: '수학' },
              { id: '과학', label: '과학' },
              { id: '음악', label: '음악' },
              { id: '미술', label: '미술' },
              { id: '체육', label: '체육' },
              { id: '영어', label: '영어' }
            ];
          } else {
            subjects = [
              { id: '국어', label: '국어' },
              { id: '사회', label: '사회' },
              { id: '도덕', label: '도덕' },
              { id: '수학', label: '수학' },
              { id: '과학', label: '과학' },
              { id: '실과', label: '실과' },
              { id: '음악', label: '음악' },
              { id: '미술', label: '미술' },
              { id: '체육', label: '체육' },
              { id: '영어', label: '영어' }
            ];
          }

          let subHtml = '';
          subjects.forEach(s => {
            const isActive = (s.id === subject);
            let items = this.getCurriculumDbSourceItems(grade, semester, s.id);
            if (s.id === '바생' || s.id === '슬생' || s.id === '즐생') {
              items = items.filter(it => it.subject === s.id);
            }
            const count = items.length;
            const countTag = count > 0
              ? `<span class="text-[10px] ml-1 font-bold ${isActive ? 'text-indigo-800' : 'text-slate-500'}">(${count})</span>`
              : `<span class="text-[10px] ml-1 opacity-40">(0)</span>`;
            const activeCls = 'px-2.5 py-1 rounded-md font-bold text-indigo-700 bg-indigo-100 shadow-xs text-xs cursor-pointer';
            const inactiveCls = 'px-2.5 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 text-xs cursor-pointer';
            subHtml += `<button type="button" onclick="App.setCurriculumDbSubject('${s.id}')" class="${isActive ? activeCls : inactiveCls}">${s.label}${countTag}</button>`;
          });
          subjectTabs.innerHTML = subHtml;
        }

        // 4. 단원 선택 드롭다운 갱신
        const sourceItems = this.getCurriculumDbSourceItems(grade, semester, subject);
        let filterForUnits = sourceItems;
        if (subject === '바생' || subject === '슬생' || subject === '즐생') {
          filterForUnits = sourceItems.filter(it => it.subject === subject);
        }
        const units = Array.from(new Set(filterForUnits.map(it => it.unit).filter(Boolean)));
        const unitSelect = document.getElementById('db-unit-select');
        if (unitSelect) {
          let opts = `<option value="">(전체 ${units.length}개 단원/대주제 보기)</option>`;
          units.forEach(u => {
            const count = filterForUnits.filter(it => it.unit === u).length;
            opts += `<option value="${u}" ${this.curriculumDbState.unit === u ? 'selected' : ''}>${u} (${count}차시)</option>`;
          });
          unitSelect.innerHTML = opts;
        }
      },

      getCurrentDbItems() {
        const { grade, semester, subject, unit, search } = this.curriculumDbState;
        const sourceItems = this.getCurriculumDbSourceItems(grade, semester, subject);

        return sourceItems.filter((it, origIdx) => {
          it._origIdx = origIdx;
          if (subject === '바생' || subject === '슬생' || subject === '즐생') {
            if (it.subject !== subject) return false;
          }
          if (unit && it.unit !== unit) return false;
          if (search) {
            const matchTopic = (it.topic || '').toLowerCase().includes(search);
            const matchUnit = (it.unit || '').toLowerCase().includes(search);
            const matchPages = (it.pages || '').toLowerCase().includes(search);
            const matchSubj = (it.subject || '').toLowerCase().includes(search);
            if (!matchTopic && !matchUnit && !matchPages && !matchSubj) return false;
          }
          return true;
        });
      },

      renderCurriculumDbList() {
        const tbody = document.getElementById('curriculum-db-tbody');
        if (!tbody) return;
        const items = this.getCurrentDbItems();
        const countBadge = document.getElementById('curriculum-db-total-badge');
        if (countBadge) {
          countBadge.innerText = `${this.curriculumDbState.grade}학년 ${this.curriculumDbState.semester} ${this.curriculumDbState.subject} (표시: ${items.length}차시)`;
        }

        if (items.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-slate-400">
            <div class="space-y-1">
              <p class="font-bold text-slate-600">${this.curriculumDbState.grade}학년 ${this.curriculumDbState.semester} ${this.curriculumDbState.subject} 표준 데이터가 준비 중입니다.</p>
              <p class="text-xs text-slate-400 font-normal">현재 2학년(1·2학기 745차시) 및 3학년(2학기 국어·사회·도덕 163차시)이 완벽하게 등록되어 있습니다.</p>
            </div>
          </td></tr>`;
          this.updateCurriculumDbSelectedCount();
          return;
        }

        const subjColorMap = {
          '국어': 'bg-indigo-50 text-indigo-700 border-indigo-200',
          '수학': 'bg-emerald-50 text-emerald-700 border-emerald-200',
          '사회': 'bg-amber-50 text-amber-700 border-amber-200',
          '도덕': 'bg-teal-50 text-teal-700 border-teal-200',
          '과학': 'bg-purple-50 text-purple-700 border-purple-200',
          '음악': 'bg-pink-50 text-pink-700 border-pink-200',
          '미술': 'bg-orange-50 text-orange-700 border-orange-200',
          '체육': 'bg-lime-50 text-lime-700 border-lime-200',
          '영어': 'bg-cyan-50 text-cyan-700 border-cyan-200',
          '실과': 'bg-yellow-50 text-yellow-700 border-yellow-200',
          '슬생': 'bg-amber-50 text-amber-700 border-amber-200',
          '즐생': 'bg-rose-50 text-rose-700 border-rose-200',
          '바생': 'bg-sky-50 text-sky-700 border-sky-200'
        };

        let html = '';
        items.forEach((it, displayIdx) => {
          const isChecked = this.curriculumDbState.selectedIndices.has(it._origIdx);
          const badgeClass = subjColorMap[it.subject] || 'bg-slate-100 text-slate-700 border-slate-200';
          html += `
            <tr class="hover:bg-amber-50/60 transition ${isChecked ? 'bg-amber-50/90 font-medium' : ''}">
              <td class="py-2 px-3 text-center">
                <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="App.toggleCurriculumDbItem(${it._origIdx}, this.checked)" class="rounded text-amber-600 focus:ring-amber-500 cursor-pointer w-4 h-4">
              </td>
              <td class="py-2 px-2.5 text-center text-slate-400 text-xs">${displayIdx + 1}</td>
              <td class="py-2 px-2 text-center text-xs">
                <span class="px-2 py-0.5 rounded-full font-bold text-[11px] border ${badgeClass}">${it.subject}</span>
              </td>
              <td class="py-2 px-3 font-semibold text-slate-800 text-xs">${it.unit}</td>
              <td class="py-2 px-3 text-slate-900 text-xs">${it.topic}</td>
              <td class="py-2 px-2.5 text-center font-bold text-indigo-700 text-xs">${it.lesson}/${it.totalLesson}</td>
              <td class="py-2 px-2.5 text-center text-slate-600 text-xs font-medium">${it.pages}</td>
            </tr>
          `;
        });
        tbody.innerHTML = html;
        this.updateCurriculumDbSelectedCount();
      },

      toggleCurriculumDbItem(origIdx, checked) {
        if (checked) {
          this.curriculumDbState.selectedIndices.add(origIdx);
        } else {
          this.curriculumDbState.selectedIndices.delete(origIdx);
        }
        this.updateCurriculumDbSelectedCount();
      },

      toggleAllCurriculumDb(selectAll) {
        const items = this.getCurrentDbItems();
        if (selectAll) {
          items.forEach(it => this.curriculumDbState.selectedIndices.add(it._origIdx));
        } else {
          items.forEach(it => this.curriculumDbState.selectedIndices.delete(it._origIdx));
        }
        this.renderCurriculumDbList();
      },

      updateCurriculumDbSelectedCount() {
        const countSpan = document.getElementById('curriculum-db-selected-count');
        if (countSpan) {
          countSpan.innerText = `${this.curriculumDbState.selectedIndices.size}개`;
        }
      },

      importSelectedCurriculumDb(showAlert = true) {
        const selected = Array.from(this.curriculumDbState.selectedIndices);
        if (selected.length === 0) {
          if (showAlert) alert('진도표에 추가할 차시를 1개 이상 선택해주세요.');
          return;
        }

        const { grade, semester, subject } = this.curriculumDbState;
        const sourceItems = this.getCurriculumDbSourceItems(grade, semester, subject);

        selected.sort((a, b) => a - b);

        const replaceMode = document.getElementById('db-replace-mode')?.checked;
        if (replaceMode) {
          if (showAlert && !confirm(`기존에 등록된 진도표(${this.curriculum.length}차시)를 모두 지우고, 선택한 ${selected.length}개 차시로 새로 교체하시겠습니까?`)) {
            return;
          }
          this.curriculum = [];
        }

        selected.forEach(idx => {
          const it = sourceItems[idx];
          if (!it) return;
          this.curriculum.push({
            id: 'c' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            subject: it.subject,
            pages: it.pages || '',
            lesson: String(it.lesson || '1'),
            totalLesson: it.totalLesson || 1,
            unit: it.unit || '',
            topic: it.unit ? `${it.unit} - ${it.topic}` : it.topic,
            isDemo: false,
            designatedTeacher: ''
          });
        });

        this.renderCurriculumTable();
        this.closeCurriculumDbModal();
        if (showAlert) {
          alert(`${grade}학년 ${semester} ${subject} ${selected.length}개 차시가 진도표에 성공적으로 등록되었습니다!`);
        }
      },

      '''

html = html[:j_start] + new_js + html[j_end:]

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Successfully updated index.html with Grade 3 data and multi-grade UI architecture!")
