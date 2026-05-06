from dummy_sensor import DummySensor
from mission_computer import MissionComputer


def main():
    ds = DummySensor()

    RunComputer = MissionComputer(ds)
    RunComputer.get_sensor_data()


if __name__ == '__main__':
    main()