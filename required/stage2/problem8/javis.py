"""
javis.py - 음성 녹음 및 STT(Speech to Text) 기능 구현

문제 7: 음성 녹음 (녹음 / 재생 / 날짜별 조회)
문제 8: 음성에서 문자로 (STT + CSV 저장 + 키워드 검색)
"""

import os
import csv
import datetime


# ─────────────────────────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────────────────────────

def create_records_folder():
    """records 폴더가 없으면 생성한다."""
    if not os.path.exists('records'):
        os.makedirs('records')


def create_transcripts_folder():
    """transcripts 폴더가 없으면 생성한다."""
    if not os.path.exists('transcripts'):
        os.makedirs('transcripts')


def get_file_name():
    """현재 날짜와 시간을 기반으로 WAV 파일 이름을 생성한다."""
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d-%H%M%S') + '.wav'


def check_stt_library():
    """
    SpeechRecognition 라이브러리 설치 여부를 확인한다.

    Returns:
        bool: 설치되어 있으면 True, 아니면 False
    """
    try:
        import speech_recognition  # noqa: F401
        return True
    except ImportError:
        return False


def print_stt_install_guide():
    """STT 라이브러리 설치 안내를 출력한다."""
    print()
    print('  ※ SpeechRecognition 라이브러리가 설치되지 않았습니다.')
    print('  아래 명령어로 설치한 뒤 다시 실행해주세요.')
    print()
    print('    pip install SpeechRecognition')
    print()
    print('  설치 후 인터넷 연결 상태에서 STT 기능을 사용할 수 있습니다.')


# ─────────────────────────────────────────────────────────────────
# 문제 7: 음성 녹음
# ─────────────────────────────────────────────────────────────────

def record_audio(file_path):
    """
    마이크를 인식하고 음성을 녹음하여 WAV 파일로 저장한다.

    sounddevice 기본 dtype(float32)을 PCM int16으로 변환하여
    SpeechRecognition 등 표준 WAV 도구와 호환되도록 저장한다.
    """
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print('필요한 라이브러리가 없습니다. 아래 명령어로 설치해주세요:')
        print('  pip install sounddevice numpy')
        return False

    import wave
    import struct

    sample_rate = 44100
    print('녹음을 시작합니다. Enter를 누르면 녹음이 종료됩니다...')

    frames = []
    recording = [True]

    def callback(indata, frame_count, time_info, status):
        if recording[0]:
            frames.append(indata.copy())

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype='float32',
        callback=callback
    ):
        input()
        recording[0] = False

    if not frames:
        print('녹음된 데이터가 없습니다.')
        return False

    audio_float = np.concatenate(frames, axis=0).flatten()

    # float32(-1.0 ~ 1.0) → int16(-32768 ~ 32767) 변환
    audio_int16 = (
        np.clip(audio_float, -1.0, 1.0) * 32767
    ).astype(np.int16)

    # 표준 PCM WAV(format 1)로 저장 — wave 표준 모듈 사용
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)           # int16 = 2바이트
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    print(f'녹음 완료: {file_path}')
    return True


def play_audio(file_path):
    """
    녹음 파일을 재생한다.

    Mac에서는 기본 내장 명령어 afplay를 우선 사용하고,
    그 외 환경에서는 sounddevice로 재생한다.
    """
    import subprocess
    import sys

    if not os.path.exists(file_path):
        print(f'파일을 찾을 수 없습니다: {file_path}')
        return

    print(f'재생 중: {os.path.basename(file_path)}')

    # Mac 환경: afplay 사용 (별도 설치 불필요)
    if sys.platform == 'darwin':
        result = subprocess.run(
            ['afplay', file_path],
            capture_output=True
        )
        if result.returncode == 0:
            print('재생 완료.')
            return
        print('afplay 실패, sounddevice로 재시도합니다.')

    # 그 외 환경: sounddevice 사용
    try:
        import sounddevice as sd
        import numpy as np
        import wave
    except ImportError:
        print('sounddevice 라이브러리가 없습니다:')
        print('  pip install sounddevice numpy')
        return

    with wave.open(file_path, 'rb') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
    dtype = dtype_map.get(sampwidth, np.int16)
    audio = np.frombuffer(raw, dtype=dtype)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)
    audio = audio.astype(np.float32) / np.iinfo(dtype).max

    sd.play(audio, samplerate=sample_rate)
    sd.wait()
    print('재생 완료.')


