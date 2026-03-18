import os

LOG_FILE_PATH = 'mission_computer_main.log'
REPORT_FILE_PATH = 'log_analysis.md'
PROBLEMS_FILE_PATH = 'mission_computer_main_danger.log'
REVERSED_FILE_PATH = 'mission_computer_main_reversed.log'

DANGER_THRESHOLD = 2


DANGER_KEYWORDS = {
    # ── 4점: 사고 그 자체를 나타내는 단어들 ────────────────
    'explosion': 4,      # 폭발
    'exploded': 4,       # 폭발했다
    'destroyed': 4,      # 파괴됨
    'catastrophic': 4,   # 치명적 사고

    # ── 3점: 심각한 이상 상태 ───────────────────────────────
    'unstable': 3,       # 불안정
    'critical': 3,       # 위험 수준
    'failure': 3,        # 실패 / 고장
    'failed': 3,         # 고장났다
    'shutdown': 3,       # 시스템 종료
    'emergency': 3,      # 비상사태
    'lost': 3,           # 신호/연결 손실

    # ── 2점: 경고성 표현 ────────────────────────────────────
    'warning': 2,        # 경고
    'abnormal': 2,       # 비정상
    'unexpected': 2,     # 예상치 못한
    'error': 2,          # 오류
    'issue': 2,          # 문제
    'problem': 2,        # 문제
    'exceeded': 2,       # 초과됨
    'drop': 2,           # 급락
    'leak': 2,           # 누출

    # ── 1점: 약한 주의 신호 ─────────────────────────────────
    'fluctuation': 1,    # 진동/변동
    'intermittent': 1,   # 간헐적
    'delay': 1,          # 지연
    'slow': 1,           # 느림
    'high': 1,           # 높은 (수치가 높다는 의미)
    'low': 1,            # 낮은 (수치가 낮다는 의미)
    'pressure': 1,       # 압력 (문맥상 주의 필요)
    'noticeable': 1,     # 눈에 띄는 (이상 감지 가능성)
    'powered down': 1,   # 전원 꺼짐
}


def read_log_file(file_path):
    lines = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없어요: {file_path}')
        print('       경로와 파일 이름을 다시 확인해 보세요!')

    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없어요: {file_path}')
        print('       파일 속성에서 읽기 권한을 확인해 보세요!')

    except UnicodeDecodeError:
        print(f'[오류] 파일 인코딩 문제가 있어요. CP949로 다시 시도할게요...')
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                lines = f.readlines()
            print('       CP949 인코딩으로 성공적으로 읽었어요!')
        except Exception as error:
            print(f'       재시도도 실패했어요: {error}')

    except OSError as error:
        print(f'[오류] 파일 시스템 오류가 발생했어요: {error}')

    return lines

def parse_log(lines):
    records = []

    for index, line in enumerate(lines):
        line = line.strip()

        if index == 0 or not line:
            continue

        parts = line.split(',', 2)

        if len(parts) == 3:
            records.append({
                'timestamp': parts[0],
                'event': parts[1],
                'message': parts[2],
            })

    return records



# 위험 점수 계산
def calculate_danger_score(message):
    total = 0
    message_lower = message.lower()

    for keyword, score in DANGER_KEYWORDS.items():
        if keyword in message_lower:
            total += score

    return total

def analyze_danger(records):
    for record in records:
        record['score'] = calculate_danger_score(record['message'])

    danger_records = [r for r in records if r['score'] >= DANGER_THRESHOLD]

    root_cause = max(records, key=lambda r: r['score']) if records else None

    if root_cause and root_cause['score'] == 0:
        root_cause = None

    return danger_records, root_cause

def print_log(records):
    print('\n' + '=' * 65)
    print('  미션 컴퓨터 로그 전체 내용 (시간 순)')
    print('=' * 65)

    for record in records:
        score = record['score']

        if score >= 4:
            marker = '[!!!]'   # 매우 위험
        elif score >= 2:
            marker = '[!! ]'   # 위험
        elif score >= 1:
            marker = '[!  ]'   # 주의
        else:
            marker = '[   ]'   # 정상

        print(f'{marker} {record["timestamp"]}  {record["message"]}  (점수: {score})')

    print('=' * 65 + '\n')


