import random
import datetime

LOG_FILE_PATH = 'env_log.csv'

internal_temperature = 'mars_base_internal_temperature'
external_temperature = 'mars_base_external_temperature'
internal_humidity = 'mars_base_internal_humidity'
external_illuminance = 'mars_base_external_illuminance'
internal_co2 = 'mars_base_internal_co2'
internal_oxygen = 'mars_base_internal_oxygen'


class DummySensor:
    def __init__(self):
        self.env_values = {
            internal_temperature: 0.0,
            external_temperature: 0.0,
            internal_humidity: 0.0,
            external_illuminance: 0.0,
            internal_co2: 0.0,
            internal_oxygen: 0.0,
        }

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
        print(f'  기지 내부 온도      : {self.env_values[internal_temperature]:>8.1f} °C')
        print(f'  기지 외부 온도      : {self.env_values[external_temperature]:>8.1f} °C')
        print(f'  기지 내부 습도      : {self.env_values[internal_humidity]:>8.1f} %')
        print(f'  기지 외부 광량      : {self.env_values[external_illuminance]:>8.1f} W/m²')
        print(f'  기지 내부 CO₂ 농도  : {self.env_values[internal_co2]:>8.4f} %')
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

            print(f'[로그] 환경 데이터 기록 완료')

        except PermissionError:
            print(f'[오류] 로그 파일 쓰기 권한이 없어요: {log_file}')

        except OSError as error:
            print(f'[오류] 로그 파일 저장 중 문제가 생겼어요: {error}')


def main():
    ds = DummySensor()

    # 랜덤데이터 할당
    ds.set_env()

    # 화면에 출력하고, 로그 파일에 기록한 뒤, env_values를 반환
    env = ds.get_env()

    print('\n[결과] 환경 데이터 확인')
    for key, value in env.items():
        print(f'    {key}: {value}')


if __name__ == '__main__':
    main()