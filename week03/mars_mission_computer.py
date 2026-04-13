import time
import datetime
import platform
import threading
import multiprocessing
import sys
import psutil

from dummy_sensor import DummySensor
from dummy_sensor import ENV_KEYS

# ──────────────────────────────────────────────
# 설정 파일 관련 상수
# ──────────────────────────────────────────────
SETTING_FILE = 'setting.txt'
OUTPUT_FILE = 'computer_info.txt'

# 시스템 정보 항목 전체 목록 (setting.txt 기본값으로도 사용)
ALL_INFO_KEYS = [
    'os',
    'os_version',
    'cpu_type',
    'cpu_cores',
    'memory_total',
]

# 부하 정보 항목 전체 목록
ALL_LOAD_KEYS = [
    'cpu_usage_percent',
    'memory_usage_percent',
]

# 반복 출력 주기 (초)
REPEAT_INTERVAL = 20


# ──────────────────────────────────────────────
# 공용 유틸리티 함수
# ──────────────────────────────────────────────

def dict_to_json(data):
    """
    딕셔너리를 JSON 형식의 문자열로 변환합니다.
    외부 라이브러리(json 모듈) 없이 직접 포매팅합니다.

    Args:
        data (dict): 변환할 딕셔너리

    Returns:
        str: JSON 형식의 문자열
    """
    lines = ['{']
    keys = list(data.keys())

    for i, key in enumerate(keys):
        value = data[key]
        # 문자열이면 따옴표로 감싸고, 숫자 등은 그대로 표현
        formatted = f'"{value}"' if isinstance(value, str) else str(value)
        comma = ',' if i < len(keys) - 1 else ''
        lines.append(f'    "{key}": {formatted}{comma}')

    lines.append('}')
    return '\n'.join(lines)


def filter_by_keys(data, allowed_keys):
    """
    딕셔너리에서 허용된 키만 추려서 새 딕셔너리를 반환합니다.
    setting.txt 설정에 따라 출력 항목을 제한할 때 재활용됩니다.

    Args:
        data (dict): 원본 딕셔너리
        allowed_keys (list): 출력을 허용할 키 목록

    Returns:
        dict: allowed_keys에 해당하는 항목만 담긴 딕셔너리
    """
    return {k: v for k, v in data.items() if k in allowed_keys}


def print_section(title, json_str):
    """
    제목과 JSON 문자열을 보기 좋은 구분선 형식으로 출력합니다.
    여러 메서드에서 공통으로 재활용하는 출력 함수입니다.

    Args:
        title (str): 출력할 섹션 제목
        json_str (str): 출력할 JSON 형식 문자열
    """
    print('\n' + '*' * 55)
    print(f'  [{title}]')
    print('*' * 55)
    print(json_str)
    print('*' * 55)


def load_setting(filepath=SETTING_FILE):
    """
    setting.txt 파일에서 출력할 항목 목록을 읽어옵니다.
    파일이 없으면 기본값(전체 항목)으로 setting.txt를 새로 생성합니다.
    각 줄에 키 이름을 하나씩 적어두는 형식입니다.

    Args:
        filepath (str): 설정 파일 경로 (기본값: 'setting.txt')

    Returns:
        dict: {'info': [...], 'load': [...]} 형태의 허용 키 목록
    """
    default_setting = ALL_INFO_KEYS + ALL_LOAD_KEYS

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            raise ValueError('설정 파일이 비어 있습니다.')
    except FileNotFoundError:
        # 파일이 없으면 기본값으로 새로 생성
        print(f'[info] {filepath} 파일이 없어 기본값으로 새로 생성합니다.')
        save_setting(default_setting, filepath)
        lines = default_setting

    # info 키와 load 키를 분리해서 반환
    info_keys = [k for k in lines if k in ALL_INFO_KEYS]
    load_keys = [k for k in lines if k in ALL_LOAD_KEYS]

    # 빈 경우 전체 항목으로 폴백
    return {
        'info': info_keys if info_keys else ALL_INFO_KEYS,
        'load': load_keys if load_keys else ALL_LOAD_KEYS,
    }


