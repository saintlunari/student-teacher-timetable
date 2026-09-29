import os

repo_tr_path = r'C:\Users\user\Documents\GitHub\student-teacher-timetable\test_runner.html'
scratch_tr_path = r'C:\Users\user\.gemini\antigravity\scratch\student-teacher-timetable\test_runner.html'

with open(scratch_tr_path, 'r', encoding='utf-8') as f:
    tr = f.read()

tc16_code = ''',
      {
        id: 'tc16',
        title: '[신규 기능] 1~6학년 교과 DB 확장 아키텍처 및 3학년 2학기 표준 진도표(국어·사회·도덕 163차시) 완벽 탑재 검증',
        desc: '1~6학년 탭 전환 지원, 3학년 2학기 3개 교과(국어 102차시, 사회 45차시, 도덕 16차시 - 총 163차시) 탑재 무결성, 단원 드롭다운·검색 필터링, 교과별 고유 배지 색상 및 Step 2 진도표 테이블 실제 등록 검증',
        run: () => {
          App.loadPreset('grade3', false);
          const frame = document.getElementById('app-frame');
          const doc = (frame && frame.contentDocument) ? frame.contentDocument : document;

          // 1. 3학년 2학기 데이터베이스 무결성 검증
          const kor3Items = App.getCurriculumDbSourceItems(3, '2학기', '국어');
          const soc3Items = App.getCurriculumDbSourceItems(3, '2학기', '사회');
          const mor3Items = App.getCurriculumDbSourceItems(3, '2학기', '도덕');

          const dataCountPass = (kor3Items.length === 102) && (soc3Items.length === 45) && (mor3Items.length === 16);
          const totalGrade3Count = kor3Items.length + soc3Items.length + mor3Items.length;

          // 2. 모달 열기 및 학년 탭 UI 검증
          App.openCurriculumDbModal();
          App.setCurriculumDbGrade(3);

          const gradeTabs = doc.getElementById('db-grade-tabs');
          const grade3Btn = doc.getElementById('db-grade-3');
          const grade2Btn = doc.getElementById('db-grade-2');
          const gradeUiPass = !!(gradeTabs && grade3Btn && grade2Btn && grade3Btn.classList.contains('bg-amber-500'));

          // 3. 3~4학년 교과 탭 동적 렌더링 검증 (국어, 사회, 도덕, 수학, 과학...)
          const subTabs = doc.getElementById('db-subject-tabs');
          const hasSocialTab = subTabs && subTabs.innerText.includes('사회');
          const hasMoralTab = subTabs && subTabs.innerText.includes('도덕');
          const subUiPass = hasSocialTab && hasMoralTab;

          // 4. 사회(45차시) 선택 및 단원 드롭다운 검증
          App.setCurriculumDbSubject('사회');
          const socTableRows = doc.querySelectorAll('#curriculum-db-tbody tr');
          const unitSelect = doc.getElementById('db-unit-select');
          const socTablePass = (socTableRows.length === 45);
          const unitSelectPass = unitSelect && unitSelect.options.length >= 3;

          // 5. 검색 필터링 동작 검증 ('문화' 검색 시 1, 2단원 관련 차시 필터링)
          App.onCurriculumDbSearch('문화');
          const filteredItems = App.getCurrentDbItems();
          const searchPass = (filteredItems.length > 0 && filteredItems.length < 45);
          App.onCurriculumDbSearch('');

          // 6. 도덕(16차시) 선택 후 5단원(4차시) 필터링 및 Step 2 진도표 등록 검증
          App.setCurriculumDbSubject('도덕');
          App.onCurriculumDbUnitChange('5. 너와 나의 공감');
          const moralUnitItems = App.getCurrentDbItems();
          const moralUnitPass = (moralUnitItems.length === 4);

          // 전체 선택 후 진도표에 추가
          App.toggleAllCurriculumDb(true);
          const curLenBefore = App.curriculum.length;
          App.importSelectedCurriculumDb(false);
          const curLenAfter = App.curriculum.length;

          const importedMoral = App.curriculum.filter(c => c.subject === '도덕' && c.unit === '5. 너와 나의 공감');
          const importPass = (curLenAfter === curLenBefore + 4) && (importedMoral.length === 4);

          // 7. 기존 2학년 DB 역호환성 검증 (745차시 불변)
          App.setCurriculumDbGrade(2);
          const kor2Items = App.getCurriculumDbSourceItems(2, '1학기', '국어');
          const math2Items = App.getCurriculumDbSourceItems(2, '1학기', '수학');
          const integ2Items = App.getCurriculumDbSourceItems(2, '1학기', '통합');
          const grade2Pass = (kor2Items.length === 118) && (math2Items.length === 64) && (integ2Items.length === 192);

          App.closeCurriculumDbModal();

          const pass = dataCountPass && gradeUiPass && subUiPass && socTablePass && unitSelectPass && searchPass && moralUnitPass && importPass && grade2Pass;
          return {
            pass,
            message: pass
              ? `3학년 2학기 표준 진도표 163차시(국어:102, 사회:45, 도덕:16) 100% 무결성 로드 완료, 1~6학년 다중 학년 탭 및 3~4학년군 동적 교과 탭 전환 정상, 단원 드롭다운·검색 필터링 및 도덕 4차시 진도표 테이블 실제 등록 완벽 검증 (2학년 745차시 역호환성 보장)`
              : `검증 실패 (dataCount:${dataCountPass} [K:${kor3Items.length},S:${soc3Items.length},M:${mor3Items.length}], gradeUi:${gradeUiPass}, subUi:${subUiPass}, socTable:${socTablePass} [${socTableRows.length}], unitSel:${unitSelectPass}, search:${searchPass}, moralUnit:${moralUnitPass}, import:${importPass}, grade2:${grade2Pass})`
          };
        }
      }
'''

# Find end of tc15 in tr
tc15_idx = tr.find("id: 'tc15'")
assert tc15_idx != -1, "tc15 not found"
end_marker = '    ];'
end_pos = tr.find(end_marker, tc15_idx)
assert end_pos != -1, "end_marker not found"

new_tr = tr[:end_pos] + tc16_code + tr[end_pos:]

# Write to both paths
with open(repo_tr_path, 'w', encoding='utf-8') as f:
    f.write(new_tr)

with open(scratch_tr_path, 'w', encoding='utf-8') as f:
    f.write(new_tr)

# Also sync index.html from repo to scratch
repo_index_path = r'C:\Users\user\Documents\GitHub\student-teacher-timetable\index.html'
scratch_index_path = r'C:\Users\user\.gemini\antigravity\scratch\student-teacher-timetable\index.html'

with open(repo_index_path, 'r', encoding='utf-8') as f:
    idx_content = f.read()

with open(scratch_index_path, 'w', encoding='utf-8') as f:
    f.write(idx_content)

print("Successfully added tc16 and synced test_runner.html & index.html to scratch!")