def list_records():
    """records 폴더의 모든 WAV 파일 목록을 반환한다."""
    if not os.path.exists('records'):
        return []
    files = sorted([
        f for f in os.listdir('records') if f.endswith('.wav')
    ])
    return files


def list_records_by_date(start_date, end_date):
    """특정 날짜 범위에 해당하는 녹음 파일 목록을 출력한다."""
    if not os.path.exists('records'):
        print('records 폴더가 없습니다.')
        return

    try:
        start = datetime.datetime.strptime(start_date, '%Y%m%d')
        end = datetime.datetime.strptime(end_date, '%Y%m%d')
    except ValueError:
        print('날짜 형식이 올바르지 않습니다. 예: 20260101')
        return

    found = []
    for file_name in sorted(os.listdir('records')):
        if not file_name.endswith('.wav'):
            continue
        date_part = file_name.split('-')[0]
        try:
            file_date = datetime.datetime.strptime(date_part, '%Y%m%d')
            if start <= file_date <= end:
                found.append(file_name)
        except ValueError:
            continue

    if found:
        print(f'\n{start_date} ~ {end_date} 범위의 녹음 파일:')
        for file_name in found:
            print(f'  {file_name}')
    else:
        print('해당 날짜 범위의 녹음 파일이 없습니다.')


def select_file():
    """파일 목록을 출력하고 사용자가 선택한 파일 경로를 반환한다."""
    files = list_records()
    if not files:
        print('녹음 파일이 없습니다.')
        return None

    print('\n녹음 파일 목록:')
    for i, file_name in enumerate(files, 1):
        print(f'  {i}. {file_name}')

    user_input = input('파일 번호 선택: ').strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(files):
        return os.path.join('records', files[int(user_input) - 1])

    print('올바른 번호를 입력해주세요.')
    return None


# ─────────────────────────────────────────────────────────────────
# 문제 8: STT - 음성 파일 → 텍스트 추출
# ─────────────────────────────────────────────────────────────────

def get_wav_format_tag(file_path):
    """
    WAV 파일의 format tag를 반환한다.

    표준 라이브러리만 사용하여 WAV 헤더를 직접 읽는다.

    Args:
        file_path (str): WAV 파일 경로

    Returns:
        int: format tag (1=PCM, 3=IEEE float) 또는 읽기 실패 시 -1
    """
    import struct
    try:
        with open(file_path, 'rb') as f:
            f.seek(20)              # fmt 청크 내 AudioFormat 오프셋
            tag = struct.unpack('<H', f.read(2))[0]
        return tag
    except (OSError, struct.error):
        return -1


def convert_to_pcm16(src_path):
    """
    float32 WAV 파일을 PCM int16 WAV로 변환하여 원본 파일을 덮어쓴다.

    SpeechRecognition은 PCM int16(format tag 1)만 지원하므로
    float32(format tag 3)로 저장된 파일을 변환한다.
    numpy 없이 표준 라이브러리 struct 모듈로 처리한다.

    Args:
        src_path (str): 변환할 WAV 파일 경로

    Returns:
        bool: 변환 성공 시 True, 실패 시 False
    """
    import struct
    import wave

    try:
        # 원본 헤더 정보 읽기
        with open(src_path, 'rb') as f:
            riff_id = f.read(4)           # 'RIFF'
            f.read(4)                      # chunk size
            wave_id = f.read(4)           # 'WAVE'
            fmt_id = f.read(4)            # 'fmt '
            fmt_size = struct.unpack('<I', f.read(4))[0]
            fmt_tag = struct.unpack('<H', f.read(2))[0]
            channels = struct.unpack('<H', f.read(2))[0]
            sample_rate = struct.unpack('<I', f.read(4))[0]
            f.read(4)                      # byte rate
            f.read(2)                      # block align
            bits = struct.unpack('<H', f.read(2))[0]

            # fmt_size가 16보다 크면 확장 바이트 건너뜀
            extra = fmt_size - 16
            if extra > 0:
                f.read(extra)

            # data 청크 찾기
            while True:
                chunk_id = f.read(4)
                if not chunk_id:
                    return False
                chunk_size = struct.unpack('<I', f.read(4))[0]
                if chunk_id == b'data':
                    raw = f.read(chunk_size)
                    break
                f.read(chunk_size)

        if fmt_tag != 3:
            return True     # 이미 PCM — 변환 불필요

        # float32 바이트 → int16 변환 (numpy 없이 struct 사용)
        float_count = len(raw) // 4
        floats = struct.unpack(f'<{float_count}f', raw)

        def clamp(v):
            return max(-1.0, min(1.0, v))

        int16_vals = [int(clamp(v) * 32767) for v in floats]
        int16_raw = struct.pack(f'<{float_count}h', *int16_vals)

        # PCM WAV로 덮어쓰기
        with wave.open(src_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int16_raw)

        return True

    except (OSError, struct.error, wave.Error) as err:
        print(f'  [변환 오류] {err}')
        return False


