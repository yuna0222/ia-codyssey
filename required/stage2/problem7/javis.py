import os
import datetime


def create_records_folder():
    """records 폴더가 없으면 생성"""
    if not os.path.exists('records'):
        os.makedirs('records')


def get_file_name():
    """현재 날짜와 시간을 기반으로 파일 이름을 생성"""
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d-%H%M%S') + '.wav'


def record_audio(file_path):
    """마이크를 인식하고 음성을 녹음하여 파일로 저장"""
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wav
    except ImportError:
        print('필요한 라이브러리가 없습니다. 아래 명령어로 설치해주세요:')
        print('  pip install sounddevice scipy numpy')
        return False

    sample_rate = 44100
    print('녹음을 시작합니다. Enter를 누르면 녹음이 종료됩니다...')

    frames = []
    recording = [True]

    def callback(indata, frame_count, time_info, status):
        if recording[0]:
            frames.append(indata.copy())

    with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
        input()
        recording[0] = False

    if frames:
        import numpy as np
        audio_data = np.concatenate(frames, axis=0)
        wav.write(file_path, sample_rate, audio_data)
        print(f'녹음 완료: {file_path}')
        return True
    else:
        print('녹음된 데이터가 없습니다.')
        return False


def play_audio(file_path):
    """녹음 파일을 재생한다."""
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wav
    except ImportError:
        print('필요한 라이브러리가 없습니다. 아래 명령어로 설치해주세요:')
        print('  pip install sounddevice scipy')
        return

    if not os.path.exists(file_path):
        print(f'파일을 찾을 수 없습니다: {file_path}')
        return

    sample_rate, data = wav.read(file_path)
    print(f'재생 중: {file_path}')
    sd.play(data, sample_rate)
    sd.wait()
    print('재생 완료.')


def list_records():
    """records 폴더의 모든 녹음 파일 목록을 반환한다."""
    if not os.path.exists('records'):
        return []
    files = sorted([f for f in os.listdir('records') if f.endswith('.wav')])
    return files


def list_records_by_date(start_date, end_date):
    """특정 범위의 날짜에 해당하는 녹음 파일 목록을 출력한다."""
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
        print(f'{start_date} ~ {end_date} 범위의 녹음 파일:')
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
    else:
        print('올바른 번호를 입력해주세요.')
        return None


def show_menu():
    """메뉴를 출력한다."""
    print('\n=== 자비스 음성 녹음 앱 ===')
    print('1. 녹음 시작')
    print('2. 녹음 파일 듣기')
    print('3. 날짜별 녹음 파일 조회')
    print('4. 종료')
    return input('선택: ').strip()


def run():
    """앱을 실행한다."""
    create_records_folder()

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
            print('앱을 종료합니다.')
            break

        else:
            print('올바른 번호를 입력해주세요.')


if __name__ == '__main__':
    run()
