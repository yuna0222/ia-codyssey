"""
javis.py - 음성 녹음 및 STT(Speech to Text) 기능 구현

문제 7: 음성 녹음 (녹음 / 재생 / 날짜별 조회)
문제 8: 음성에서 문자로 (STT + CSV 저장 + 키워드 검색)
"""

import os
import csv
import wave
import struct
import datetime
import subprocess
import sys

# ─────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────

RECORDS_DIR = 'records'
TRANSCRIPTS_DIR = 'transcripts'
SAMPLE_RATE = 44100


# ─────────────────────────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────────────────────────

def make_dir(path):
    """폴더가 없으면 생성한다."""
    if not os.path.exists(path):
        os.makedirs(path)


def time_str(seconds):
    """초를 MM:SS 형식 문자열로 변환한다."""
    return '{:02d}:{:02d}'.format(int(seconds) // 60, int(seconds) % 60)


def wav_to_csv_path(wav_path):
    """WAV 파일 경로로부터 대응하는 CSV 경로를 반환한다."""
    base = os.path.splitext(os.path.basename(wav_path))[0]
    return os.path.join(TRANSCRIPTS_DIR, base + '.csv')


# ─────────────────────────────────────────────────────────────────
# 문제 7: 음성 녹음
# ─────────────────────────────────────────────────────────────────

def record_audio(file_path):
    """
    마이크로 음성을 녹음하여 PCM int16 WAV 파일로 저장한다.
    Enter 키를 누르면 녹음이 종료된다.
    """
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print('pip install sounddevice numpy')
        return False

    print('녹음을 시작합니다. Enter를 누르면 녹음이 종료됩니다...')

    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            callback=callback
    ):
        input()

    if not frames:
        print('녹음된 데이터가 없습니다.')
        return False

    # float32 → int16 변환 후 PCM WAV 저장
    audio = np.concatenate(frames).flatten()
    audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    print(f'녹음 완료: {file_path}')
    return True


def play_audio(file_path):
    """녹음 파일을 재생한다. Mac은 afplay, 그 외는 sounddevice를 사용한다."""
    if not os.path.exists(file_path):
        print(f'파일을 찾을 수 없습니다: {file_path}')
        return

    print(f'재생 중: {os.path.basename(file_path)}')

    if sys.platform == 'darwin':
        subprocess.run(['afplay', file_path])
        print('재생 완료.')
        return

    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print('pip install sounddevice numpy')
        return

    with wave.open(file_path, 'rb') as wf:
        rate = wf.getframerate()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
        channels = wf.getnchannels()

    dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
    dtype = dtype_map.get(sw, np.int16)
    audio = np.frombuffer(raw, dtype=dtype)
    if channels > 1:
        audio = audio.reshape(-1, channels)
    audio = audio.astype(np.float32) / np.iinfo(dtype).max

    sd.play(audio, samplerate=rate)
    sd.wait()
    print('재생 완료.')


def list_records():
    """records 폴더의 WAV 파일 목록을 반환한다."""
    if not os.path.exists(RECORDS_DIR):
        return []
    return sorted([
        f for f in os.listdir(RECORDS_DIR) if f.endswith('.wav')
    ])


def list_records_by_date(start_date, end_date):
    """날짜 범위(YYYYMMDD)에 해당하는 녹음 파일 목록을 출력한다."""
    try:
        start = datetime.datetime.strptime(start_date, '%Y%m%d')
        end = datetime.datetime.strptime(end_date, '%Y%m%d')
    except ValueError:
        print('날짜 형식 오류. 예: 20260101')
        return

    found = []
    for name in list_records():
        try:
            date = datetime.datetime.strptime(name.split('-')[0], '%Y%m%d')
            if start <= date <= end:
                found.append(name)
        except ValueError:
            continue

    if found:
        print(f'\n{start_date} ~ {end_date} 범위의 녹음 파일:')
        for name in found:
            print(f'  {name}')
    else:
        print('해당 날짜 범위의 파일이 없습니다.')


def select_file():
    """파일 목록을 출력하고 사용자가 선택한 파일 경로를 반환한다."""
    files = list_records()
    if not files:
        print('녹음 파일이 없습니다.')
        return None

    print('\n녹음 파일 목록:')
    for i, name in enumerate(files, 1):
        print(f'  {i}. {name}')

    choice = input('파일 번호 선택: ').strip()
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        return os.path.join(RECORDS_DIR, files[int(choice) - 1])

    print('올바른 번호를 입력해주세요.')
    return None


