import time
import datetime

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
    def __init__(self, sensor):
        self.sensor = sensor
        self.env_values = {key: 0.0 for key in ENV_KEYS}
        self.history = {key: [] for key in ENV_KEYS}

    def print_average(self):
        avg = {
            key: round(sum(vals) / len(vals), 4)
            for key, vals in self.history.items() if vals
        }

        print('\n' + '*' * 55)
        print('  [5분 평균값]')
        print('*' * 55)
        print(dict_to_json(avg))
        print('*' * 55)

        self.history = {key: [] for key in ENV_KEYS}

    def get_sensor_data(self):
        print('[info] 정지하려면 Ctrl+C 를 누르세요.')

        count = 0

        try:
            while True:
                self.sensor.set_env()
                sensor_data = self.sensor.get_env()

                for key in ENV_KEYS:
                    self.env_values[key] = sensor_data[key]

                for key in ENV_KEYS:
                    self.history[key].append(self.env_values[key])

                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'\n  [{timestamp}] MissionComputer JSON 출력:')
                print(dict_to_json(self.env_values))

                count += 1

                if count >= 60:
                    self.print_average()
                    count = 0

                time.sleep(5)

        except KeyboardInterrupt:
            print('\n시스템이 종료됩니다.')
