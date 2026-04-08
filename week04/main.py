"""
화성 기지 미션 컴퓨터
동양미래대학교 컴퓨터공학부 - Codyssey 과제 (문제 5)

[구조 설명]
  공통 상수       → DummySensor와 MissionComputer가 함께 재활용해요.
  DummySensor     → 랜덤 환경 데이터 생성 (문제 4 코드 그대로)
  MissionComputer → 5초마다 센서 데이터를 JSON 형태로 출력

[보너스]
  Ctrl+C 입력 시 'System stopped....' 출력 후 종료
  60회(5분)마다 각 항목 평균값 별도 출력
"""

import random
import time
import datetime

# =============================================================
# 공통 상수: 딕셔너리 키 이름
#
#   DummySensor와 MissionComputer 둘 다 같은 키를 써요.
#   여기서 한 번만 정의하면 두 클래스가 함께 재활용할 수 있어요.
#   오타 방지 효과도 있어요!
# =============================================================

LOG_FILE_PATH = 'env_log.csv'

internal_temperature = 'mars_base_internal_temperature'
external_temperature = 'mars_base_external_temperature'
internal_humidity = 'mars_base_internal_humidity'
external_illuminance = 'mars_base_external_illuminance'
internal_co2 = 'mars_base_internal_co2'
internal_oxygen = 'mars_base_internal_oxygen'

# 키 순서를 리스트로 관리해요.
# DummySensor의 초기화, MissionComputer의 history 등에서 함께 재활용해요.
ENV_KEYS = [
    internal_temperature,
    external_temperature,
    internal_humidity,
    external_illuminance,
    internal_co2,
    internal_oxygen,
]


# =============================================================
# DummySensor 클래스 (문제 4 코드 그대로 재활용)
# =============================================================

class DummySensor:

    def __init__(self):
        # 0.0(float)으로 초기화해야 이후 float 대입 시 타입 경고가 없어요.
        # ENV_KEYS를 재활용해서 한 줄로 깔끔하게 초기화해요.
        self.env_values = {key: 0.0 for key in ENV_KEYS}

    def set_env(self):
        self.env_values[internal_temperature] = round(random.uniform(18, 30), 1)
        self.env_values[external_temperature] = round(random.uniform(0, 21), 1)
        self.env_values[internal_humidity] = round(random.uniform(50, 60), 1)
        self.env_values[external_illuminance] = round(random.uniform(500, 715), 1)
        self.env_values[internal_co2] = round(random.uniform(0.02, 0.1), 4)
        self.env_values[internal_oxygen] = round(random.uniform(4, 7), 2)

    def get_env(self):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print('\n' + '=' * 55)
        print(f'화성 기지 환경 데이터  [{timestamp}]')
        print('=' * 55)
        print(f'  기지 내부 온도      : {self.env_values[internal_temperature]:>8.1f} C')
        print(f'  기지 외부 온도      : {self.env_values[external_temperature]:>8.1f} C')
        print(f'  기지 내부 습도      : {self.env_values[internal_humidity]:>8.1f} %')
        print(f'  기지 외부 광량      : {self.env_values[external_illuminance]:>8.1f} W/m2')
        print(f'  기지 내부 CO2 농도  : {self.env_values[internal_co2]:>8.4f} %')
        print(f'  기지 내부 산소 농도  : {self.env_values[internal_oxygen]:>8.2f} %')
        print('=' * 55)

        self.write_log(timestamp)

        return self.env_values

    def write_log(self, timestamp, log_file=LOG_FILE_PATH):
        try:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    is_new_file = (f.read().strip() == '')
            except FileNotFoundError:
                is_new_file = True

            with open(log_file, 'a', encoding='utf-8') as f:
                if is_new_file:
                    f.write(
                        'timestamp,'
                        'internal_temperature,'
                        'external_temperature,'
                        'internal_humidity,'
                        'external_illuminance,'
                        'internal_co2,'
                        'internal_oxygen\n'
                    )

                f.write(
                    f'{timestamp},'
                    f'{self.env_values[internal_temperature]},'
                    f'{self.env_values[external_temperature]},'
                    f'{self.env_values[internal_humidity]},'
                    f'{self.env_values[external_illuminance]},'
                    f'{self.env_values[internal_co2]},'
                    f'{self.env_values[internal_oxygen]}\n'
                )

            print('[로그] 환경 데이터 기록 완료')

        except PermissionError:
            print(f'[오류] 로그 파일 쓰기 권한이 없어요: {log_file}')

        except OSError as error:
            print(f'[오류] 로그 파일 저장 중 문제가 생겼어요: {error}')


