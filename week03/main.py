from dummy_sensor import DummySensor
from mission_computer import MissionComputer


def main():
    ds = DummySensor()
    run_computer = MissionComputer(ds)
    run_computer.get_sensor_data()


if __name__ == '__main__':
    main()