def transcribe_audio(file_path, language='ko-KR'):
    """
    WAV 파일에서 STT를 수행하여 (시간, 텍스트) 결과 목록을 반환한다.

    SpeechRecognition 라이브러리와 Google Web Speech API를 사용한다.
    float32 포맷 파일은 자동으로 PCM int16으로 변환 후 처리한다.
    파일을 30초 단위 청크로 분할하여 긴 파일도 지원한다.

    Args:
        file_path (str): 변환할 WAV 파일 경로
        language (str): 인식 언어 코드 (기본값: 'ko-KR')

    Returns:
        list[tuple]: [(시간문자열, 인식텍스트), ...] 또는 오류 시 빈 리스트
    """
    if not check_stt_library():
        print_stt_install_guide()
        return []

    import speech_recognition as sr

    if not os.path.exists(file_path):
        print(f'파일을 찾을 수 없습니다: {file_path}')
        return []

    # float32 WAV는 SR이 읽지 못하므로 PCM int16으로 자동 변환
    fmt_tag = get_wav_format_tag(file_path)
    if fmt_tag == 3:
        print('  [포맷 변환] float32 → PCM int16 자동 변환 중...')
        if not convert_to_pcm16(file_path):
            print('  [오류] 포맷 변환 실패. 파일을 확인해주세요.')
            return []
        print('  [포맷 변환] 완료')

    recognizer = sr.Recognizer()
    results = []

    print(f'\nSTT 변환 중: {os.path.basename(file_path)}')
    print('-' * 45)

    # 전체 오디오 길이 먼저 파악
    try:
        with sr.AudioFile(file_path) as source:
            total_duration = source.DURATION
    except ValueError as err:
        print(f'  [오류] 오디오 파일을 열 수 없습니다: {err}')
        return []

    if total_duration is None or total_duration <= 0:
        print('오디오 길이를 읽을 수 없습니다.')
        return []

    # 파일 길이에 따라 청크 크기를 자동 조정한다
    # 60초 이상: 30초 단위 / 10초 이상: 10초 단위 / 그 미만: 5초 단위
    if total_duration >= 60:
        chunk_duration = 30.0
    elif total_duration >= 10:
        chunk_duration = 10.0
    else:
        chunk_duration = 5.0

    print(f'  파일 길이: {total_duration:.1f}초 / 청크: {chunk_duration:.0f}초 단위')

    offset = 0.0
    while offset < total_duration:
        current_chunk = min(chunk_duration, total_duration - offset)
        end_offset = offset + current_chunk

        # 시간 표시: 시작~끝 구간 (예: 00:00~00:10)
        def fmt_time(sec):
            return '{:02d}:{:02d}'.format(int(sec) // 60, int(sec) % 60)

        time_str = fmt_time(offset)
        time_range = f'{fmt_time(offset)}~{fmt_time(end_offset)}'

        # 매 청크마다 파일을 새로 열어 원하는 구간을 읽는다
        with sr.AudioFile(file_path) as source:
            audio_chunk = recognizer.record(
                source,
                offset=offset,
                duration=current_chunk
            )

        try:
            text = recognizer.recognize_google(
                audio_chunk,
                language=language
            )
            print(f'  [{time_range}] {text}')
            results.append((time_str, text))

        except sr.UnknownValueError:
            # 무음 구간도 시간 정보와 함께 CSV에 기록한다
            print(f'  [{time_range}] (인식 불가 - 무음 또는 잡음)')
            results.append((time_str, '(인식 불가)'))

        except sr.RequestError as err:
            msg = f'API 요청 오류: {err}'
            print(f'  [{time_range}] {msg}')
            print('  ※ 인터넷 연결을 확인해주세요.')
            results.append((time_str, msg))

        offset += current_chunk

    return results


def save_transcript_csv(wav_path, transcript_data):
    """
    STT 결과를 CSV 파일로 저장한다.

    파일 이름은 WAV 파일과 동일하게 하되 확장자는 .csv로 저장하며
    transcripts 폴더에 위치한다. 인식 불가 구간도 포함하여 저장한다.

    Args:
        wav_path (str): 원본 WAV 파일 경로
        transcript_data (list[tuple]): [(시간, 텍스트), ...] 목록

    Returns:
        str: 저장된 CSV 파일 경로
    """
    create_transcripts_folder()

    base_name = os.path.splitext(os.path.basename(wav_path))[0]
    csv_path = os.path.join('transcripts', base_name + '.csv')

    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['시간', '인식된 텍스트'])
        writer.writerows(transcript_data)

    print(f'\nCSV 저장 완료: {csv_path}')
    print(f'  저장된 항목 수: {len(transcript_data)}개')
    return csv_path