# =============================================================
# MissionComputer 클래스 (문제 5 신규)
#
#   get_sensor_data():
#     ds에서 데이터를 받아 env_values에 저장하고
#     JSON 형태로 5초마다 반복 출력해요.
#
#   dict_to_json():
#     import json 없이 딕셔너리를 JSON 문자열로 직접 변환해요.
#
#   [보너스 1] Ctrl+C → KeyboardInterrupt 로 정지
#     threading 없이 처리하는 가장 단순한 방법이에요.
#     try-except KeyboardInterrupt 로 Ctrl+C를 잡아서
#     'System stopped....' 를 출력하고 루프를 끝내요.
#
#   [보너스 2] 5분 평균
#     5초 x 60회 = 5분
#     history 리스트에 값을 쌓다가 60개가 되면 평균 출력 후 초기화해요.
# =============================================================


def dict_to_json(data):
    """
    딕셔너리를 JSON 형태 문자열로 변환합니다.
    import json 없이 직접 포맷팅해요.

    JSON 규칙:
      - 키는 항상 큰따옴표로 감싸요: "key"
      - 마지막 항목엔 쉼표가 없어요
    """
    lines = ['{']
    keys = list(data.keys())
    for i, key in enumerate(keys):
        value = data[key]
        # 문자열이면 따옴표로 감싸고, 숫자면 그대로 써요
        formatted = f'"{value}"' if isinstance(value, str) else str(value)
        comma = ',' if i < len(keys) - 1 else ''
        lines.append(f'    "{key}": {formatted}{comma}')
    lines.append('}')
    return '\n'.join(lines)


class MissionComputer:

    def __init__(self, sensor):
        # 외부에서 만든 ds 인스턴스를 받아서 self.sensor에 저장해요.
        # 이렇게 하면 MissionComputer가 어떤 센서든 받아서 쓸 수 있어요.
        # (나중에 실제 센서 클래스로 교체도 쉬워져요!)
        self.sensor = sensor

        # ENV_KEYS를 재활용해서 DummySensor와 동일한 구조로 초기화해요.
        self.env_values = {key: 0.0 for key in ENV_KEYS}

        # ★ [보너스 2] 항목별로 빈 리스트를 만들어요.
        # 측정할 때마다 값을 append하고 60개가 되면 평균을 내요.
        self.history = {key: [] for key in ENV_KEYS}

    def print_average(self):
        """
        ★ [보너스 2] history에 쌓인 값의 평균을 계산해서 출력해요.
        출력 후 history를 초기화해요.
        """
        # 각 키마다 리스트 합계 / 개수 = 평균 계산
        avg = {
            key: round(sum(vals) / len(vals), 4)
            for key, vals in self.history.items() if vals
        }

        print('\n' + '*' * 55)
        print('  [5분 평균값]')
        print('*' * 55)
        print(dict_to_json(avg))
        print('*' * 55)

        # 평균 출력 후 history 초기화 (ENV_KEYS 재활용)
        self.history = {key: [] for key in ENV_KEYS}

    def get_sensor_data(self):
        """
        5초마다 센서 데이터를 읽어 JSON 형태로 출력합니다.

        [보너스 1] 정지 방법
          threading 없이 Ctrl+C (KeyboardInterrupt) 로 정지해요.
          try 블록 안에서 루프를 돌다가 Ctrl+C가 눌리면
          except KeyboardInterrupt 로 잡아서 메시지를 출력해요.
        """
        print('[안내] 정지하려면 Ctrl+C 를 누르세요.')

        count = 0  # 5분 평균 계산용 카운터

        # ★ [보너스 1] Ctrl+C를 KeyboardInterrupt로 잡아요.
        try:
            while True:
                # self.sensor(= ds)에서 새 환경값 생성 후 env_values에 복사
                # ENV_KEYS를 재활용해서 반복문으로 깔끔하게 처리해요.
                self.sensor.set_env()
                sensor_data = self.sensor.get_env()
                for key in ENV_KEYS:
                    self.env_values[key] = sensor_data[key]

                # ★ [보너스 2] history에 이번 측정값 추가
                for key in ENV_KEYS:
                    self.history[key].append(self.env_values[key])

                # 현재 시각 + JSON 출력
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'\n  [{timestamp}] MissionComputer JSON 출력:')
                print(self.dict_to_json(self.env_values))

                count += 1

                # 60회(5분)마다 평균 출력 후 카운터 초기화
                if count >= 60:
                    self.print_average()
                    count = 0

                # 5초 대기
                time.sleep(5)

        except KeyboardInterrupt:
            # Ctrl+C 를 누르면 여기로 와요.
            print('\nSystem stopped....')


# =============================================================
# main(): 전체 실행 흐름 관리
#
#   ds와 RunComputer를 main() 안에서 선언해요.
#   전역변수로 두면 어디서든 건드릴 수 있어서 코드가 예측하기 어려워져요.
#   main() 안에 두면 "여기서 시작한다"는 흐름이 명확해져요.
# =============================================================

def main():
    # DummySensor를 ds라는 이름으로 인스턴스화해요. (문제 조건)
    ds = DummySensor()

    # ds를 MissionComputer에 넘겨줘요.
    # MissionComputer는 받은 센서를 self.sensor로 저장해서 사용해요.
    RunComputer = MissionComputer(ds)

    RunComputer.get_sensor_data()


if __name__ == '__main__':
    main()
