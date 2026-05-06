import datetime
import sys
import threading
import time

from dummy_sensor import ENV_KEYS


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


class MissionComputer:
    """화성 기지 미션 컴퓨터 — 센서 데이터 수집 및 출력 담당."""

    INTERVAL = 5  # 센서 읽기 주기 (초)
    AVG_COUNT = 60  # 평균 출력 주기 (5초 × 60 = 5분)

    def __init__(self, sensor):
        self.sensor = sensor
        self.env_values = {key: 0.0 for key in ENV_KEYS}
        self.history = {key: [] for key in ENV_KEYS}
        self._stop = False  # 종료 플래그

    def _wait_for_quit(self):
        while not self._stop:
            key = sys.stdin.readline().strip().lower()
            if key == 'q':
                self._stop = True
                break

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

        # 히스토리 초기화
        self.history = {key: [] for key in ENV_KEYS}

    def get_sensor_data(self):
        print('[info] 정지하려면 Q + Enter 를 누르세요.')

        # 키 입력 감지 스레드 시작
        quit_thread = threading.Thread(target=self._wait_for_quit, daemon=True)
        quit_thread.start()

        count = 0

        while not self._stop:
            # 센서값 읽기
            self.sensor.set_env()
            sensor_data = self.sensor.get_env()

            # env_values 갱신 및 히스토리 누적
            for key in ENV_KEYS:
                self.env_values[key] = sensor_data[key]
                self.history[key].append(self.env_values[key])

            # JSON 출력
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'\n  [{timestamp}] MissionComputer JSON 출력:')
            print(dict_to_json(self.env_values))

            count += 1

            # 60회마다 5분 평균 출력
            if count >= self.AVG_COUNT:
                self.print_average()
                count = 0

            # 5초 대기 (0.1초 단위로 쪼개서 종료 플래그 즉시 반응)
            for _ in range(self.INTERVAL * 10):
                if self._stop:
                    break
                time.sleep(0.1)

        print('\nSystem stopped....')