def save_setting(keys, filepath=SETTING_FILE):
    """
    키 목록을 setting.txt 파일에 저장합니다.
    한 줄에 하나의 키 이름이 기록됩니다.

    Args:
        keys (list): 저장할 키 이름 목록
        filepath (str): 저장할 파일 경로
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for key in keys:
            f.write(key + '\n')


def save_to_file(content, filepath=OUTPUT_FILE):
    """
    문자열 내용을 지정한 파일에 저장합니다.
    get_mission_computer_info() 결과를 computer_info.txt로 추출할 때 사용합니다.

    Args:
        content (str): 저장할 문자열
        filepath (str): 저장할 파일 경로
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[info] 결과가 {filepath} 에 저장되었습니다.')


def wait_interruptible(seconds, stop_flag):
    """
    지정한 초(seconds) 동안 대기하되, stop_flag 가 세팅되면 즉시 반환합니다.
    time.sleep(seconds) 대신 사용해서 중단 신호에 빠르게 반응할 수 있게 합니다.

    Args:
        seconds (int|float): 대기할 최대 시간(초)
        stop_flag: 중단 신호 이벤트 (threading.Event 또는 multiprocessing.Event)
    """
    # 0.5초 간격으로 쪼개서 체크 → 중단 신호를 최대 0.5초 내에 감지
    interval = 0.5
    elapsed = 0.0
    while elapsed < seconds:
        if stop_flag.is_set():
            return
        time.sleep(interval)
        elapsed += interval


# ──────────────────────────────────────────────
# MissionComputer 클래스
# ──────────────────────────────────────────────