def convert_selected_record():
    """사용자가 선택한 WAV 파일 하나를 STT 변환하여 CSV로 저장한다."""
    if not check_stt_library():
        print_stt_install_guide()
        return

    wav_path = select_file()
    if not wav_path:
        return

    transcript_data = transcribe_audio(wav_path)
    save_transcript_csv(wav_path, transcript_data)


def convert_all_records():
    """
    records 폴더의 모든 WAV 파일을 STT 변환하여 CSV로 저장한다.

    이미 변환된 파일(동일 이름 CSV 존재)은 건너뛴다.
    """
    if not check_stt_library():
        print_stt_install_guide()
        return

    files = list_records()
    if not files:
        print('변환할 녹음 파일이 없습니다.')
        return

    create_transcripts_folder()
    converted = 0

    for file_name in files:
        base_name = os.path.splitext(file_name)[0]
        csv_path = os.path.join('transcripts', base_name + '.csv')

        wav_path = os.path.join('records', file_name)
        transcript_data = transcribe_audio(wav_path)
        save_transcript_csv(wav_path, transcript_data)
        converted += 1

    print(f'\n전체 변환 완료: {converted}개 파일 처리됨')


# ─────────────────────────────────────────────────────────────────
# 문제 8 보너스: 키워드 검색
# ─────────────────────────────────────────────────────────────────

def search_keyword(keyword):
    """
    transcripts 폴더의 모든 CSV 파일에서 키워드를 검색하여 출력한다.

    검색 결과에서 키워드는 [ ] 로 강조 표시된다.

    Args:
        keyword (str): 검색할 키워드
    """
    if not os.path.exists('transcripts'):
        print('transcripts 폴더가 없습니다. 먼저 STT 변환을 진행해주세요.')
        return

    csv_files = sorted([
        f for f in os.listdir('transcripts') if f.endswith('.csv')
    ])

    if not csv_files:
        print('저장된 CSV 파일이 없습니다. 먼저 STT 변환을 진행해주세요.')
        return

    total_matches = 0
    print(f'\n[키워드 검색] "{keyword}"')
    print('=' * 50)

    for csv_file in csv_files:
        csv_path = os.path.join('transcripts', csv_file)
        file_matches = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # 헤더 행 건너뜀
            for row in reader:
                if len(row) < 2:
                    continue
                time_str, text = row[0], row[1]
                if keyword in text:
                    file_matches.append((time_str, text))

        if file_matches:
            print(f'\n파일: {csv_file}')
            print('-' * 50)
            for time_str, text in file_matches:
                highlighted = text.replace(keyword, f'[{keyword}]')
                print(f'  [{time_str}] {highlighted}')
            total_matches += len(file_matches)

    print('\n' + '=' * 50)
    if total_matches == 0:
        print(f'"{keyword}"을(를) 찾을 수 없습니다.')
    else:
        print(f'총 {total_matches}개 항목에서 "{keyword}" 발견.')