# ─────────────────────────────────────────────────────────────────
# 문제 8: STT
# ─────────────────────────────────────────────────────────────────

def fix_wav_format(file_path):
    """
    float32 WAV(format 3)를 PCM int16(format 1)으로 변환한다.
    SpeechRecognition은 PCM WAV만 지원하기 때문에 필요하다.
    """
    with open(file_path, 'rb') as f:
        f.seek(20)
        fmt_tag = struct.unpack('<H', f.read(2))[0]

    if fmt_tag != 3:
        return  # 이미 PCM이면 변환 불필요

    print('  [포맷 변환] float32 → PCM int16 변환 중...')

    with open(file_path, 'rb') as f:
        f.seek(20)
        fmt_tag = struct.unpack('<H', f.read(2))[0]
        f.seek(22)
        channels = struct.unpack('<H', f.read(2))[0]
        sample_rate = struct.unpack('<I', f.read(4))[0]
        f.seek(16)
        fmt_size = struct.unpack('<I', f.read(4))[0]
        f.seek(20 + fmt_size)  # fmt 청크 끝으로 이동

        # data 청크 탐색
        while True:
            chunk_id = f.read(4)
            chunk_size = struct.unpack('<I', f.read(4))[0]
            if chunk_id == b'data':
                raw = f.read(chunk_size)
                break
            f.read(chunk_size)

    # float32 → int16
    count = len(raw) // 4
    floats = struct.unpack(f'<{count}f', raw)
    int16 = [int(max(-1.0, min(1.0, v)) * 32767) for v in floats]
    int16_raw = struct.pack(f'<{count}h', *int16)

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_raw)

    print('  [포맷 변환] 완료')


def transcribe_audio(file_path, language='ko-KR'):
    """
    WAV 파일을 STT 변환하여 (시작시간, 텍스트) 목록을 반환한다.

    파일 길이에 따라 청크 단위를 자동 조정한다.
      60초 이상 → 30초 단위
      10초 이상 → 10초 단위
      10초 미만 →  5초 단위
    """
    try:
        import speech_recognition as sr
    except ImportError:
        print('pip install SpeechRecognition')
        return []

    fix_wav_format(file_path)

    recognizer = sr.Recognizer()
    results = []

    try:
        with sr.AudioFile(file_path) as source:
            total = source.DURATION
    except ValueError as err:
        print(f'파일 열기 실패: {err}')
        return []

    # 파일 길이에 따라 청크 크기 자동 결정
    if total >= 60:
        chunk = 30.0
    elif total >= 10:
        chunk = 10.0
    else:
        chunk = 5.0

    print(f'\nSTT 변환 중: {os.path.basename(file_path)}')
    print(f'  길이: {total:.1f}초 / 청크: {chunk:.0f}초 단위')
    print('-' * 45)

    offset = 0.0
    while offset < total:
        duration = min(chunk, total - offset)
        t_start = time_str(offset)
        t_end = time_str(offset + duration)

        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(
                source, offset=offset, duration=duration
            )

        try:
            text = recognizer.recognize_google(audio, language=language)
            print(f'  [{t_start}~{t_end}] {text}')
            results.append((t_start, text))

        except sr.UnknownValueError:
            print(f'  [{t_start}~{t_end}] (인식 불가)')
            results.append((t_start, '(인식 불가)'))

        except sr.RequestError as err:
            print(f'  [{t_start}~{t_end}] API 오류: {err}')
            results.append((t_start, f'API 오류: {err}'))

        offset += duration

    return results


def save_csv(wav_path, data):
    """STT 결과를 WAV와 같은 이름의 CSV 파일로 저장한다."""
    make_dir(TRANSCRIPTS_DIR)
    csv_path = wav_to_csv_path(wav_path)

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['시간', '인식된 텍스트'])
        writer.writerows(data)

    print(f'\nCSV 저장: {csv_path} ({len(data)}개 항목)')
    return csv_path


def convert_one():
    """선택한 WAV 파일 1개를 STT 변환하여 CSV로 저장한다."""
    wav_path = select_file()
    if wav_path:
        save_csv(wav_path, transcribe_audio(wav_path))


# ─────────────────────────────────────────────────────────────────
# 보너스: 키워드 검색
# ─────────────────────────────────────────────────────────────────