class MissionComputer:
    """
    화성 기지 미션 컴퓨터를 나타내는 클래스.
    센서 데이터 수집, 시스템 정보 조회, 부하 모니터링 기능을 담당합니다.
    멀티 쓰레드 / 멀티 프로세스 환경에서 stop_flag 로 종료를 제어합니다.
    """

    def __init__(self, sensor, stop_flag=None):
        """
        MissionComputer 초기화.

        Args:
            sensor: 환경 센서 객체 (DummySensor 등)
            stop_flag: 종료 신호 이벤트 (threading.Event 또는
                       multiprocessing.Event). None 이면 내부에서 생성합니다.
        """
        self.sensor = sensor
        self.env_values = {key: 0.0 for key in ENV_KEYS}
        self.history = {key: [] for key in ENV_KEYS}

        # setting.txt 에서 출력 항목 설정 로드
        self.setting = load_setting()

        # 외부에서 stop_flag 를 주입받지 않으면 내부 threading.Event 로 생성
        # 멀티 프로세스 모드에서는 multiprocessing.Event 를 주입받아 사용합니다.
        self.stop_flag = stop_flag if stop_flag is not None else threading.Event()

    def print_average(self):
        """
        지금까지 수집된 센서 데이터의 평균값을 계산해 출력합니다.
        출력 후 히스토리를 초기화해 다음 주기를 준비합니다.
        """
        avg = {
            key: round(sum(vals) / len(vals), 4)
            for key, vals in self.history.items() if vals
        }

        print_section('5분 평균값', dict_to_json(avg))

        # 히스토리 초기화
        self.history = {key: [] for key in ENV_KEYS}

    def get_sensor_data(self):
        """
        센서에서 환경 데이터를 5초 간격으로 반복 수집해 출력합니다.
        60회(5분)마다 평균값을 출력합니다.
        stop_flag 가 세팅되면 루프를 종료합니다.
        """
        print('[sensor] 센서 데이터 수집 시작')

        count = 0

        while not self.stop_flag.is_set():
            self.sensor.set_env()
            sensor_data = self.sensor.get_env()

            for key in ENV_KEYS:
                self.env_values[key] = sensor_data[key]

            for key in ENV_KEYS:
                self.history[key].append(self.env_values[key])

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'\n  [{timestamp}] [센서] MissionComputer JSON 출력:')
            print(dict_to_json(self.env_values))

            count += 1

            if count >= 60:
                self.print_average()
                count = 0

            # 5초 대기하되 stop_flag 감지 시 즉시 빠져나옴
            wait_interruptible(5, self.stop_flag)

        print('[sensor] 센서 데이터 수집이 종료되었습니다.')

    def get_mission_computer_info(self):
        """
        미션 컴퓨터의 시스템 정보를 20초마다 반복 조회해 출력합니다.
        setting.txt 에 설정된 항목만 출력하고 computer_info.txt 에도 저장합니다.
        stop_flag 가 세팅되면 루프를 종료합니다.

        조회 항목:
            - os              : 운영체제 이름
            - os_version      : 운영체제 버전
            - cpu_type        : CPU 아키텍처/종류
            - cpu_cores       : CPU 코어 수
            - memory_total    : 전체 메모리 크기 (GB)

        예외 처리:
            각 항목을 개별적으로 try/except 로 감싸서,
            일부 정보를 가져오지 못해도 나머지는 정상 출력됩니다.
        """
        print('[info] 시스템 정보 모니터링 시작')

        while not self.stop_flag.is_set():
            raw_info = {}

            # 운영체제 이름
            try:
                raw_info['os'] = platform.system()
            except Exception as e:
                raw_info['os'] = f'조회 실패: {e}'

            # 운영체제 버전
            try:
                raw_info['os_version'] = platform.version()
            except Exception as e:
                raw_info['os_version'] = f'조회 실패: {e}'

            # CPU 아키텍처/타입
            try:
                raw_info['cpu_type'] = platform.processor() or platform.machine()
            except Exception as e:
                raw_info['cpu_type'] = f'조회 실패: {e}'

            # CPU 코어 수 (논리 코어 기준)
            try:
                raw_info['cpu_cores'] = psutil.cpu_count(logical=True)
            except Exception as e:
                raw_info['cpu_cores'] = f'조회 실패: {e}'

            # 전체 메모리 크기 (바이트 → GB 변환, 소수점 2자리)
            try:
                mem_bytes = psutil.virtual_memory().total
                raw_info['memory_total'] = f'{round(mem_bytes / (1024 ** 3), 2)} GB'
            except Exception as e:
                raw_info['memory_total'] = f'조회 실패: {e}'

            # setting.txt 에서 허용된 항목만 필터링
            filtered = filter_by_keys(raw_info, self.setting['info'])
            json_str = dict_to_json(filtered)

            print_section('미션 컴퓨터 시스템 정보', json_str)

            # computer_info.txt 로 저장
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            output_content = f'[{timestamp}] 미션 컴퓨터 시스템 정보\n{json_str}\n'
            save_to_file(output_content)

            # 20초 대기하되 stop_flag 감지 시 즉시 빠져나옴
            wait_interruptible(REPEAT_INTERVAL, self.stop_flag)

        print('[info] 시스템 정보 모니터링이 종료되었습니다.')

    def get_mission_computer_load(self):
        """
        미션 컴퓨터의 CPU/메모리 실시간 사용량을 20초마다 반복 조회해 출력합니다.
        setting.txt 에 설정된 항목만 출력합니다.
        stop_flag 가 세팅되면 루프를 종료합니다.

        조회 항목:
            - cpu_usage_percent    : CPU 실시간 사용률 (%)
            - memory_usage_percent : 메모리 실시간 사용률 (%)

        예외 처리:
            각 항목을 개별적으로 try/except 로 감싸서,
            일부 조회 실패 시에도 나머지는 정상 출력됩니다.
        """
        print('[load] 부하 모니터링 시작')

        while not self.stop_flag.is_set():
            raw_load = {}

            # CPU 사용률 (interval=1 → 1초 동안 측정 후 반환)
            try:
                raw_load['cpu_usage_percent'] = psutil.cpu_percent(interval=1)
            except Exception as e:
                raw_load['cpu_usage_percent'] = f'조회 실패: {e}'

            # 메모리 사용률
            try:
                raw_load['memory_usage_percent'] = psutil.virtual_memory().percent
            except Exception as e:
                raw_load['memory_usage_percent'] = f'조회 실패: {e}'

            # setting.txt 에서 허용된 항목만 필터링
            filtered = filter_by_keys(raw_load, self.setting['load'])
            json_str = dict_to_json(filtered)

            print_section('미션 컴퓨터 실시간 부하', json_str)

            # 20초 대기하되 stop_flag 감지 시 즉시 빠져나옴
            wait_interruptible(REPEAT_INTERVAL, self.stop_flag)

        print('[load] 부하 모니터링이 종료되었습니다.')


