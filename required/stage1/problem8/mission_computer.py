import datetime
import platform
import time
import threading

import psutil

from dummy_sensor import ENV_KEYS

SETTING_FILE = 'setting.txt'
OUTPUT_FILE = 'computer_info.txt'

REPEAT_INTERVAL = 20

# 시스템 정보 전체 항목 목록
ALL_INFO_KEYS = [
    'os',
    'os_version',
    'cpu_type',
    'cpu_cores',
    'memory_total',
]

# 부하 정보 전체 항목 목록
ALL_LOAD_KEYS = [
    'cpu_usage_percent',
    'memory_usage_percent',
]


def dict_to_json(data):
    lines = ['{']
    keys = list(data.keys())

    for i, key in enumerate(keys):
        value = data[key]
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


def save_to_file(content, filepath=OUTPUT_FILE):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[info] 결과가 {filepath} 에 저장되었습니다.')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def load_setting(filepath=SETTING_FILE):
    default_keys = ALL_INFO_KEYS + ALL_LOAD_KEYS

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            raise ValueError('설정 파일이 비어 있습니다.')
    except FileNotFoundError:
        print(f'[info] {filepath} 파일이 없어 기본값으로 새로 생성합니다.')
        save_setting(default_keys, filepath)
        lines = default_keys

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


def wait_interruptible(seconds, stop_flag):
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

        self.stop_flag = stop_flag if stop_flag is not None else threading.Event()

        self.setting = load_setting()

    #  센서 데이터
    def print_average(self):
        avg = {
            key: round(sum(vals) / len(vals), 4)
            for key, vals in self.history.items()
            if vals
        }

        print('\n' + '*' * 55)
        print('  [5분 평균값]')
        print('*' * 55)
        print(dict_to_json(avg))
        print('*' * 55)

        self.history = {key: [] for key in ENV_KEYS}

    def get_sensor_data(self):
        print('[sensor] 센서 데이터 수집 시작')

        count = 0

        while not self.stop_flag.is_set():
            self.sensor.set_env()
            sensor_data = self.sensor.get_env()

            for key in ENV_KEYS:
                self.env_values[key] = sensor_data[key]
                self.history[key].append(self.env_values[key])

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'\n  [{timestamp}] MissionComputer JSON 출력:')
            print(dict_to_json(self.env_values))

            count += 1

            if count >= 60:
                self.print_average()
                count = 0

            wait_interruptible(5, self.stop_flag)

        print('[sensor] 센서 데이터 수집이 종료되었습니다.')

    # 시스템 정보
    def get_mission_computer_info(self):
        """
        미션 컴퓨터의 시스템 정보를 수집해 JSON 형식으로 출력한다.
        20초마다 반복하며 stop_flag 가 세워지면 종료한다.
        결과를 computer_info.txt 에 저장한다.
        setting.txt 가 있으면 해당 항목만 출력한다. (보너스)
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

            # setting.txt 기반 필터링
            filtered = filter_by_keys(raw_info, self.setting['info'])
            json_str = dict_to_json(filtered)

            print_section('미션 컴퓨터 시스템 정보', json_str)

            # computer_info.txt 로 저장
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            output_content = f'[{timestamp}] 미션 컴퓨터 시스템 정보\n{json_str}\n'
            save_to_file(output_content)

            wait_interruptible(REPEAT_INTERVAL, self.stop_flag)

        print('[info] 시스템 정보 모니터링이 종료되었습니다.')

    # ── 시스템 부하 ────────────────────────────────────────────
    def get_mission_computer_load(self):
        print('[load] 부하 모니터링 시작')

        while not self.stop_flag.is_set():
            raw_load = {}

            # CPU 사용률
            try:
                raw_load['cpu_usage_percent'] = psutil.cpu_percent(interval=1)
            except Exception as e:
                raw_load['cpu_usage_percent'] = f'조회 실패: {e}'

            # 메모리 사용률
            try:
                raw_load['memory_usage_percent'] = psutil.virtual_memory().percent
            except Exception as e:
                raw_load['memory_usage_percent'] = f'조회 실패: {e}'

            # setting.txt 기반 필터링
            filtered = filter_by_keys(raw_load, self.setting['load'])
            print_section('미션 컴퓨터 실시간 부하', dict_to_json(filtered))

            wait_interruptible(REPEAT_INTERVAL, self.stop_flag)

        print('[load] 부하 모니터링이 종료되었습니다.')