def search_keyword(keyword):
    """transcripts 폴더의 모든 CSV에서 키워드를 검색하여 출력한다."""
    if not os.path.exists(TRANSCRIPTS_DIR):
        print('변환된 파일이 없습니다. 먼저 STT 변환을 실행해주세요.')
        return

    csv_files = sorted([
        f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.csv')
    ])

    if not csv_files:
        print('CSV 파일이 없습니다.')
        return

    total = 0
    print(f'\n[검색] "{keyword}"')
    print('=' * 45)

    for csv_file in csv_files:
        matches = []
        with open(os.path.join(TRANSCRIPTS_DIR, csv_file),
                  'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 헤더 건너뜀
            for row in reader:
                if len(row) >= 2 and keyword in row[1]:
                    matches.append(row)

        if matches:
            print(f'\n파일: {csv_file}')
            print('-' * 45)
            for row in matches:
                highlighted = row[1].replace(keyword, f'[{keyword}]')
                print(f'  [{row[0]}] {highlighted}')
            total += len(matches)

    print('\n' + '=' * 45)
    if total == 0:
        print(f'"{keyword}" 검색 결과 없음.')
    else:
        print(f'총 {total}개 항목 발견.')


# ─────────────────────────────────────────────────────────────────
# STT 결과 보기
# ─────────────────────────────────────────────────────────────────

def show_transcript():
    """WAV 파일을 선택하여 해당 CSV 변환 결과를 출력한다."""
    files = list_records()
    if not files:
        print('녹음 파일이 없습니다.')
        return

    print('\n녹음 파일 목록:')
    for i, name in enumerate(files, 1):
        csv_path = wav_to_csv_path(os.path.join(RECORDS_DIR, name))
        status = '[변환됨]' if os.path.exists(csv_path) else '[미변환]'
        print(f'  {i}. {name} {status}')

    choice = input('파일 번호 선택: ').strip()
    if not (choice.isdigit() and 1 <= int(choice) <= len(files)):
        print('올바른 번호를 입력해주세요.')
        return

    csv_path = wav_to_csv_path(
        os.path.join(RECORDS_DIR, files[int(choice) - 1])
    )

    if not os.path.exists(csv_path):
        print('아직 변환되지 않은 파일입니다. 메뉴 4번 또는 5번을 먼저 실행해주세요.')
        return

    print(f'\n[STT 결과] {os.path.basename(csv_path)}')
    print('-' * 45)
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 헤더 건너뜀
        for row in reader:
            if len(row) >= 2:
                print(f'  [{row[0]}] {row[1]}')


# ─────────────────────────────────────────────────────────────────
# 메뉴 & 실행
# ─────────────────────────────────────────────────────────────────

def show_menu():
    """메뉴를 출력하고 사용자 입력을 반환한다."""
    try:
        import speech_recognition  # noqa: F401
        stt_status = 'OK'
    except ImportError:
        stt_status = '미설치 → pip install SpeechRecognition'

    print('\n=== 자비스 음성 녹음 & STT 앱 ===')
    print(f'[STT: {stt_status}]')
    print('1. 녹음 시작')
    print('2. 녹음 파일 듣기')
    print('3. 날짜별 녹음 파일 조회')
    print('4. 선택 파일 STT 변환 (→ CSV)')
    print('5. STT 결과 보기')
    print('6. 키워드 검색')
    print('0. 종료')
    return input('선택: ').strip()


def run():
    """앱 메인 루프를 실행한다."""
    make_dir(RECORDS_DIR)
    make_dir(TRANSCRIPTS_DIR)

    actions = {
        '1': lambda: record_audio(
            os.path.join(
                RECORDS_DIR,
                datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.wav'
            )
        ),
        '2': lambda: play_audio(select_file() or ''),
        '3': lambda: list_records_by_date(
            input('시작 날짜 (예: 20260101): ').strip(),
            input('종료 날짜 (예: 20260131): ').strip()
        ),
        '4': convert_one,
        '5': show_transcript,
        '6': lambda: search_keyword(input('검색 키워드: ').strip()),
    }

    while True:
        choice = show_menu()
        if choice == '0':
            print('앱을 종료합니다.')
            break
        elif choice in actions:
            actions[choice]()
        else:
            print('올바른 번호를 입력해주세요.')


if __name__ == '__main__':
    run()
