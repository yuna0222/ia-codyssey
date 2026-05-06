import multiprocessing
import sys
import threading

from dummy_sensor import DummySensor
from mission_computer import MissionComputer

# 반복 출력 주기 (초)
REPEAT_INTERVAL = 20


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