# 로그 리스트를 파일로 저장하는 함수
def save_lines(lines, file_name):
    try:
        with open(file_name, 'w', encoding='utf-8') as new_file:
            for line in lines:
                new_file.write(line)

    except PermissionError:
        print(f'[오류] {file_name}의 파일 쓰기 권한이 없어요')
    except OSError as error:
        print(f'[오류] 파일 저장 중 오류가 발생했어요: {error}')


def write_report(records, danger_records, root_cause, ):
    lines = []

    lines.append('# 미션 컴퓨터 사고 분석 보고서\n\n')
    lines.append('---\n\n')

    # 1. 분석 개요
    lines.append('## 1. 분석 개요\n\n')
    lines.append('| 항목 | 내용 |\n')
    lines.append('|------|------|\n')
    lines.append(f'| 전체 로그 수 | {len(records)} 건 |\n')
    lines.append(f'| 분석 시작 시각 | {records[0]["timestamp"]} |\n')
    lines.append(f'| 분석 종료 시각 | {records[-1]["timestamp"]} |\n')
    lines.append(f'| 위험 탐지 기준 점수 | {DANGER_THRESHOLD}점 이상 |\n')
    lines.append(f'| 위험 로그 수 | {len(danger_records)} 건 |\n')
    lines.append('\n')

    # 2. 추정 사고 원인
    lines.append('## 2. 추정 사고 원인 (최고 위험 점수 로그)\n\n')
    if root_cause:
        lines.append(f'- **발생 시각**: {root_cause["timestamp"]}\n')
        lines.append(f'- **위험 점수**: {root_cause["score"]}점\n')
        lines.append(f'- **내용**: {root_cause["message"]}\n')
    else:
        lines.append('- 사고 원인을 특정할 수 없습니다.\n')
    lines.append('\n')

    # 3. 위험 로그 목록 (점수 높은 순 정렬)
    lines.append('## 3. 위험 로그 목록 (점수 높은 순)\n\n')
    lines.append('| 시각 | 점수 | 메시지 |\n')
    lines.append('|------|------|--------|\n')

    # sorted()로 점수 기준 내림차순 정렬
    for r in sorted(danger_records, key=lambda x: x['score'], reverse=True):
        lines.append(f'| {r["timestamp"]} | {r["score"]}점 | {r["message"]} |\n')
    lines.append('\n')

    # 4. 전체 로그 (점수 포함)
    lines.append('## 4. 전체 로그 및 위험 점수\n\n')
    lines.append('| 시각 | 점수 | 메시지 |\n')
    lines.append('|------|------|--------|\n')
    for r in records:
        lines.append(f'| {r["timestamp"]} | {r["score"]}점 | {r["message"]} |\n')
    lines.append('\n')

    # 5. 결론
    lines.append('## 5. 결론 및 권고\n\n')
    lines.append(
        '키워드 위험 점수화 분석 결과, 미션 완료 후 산소 탱크 불안정 및 폭발이 '
        '발생한 것으로 확인됩니다. 미션 성공 이후에도 귀환 단계의 시스템 안전 점검이 '
        '필요하며, 산소 탱크 모니터링 강화를 권고합니다.\n\n'
    )
    lines.append('**권고 사항:**\n\n')
    lines.append('1. 산소 탱크 압력 센서 실시간 모니터링 강화\n')
    lines.append('2. 미션 완료 후에도 전체 시스템 안전 점검 유지\n')
    lines.append('3. 위험 키워드 감지 시 자동 경보 시스템 도입\n')
    lines.append('4. 로그 레벨 체계 재정비 (사고는 반드시 ERROR/CRITICAL로 기록)\n')

    save_lines(lines, REPORT_FILE_PATH)






def main():
    print('Hello Mars')

    lines = read_log_file(LOG_FILE_PATH)

    if not lines:
        print('프로그램을 종료')
        return

    records = parse_log(lines)

    danger_records, root_cause = analyze_danger(records)

    print_log(records)

    print('추정 사고 원인')
    print('-' * 65)
    if root_cause:
        print(f'  ★ 시각  : {root_cause["timestamp"]}')
        print(f'  ★ 점수  : {root_cause["score"]}점')
        print(f'  ★ 내용  : {root_cause["message"]}')
    else:
        print('  위험 로그가 발견되지 않음')
    print('-' * 65)


    write_report(records, danger_records, root_cause)


    print('\n모든 작업이 완료')


if __name__ == '__main__':
    main()