# ──────────────────────────────────────────────
# 키 입력 감지 함수 (보너스: q 입력 시 중단)
# ──────────────────────────────────────────────

def watch_for_quit(stop_flag):
    """
    사용자가 'q' + Enter 를 입력하면 stop_flag 를 세팅해 모든 루프를 중단합니다.
    멀티 쓰레드/프로세스 모드에서 메인 흐름으로 직접 호출합니다.

    Args:
        stop_flag: 중단 신호 이벤트 (threading.Event 또는 multiprocessing.Event)
    """
    print("\n[system] 'q' + Enter 를 입력하면 모든 모니터링이 종료됩니다.\n")
    while not stop_flag.is_set():
        try:
            user_input = input()
            if user_input.strip().lower() == 'q':
                print('[system] 종료 신호 수신. 모든 작업을 중단합니다...')
                stop_flag.set()
                break
        except EOFError:
            # 파이프/리다이렉션 환경에서 input() 이 EOF 를 반환할 수 있음
            break


# ──────────────────────────────────────────────
# 멀티 쓰레드 실행 함수
# ──────────────────────────────────────────────

def run_with_threads():
    """
    하나의 MissionComputer 인스턴스(runComputer)를 생성하고
    get_mission_computer_info, get_mission_computer_load, get_sensor_data 를
    각각 별도 쓰레드로 동시에 실행합니다.

    보너스: 'q' 입력으로 모든 쓰레드를 한 번에 종료합니다.
    """
    print('=' * 55)
    print('  [멀티 쓰레드 모드 시작]')
    print('=' * 55)

    # 공유 stop_flag: 모든 쓰레드가 같은 이벤트를 바라봄
    stop_flag = threading.Event()

    ds = DummySensor()
    runComputer = MissionComputer(ds, stop_flag=stop_flag)

    # 각 메서드를 daemon=True 쓰레드로 실행
    # daemon=True → 메인 쓰레드 종료 시 자동으로 함께 종료됨
    threads = [
        threading.Thread(
            target=runComputer.get_mission_computer_info,
            name='Thread-Info',
            daemon=True
        ),
        threading.Thread(
            target=runComputer.get_mission_computer_load,
            name='Thread-Load',
            daemon=True
        ),
        threading.Thread(
            target=runComputer.get_sensor_data,
            name='Thread-Sensor',
            daemon=True
        ),
    ]

    for t in threads:
        t.start()

    # 보너스: 메인 흐름에서 'q' 입력 대기 → stop_flag 세팅
    watch_for_quit(stop_flag)

    # stop_flag 세팅 후 각 쓰레드가 정리될 때까지 최대 5초 대기
    for t in threads:
        t.join(timeout=5)

    print('\n[멀티 쓰레드 모드 종료]\n')