# ─────────────────────────────────────────────────────────────────
# STT 결과 보기
# ─────────────────────────────────────────────────────────────────

def show_transcript(csv_path):
    """지정한 CSV 파일의 전체 STT 결과를 출력한다."""
    if not os.path.exists(csv_path):
        print(f'\n[안내] 아직 변환되지 않은 파일입니다: {csv_path}')
        print('  메뉴 4번(선택 변환) 또는 5번(전체 변환)을 먼저 실행해주세요.')
        return

    print(f'\n[STT 결과] {os.path.basename(csv_path)}')
    print('-' * 50)

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # 헤더 건너뜀
        rows = list(reader)

    if not rows:
        print('  (저장된 내용이 없습니다.)')
        return

    for row in rows:
        if len(row) >= 2:
            print(f'  [{row[0]}] {row[1]}')


def select_and_show_transcript():
    """WAV 파일을 선택하여 해당 CSV 변환 결과를 출력한다."""
    files = list_records()
    if not files:
        print('녹음 파일이 없습니다.')
        return

    print('\n녹음 파일 목록:')
    for i, file_name in enumerate(files, 1):
        base_name = os.path.splitext(file_name)[0]
        csv_path = os.path.join('transcripts', base_name + '.csv')
        status = '[변환됨]' if os.path.exists(csv_path) else '[미변환]'
        print(f'  {i}. {file_name} {status}')

    user_input = input('파일 번호 선택: ').strip()
    if not (user_input.isdigit() and 1 <= int(user_input) <= len(files)):
        print('올바른 번호를 입력해주세요.')
        return

    selected = files[int(user_input) - 1]
    base_name = os.path.splitext(selected)[0]
    csv_path = os.path.join('transcripts', base_name + '.csv')
    show_transcript(csv_path)


# ─────────────────────────────────────────────────────────────────
# 메뉴
# ─────────────────────────────────────────────────────────────────

def show_menu():
    """메뉴를 출력하고 사용자 입력을 반환한다."""
    if check_stt_library():
        stt_status = 'OK'
    else:
        stt_status = '미설치 - pip install SpeechRecognition'
    print('\n=== 자비스 음성 녹음 & STT 앱 ===')
    print(f'[STT 라이브러리: {stt_status}]')
    print('--- 문제 7: 녹음 ---')
    print('1. 녹음 시작')
    print('2. 녹음 파일 듣기')
    print('3. 날짜별 녹음 파일 조회')
    print('--- 문제 8: STT ---')
    print('4. 선택 파일 STT 변환 (→ CSV 저장)')
    print('5. 전체 파일 STT 변환 (→ CSV 저장)')
    print('6. STT 결과 보기')
    print('--- 보너스: 키워드 검색 ---')
    print('7. 키워드 검색')
    print('-' * 34)
    print('0. 종료')
    return input('선택: ').strip()


def run():
    """앱 메인 루프를 실행한다."""
    create_records_folder()
    create_transcripts_folder()

    while True:
        choice = show_menu()

        if choice == '1':
            file_name = get_file_name()
            file_path = os.path.join('records', file_name)
            record_audio(file_path)

        elif choice == '2':
            file_path = select_file()
            if file_path:
                play_audio(file_path)

        elif choice == '3':
            start_date = input('시작 날짜 입력 (예: 20260101): ').strip()
            end_date = input('종료 날짜 입력 (예: 20260131): ').strip()
            list_records_by_date(start_date, end_date)

        elif choice == '4':
            convert_selected_record()

        elif choice == '5':
            convert_all_records()

        elif choice == '6':
            select_and_show_transcript()

        elif choice == '7':
            keyword = input('검색할 키워드 입력: ').strip()
            if keyword:
                search_keyword(keyword)
            else:
                print('키워드를 입력해주세요.')

        elif choice == '0':
            print('앱을 종료합니다.')
            break

        else:
            print('올바른 번호를 입력해주세요.')


if __name__ == '__main__':
    run()