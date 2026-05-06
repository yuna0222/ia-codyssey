import time
import datetime
import platform
import threading
import multiprocessing
import sys
import psutil

from dummy_sensor import DummySensor
from dummy_sensor import ENV_KEYS

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


def dict_to_json(data):
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
    return {k: v for k, v in data.items() if k in allowed_keys}


def print_section(title, json_str):
    print('\n' + '*' * 55)
    print(f'  [{title}]')
    print('*' * 55)
    print(json_str)
    print('*' * 55)


def load_setting(filepath=SETTING_FILE):
    default_setting = ALL_INFO_KEYS + ALL_LOAD_KEYS

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            raise ValueError('설정 파일이 비어 있습니다.')
    except FileNotFoundError:
        print(f'[info] {filepath} 파일이 없어 기본값으로 새로 생성합니다.')
        save_setting(default_setting, filepath)
        lines = default_setting

    info_keys = [k for k in lines if k in ALL_INFO_KEYS]
    load_keys = [k for k in lines if k in ALL_LOAD_KEYS]

    return {
        'info': info_keys if info_keys else ALL_INFO_KEYS,
        'load': load_keys if load_keys else ALL_LOAD_KEYS,
    }


def save_setting(keys, filepath=SETTING_FILE):
    with open(filepath, 'w', encoding='utf-8') as f:
        for key in keys:
            f.write(key + '\n')


def save_to_file(content, filepath=OUTPUT_FILE):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[info] 결과가 {filepath} 에 저장되었습니다.')


def wait_interruptible(seconds, stop_flag):
    # 0.5초 간격으로 쪼개서 체크 → 중단 신호를 최대 0.5초 내에 감지
    interval = 0.5
    elapsed = 0.0
    while elapsed < seconds:
        if stop_flag.is_set():
            return
        time.sleep(interval)
        elapsed += interval


class MissionComputer:
    def __init__(self, sensor, stop_flag=None):

        self.sensor = sensor
        self.env_values = {key: 0.0 for key in ENV_KEYS}
        self.history = {key: [] for key in ENV_KEYS}

        self.setting = load_setting()

        self.stop_flag = stop_flag if stop_flag is not None else threading.Event()

    def print_average(self):
        avg = {
            key: round(sum(vals) / len(vals), 4)
            for key, vals in self.history.items() if vals
        }

        print_section('5분 평균값', dict_to_json(avg))

        self.history = {key: [] for key in ENV_KEYS}

    def get_sensor_data(self):
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


# 키 입력 감지 함수 (q 입력 시 중단)
def watch_for_quit(stop_flag):
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


def run_with_threads():
    print('=' * 55)
    print('  [멀티 쓰레드 모드 시작]')
    print('=' * 55)

    stop_flag = threading.Event()

    ds = DummySensor()
    runComputer = MissionComputer(ds, stop_flag=stop_flag)

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

    watch_for_quit(stop_flag)

    for t in threads:
        t.join(timeout=5)

    print('\n[멀티 쓰레드 모드 종료]\n')


def _process_info(stop_flag):
    ds = DummySensor()
    runComputer1 = MissionComputer(ds, stop_flag=stop_flag)
    runComputer1.get_mission_computer_info()


def _process_load(stop_flag):
    ds = DummySensor()
    runComputer2 = MissionComputer(ds, stop_flag=stop_flag)
    runComputer2.get_mission_computer_load()


def _process_sensor(stop_flag):
    ds = DummySensor()
    runComputer3 = MissionComputer(ds, stop_flag=stop_flag)
    runComputer3.get_sensor_data()


def run_with_processes():
    print('=' * 55)
    print('  [멀티 프로세스 모드 시작]')
    print('=' * 55)

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

    watch_for_quit(mp_stop_flag)

    for p in processes:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()

    print('\n[멀티 프로세스 모드 종료]\n')


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'thread'

    if mode == 'process':
        run_with_processes()
    else:
        run_with_threads()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
