import itertools
import multiprocessing
import os
import string
import time
import zipfile


ZIP_FILE = 'emergency_storage_key.zip'
PASSWORD_FILE = 'password.txt'

PASSWORD_LENGTH = 6
CHARACTERS = string.digits + string.ascii_lowercase
PRINT_INTERVAL = 100000


PRIORITY_WORDS = [
    'coffee',
    'oxygen',
    'storage',
    'emergency',
    'mars',
    'base',
    'door',
    'key',
    'food',
    'water',
    'rescue',
    'space',
    'human',
    'life',
]


def make_elapsed_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f'{minutes}분 {secs}초'


def find_smallest_file(zip_file):
    smallest_file = None

    for file_info in zip_file.infolist():
        if file_info.filename.endswith('/') or file_info.file_size == 0:
            continue

        if smallest_file is None:
            smallest_file = file_info
        elif file_info.compress_size < smallest_file.compress_size:
            smallest_file = file_info

    if smallest_file:
        return smallest_file.filename

    return None


def try_password(zip_file, target_file, password):
    """이미 열린 ZipFile 객체로 암호를 검증한다."""
    try:
        zip_file.read(target_file, pwd=password.encode('utf-8'))
        return True
    except Exception:
        return False


def save_password(password):
    try:
        with open(PASSWORD_FILE, 'w', encoding='utf-8') as file:
            file.write(password)
        print(f'[저장] {PASSWORD_FILE} 저장 완료')
    except OSError as error:
        print('[오류] password.txt 저장 실패')
        print(error)


def check_zip_file(zip_path):
    if not os.path.exists(zip_path):
        print(f'[오류] 파일을 찾을 수 없습니다: {zip_path}')
        return None

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            return find_smallest_file(zip_file)
    except zipfile.BadZipFile:
        print('[오류] 정상적인 ZIP 파일이 아닙니다.')
    except OSError as error:
        print('[오류] ZIP 파일 처리 중 문제가 발생했습니다.')
        print(error)

    return None


def make_priority_candidates():
    candidates = []

    for word in PRIORITY_WORDS:
        if len(word) == PASSWORD_LENGTH:
            candidates.append(word)

        if len(word) < PASSWORD_LENGTH:
            remain = PASSWORD_LENGTH - len(word)

            for number in range(10 ** remain):
                suffix = str(number).zfill(remain)
                candidates.append(word + suffix)

            for number in range(10 ** remain):
                prefix = str(number).zfill(remain)
                candidates.append(prefix + word)

    for number in range(1000000):
        candidates.append(str(number).zfill(6))

    return candidates


def try_priority_passwords(zip_path, target_file, start_time):
    candidates = make_priority_candidates()

    print('[1단계] 우선순위 후보 검사 시작')
    print(f'[정보] 후보 수: {len(candidates):,}')
    print('-' * 50)

    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for count, password in enumerate(candidates, start=1):
            if count % PRINT_INTERVAL == 0:
                elapsed = time.time() - start_time
                print(
                    f'[진행] {count:,}회 | 현재: {password} | '
                    f'{make_elapsed_time(elapsed)}'
                )

            if try_password(zip_file, target_file, password):
                elapsed = time.time() - start_time
                print('[성공] 우선순위 후보에서 암호 발견')
                print(f'[암호] {password}')
                print(f'[반복] {count:,}회')
                print(f'[시간] {make_elapsed_time(elapsed)}')
                return password

    print('[1단계 종료] 우선순위 후보에서 찾지 못했습니다.')
    return None


def number_to_password(number):
    indexes = [0] * PASSWORD_LENGTH

    for position in range(PASSWORD_LENGTH - 1, -1, -1):
        indexes[position] = number % len(CHARACTERS)
        number //= len(CHARACTERS)

    return ''.join(CHARACTERS[index] for index in indexes)


def worker(args):
    worker_id, start, end, zip_path, target_file, found_event, result_queue = args
    local_count = 0

    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for number in range(start, end):
            if found_event.is_set():
                return

            password = number_to_password(number)
            local_count += 1

            if try_password(zip_file, target_file, password):
                result_queue.put((worker_id, password, local_count))
                found_event.set()
                return


def unlock_zip_bruteforce(zip_path, target_file, start_time):
    print('\n[2단계] 전체 브루트포스 시작')
    print('시간이 오래 걸릴 수 있습니다.')
    print('-' * 50)

    total = len(CHARACTERS) ** PASSWORD_LENGTH
    cpu_count = max(1, multiprocessing.cpu_count() - 1)
    chunk_size = total // cpu_count

    found_event = multiprocessing.Event()
    result_queue = multiprocessing.Queue()
    processes = []

    for worker_id in range(cpu_count):
        start = worker_id * chunk_size

        if worker_id == cpu_count - 1:
            end = total
        else:
            end = start + chunk_size

        process = multiprocessing.Process(
            target=worker,
            args=(
                (
                    worker_id + 1,
                    start,
                    end,
                    zip_path,
                    target_file,
                    found_event,
                    result_queue,
                ),
            ),
        )
        processes.append(process)
        process.start()

    try:
        while True:
            if not result_queue.empty():
                worker_id, password, local_count = result_queue.get()
                found_event.set()

                for process in processes:
                    if process.is_alive():
                        process.terminate()

                for process in processes:
                    process.join()

                elapsed = time.time() - start_time
                print('[성공] 전체 브루트포스에서 암호 발견')
                print(f'[작업 번호] {worker_id}')
                print(f'[작업 반복 회수] {local_count:,}')
                print(f'[암호] {password}')
                print(f'[시간] {make_elapsed_time(elapsed)}')
                return password

            alive = any(process.is_alive() for process in processes)

            if not alive:
                break

            elapsed = time.time() - start_time
            print(f'\r[진행 중] 경과 시간: {make_elapsed_time(elapsed)}', end='')
            time.sleep(1)

    except KeyboardInterrupt:
        print('\n[중단] 사용자가 작업을 중단했습니다.')
        found_event.set()

    for process in processes:
        if process.is_alive():
            process.terminate()

    for process in processes:
        process.join()

    print('\n[실패] 암호를 찾지 못했습니다.')
    return None


def unlock_zip(zip_path=ZIP_FILE):
    start_time = time.time()
    start_text = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

    print('=' * 50)
    print('Emergency Storage 암호 해독기')
    print('=' * 50)
    print(f'[시작 시간] {start_text}')
    print(f'[대상 파일] {zip_path}')
    print(f'[암호 조건] 숫자 + 소문자 알파벳 6자리')
    print('-' * 50)

    target_file = check_zip_file(zip_path)

    if target_file is None:
        return None

    print(f'[검사 대상 파일] {target_file}')

    password = try_priority_passwords(zip_path, target_file, start_time)

    if password is None:
        password = unlock_zip_bruteforce(zip_path, target_file, start_time)

    if password:
        save_password(password)
        return password

    return None


if __name__ == '__main__':
    multiprocessing.freeze_support()
    unlock_zip()