# ──────────────────────────────────────────────
# 멀티 프로세스용 실행 함수
# (클래스 메서드를 Process target 으로 직접 쓸 수 없어 모듈 레벨 함수로 분리)
# ──────────────────────────────────────────────

def _process_info(stop_flag):
    """
    멀티 프로세스 환경에서 runComputer1 인스턴스로
    get_mission_computer_info 를 실행합니다.

    Args:
        stop_flag (multiprocessing.Event): 프로세스 간 공유 종료 신호
    """
    ds = DummySensor()
    runComputer1 = MissionComputer(ds, stop_flag=stop_flag)
    runComputer1.get_mission_computer_info()


def _process_load(stop_flag):
    """
    멀티 프로세스 환경에서 runComputer2 인스턴스로
    get_mission_computer_load 를 실행합니다.

    Args:
        stop_flag (multiprocessing.Event): 프로세스 간 공유 종료 신호
    """
    ds = DummySensor()
    runComputer2 = MissionComputer(ds, stop_flag=stop_flag)
    runComputer2.get_mission_computer_load()


def _process_sensor(stop_flag):
    """
    멀티 프로세스 환경에서 runComputer3 인스턴스로
    get_sensor_data 를 실행합니다.

    Args:
        stop_flag (multiprocessing.Event): 프로세스 간 공유 종료 신호
    """
    ds = DummySensor()
    runComputer3 = MissionComputer(ds, stop_flag=stop_flag)
    runComputer3.get_sensor_data()


def run_with_processes():
    """
    3개의 MissionComputer 인스턴스(runComputer1/2/3)를 각각 별도 프로세스로 실행합니다.

    - runComputer1 → get_mission_computer_info (프로세스 1)
    - runComputer2 → get_mission_computer_load (프로세스 2)
    - runComputer3 → get_sensor_data           (프로세스 3)

    보너스: 'q' 입력으로 multiprocessing.Event 를 세팅해 전체 프로세스를 종료합니다.
    """
    print('=' * 55)
    print('  [멀티 프로세스 모드 시작]')
    print('=' * 55)

    # 프로세스 간 공유 stop_flag (multiprocessing.Event 사용)
    mp_stop_flag = multiprocessing.Event()

    processes = [
        multiprocessing.Process(
            target=_process_info,
            args=(mp_stop_flag,),
            name='Process-Info',
            daemon=True
        ),
        multiprocessing.Process(
            target=_process_load,
            args=(mp_stop_flag,),
            name='Process-Load',
            daemon=True
        ),
        multiprocessing.Process(
            target=_process_sensor,
            args=(mp_stop_flag,),
            name='Process-Sensor',
            daemon=True
        ),
    ]

    for p in processes:
        p.start()

    # 보너스: 메인 흐름에서 'q' 입력 대기 → mp_stop_flag 세팅
    watch_for_quit(mp_stop_flag)

    # stop_flag 세팅 후 각 프로세스가 정리될 때까지 최대 5초 대기
    for p in processes:
        p.join(timeout=5)
        if p.is_alive():
            # 5초 내 종료되지 않으면 강제 종료
            p.terminate()

    print('\n[멀티 프로세스 모드 종료]\n')


# ──────────────────────────────────────────────
# 진입점
# ──────────────────────────────────────────────

def main():
    """
    프로그램 진입점.
    명령줄 인수로 실행 모드를 선택합니다.

    사용법:
        python mars_mission_computer.py          → 멀티 쓰레드 모드 (기본)
        python mars_mission_computer.py thread   → 멀티 쓰레드 모드
        python mars_mission_computer.py process  → 멀티 프로세스 모드
    """
    mode = sys.argv[1] if len(sys.argv) > 1 else 'thread'

    if mode == 'process':
        run_with_processes()
    else:
        run_with_threads()


if __name__ == '__main__':
    # 멀티 프로세스 사용 시 Windows 환경에서 필수 (spawn 방식 보호)
    multiprocessing.freeze_support()
    main()