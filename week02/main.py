import pickle

CSV_FILE_PATH = 'Mars_Base_Inventory_List.csv'
DANGER_CSV_PATH = 'Mars_Base_Inventory_danger.csv'
BIN_FILE_PATH = 'Mars_Base_Inventory_List.bin'

FLAMMABILITY_THRESHOLD = 0.7


def read_csv(file_path):
    lines = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없어요: {file_path}')
        print('       파일 이름과 경로를 다시 확인해 보세요!')

    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없어요: {file_path}')
        print('       파일 속성에서 읽기 권한을 확인해 보세요!')

    except UnicodeDecodeError:
        print('[오류] 인코딩 문제! CP949로 다시 시도할게요...')
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                lines = f.readlines()
            print('       CP949 인코딩으로 성공적으로 읽었어요!')
        except Exception as error:
            print(f'       재시도도 실패했어요: {error}')

    except OSError as error:
        print(f'[오류] 파일 시스템 오류: {error}')

    return lines


def print_raw_csv(lines):
    print('\n' + '=' * 70)
    print('  원본 CSV 파일 내용')
    print('=' * 70)

    for line in lines:
        print(line.strip())

    print('=' * 70)


def normalize_key(key):
    return (
        key.strip()
        .lower()
        .replace(' ', '_')
        .replace('(', '')
        .replace(')', '')
        .replace('/', '_')
        .replace('³', '3')
    )


def parse_csv(lines):
    records = []
    headers = []

    for index, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        parts = [p.strip() for p in line.split(',')]

        if index == 0:
            headers = [normalize_key(h) for h in parts]
            continue

        if len(parts) != len(headers):
            continue

        record = dict(zip(headers, parts))

        try:
            record['flammability'] = float(record['flammability'])
        except ValueError:
            record['flammability'] = 0.0

        records.append(record)

    return records


def sort_by_flammability(records):
    sorted_records = sorted(
        records,
        key=lambda record: record['flammability'],
        reverse=True
    )

    return sorted_records


def print_records(records, title='물질 목록'):
    print('\n' + '=' * 70)
    print(f'  {title}  (총 {len(records)}개)')
    print('=' * 70)

    if not records:
        print("데이터 없음")
        return

    headers = list(records[0].keys())

    print(f'  {"No.":<5}', end='')
    for h in headers:
        print(f'{h:<20}', end='')
    print()

    print('  ' + '-' * (5 + len(headers) * 20))

    for index, record in enumerate(records):
        print(f'  {index + 1:<5}', end='')

        for h in headers:
            value = record[h]

            if isinstance(value, float):
                print(f'{value:<20.2f}', end='')
            else:
                print(f'{str(value):<20}', end='')

        print()

    print('=' * 70)


def filter_dangerous(records, threshold=FLAMMABILITY_THRESHOLD):
    dangerous = [r for r in records if r['flammability'] >= threshold]

    return dangerous


def save_danger_csv(records, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('Substance,Weight (g/cm³),Specific Gravity,Strength,Flammability\n')

            for record in records:
                f.write(
                    f'{record.get("substance", "")},'
                    f'{record.get("weight_g_cm3", "")},'
                    f'{record.get("specific_gravity", "")},'
                    f'{record.get("strength", "")},'
                    f'{record.get("flammability", "")}\n'
                )

    except PermissionError:
        print(f'{file_path}파일의 쓰기 권한이 없어요: ')

    except OSError as error:
        print(f'{file_path}파일의 CSV 저장 중 오류 발생: {error}')


def save_binary(records, file_path):
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(records, f)


    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없어요: {file_path}')

    except OSError as error:
        print(f'[오류] 이진 파일 저장 중 오류 발생: {error}')


def load_and_print_binary(file_path):
    try:
        with open(file_path, 'rb') as f:
            records = pickle.load(f)

        print_records(records, title='[보너스] 이진 파일에서 복원된 목록 (인화성 순)')

        return records

    except FileNotFoundError:
        print(f'[오류] 이진 파일이 없어요: {file_path}')

    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없어요: {file_path}')

    except Exception as error:
        print(f'[오류] 이진 파일 읽기 실패: {error}')

    return []


def main():
    lines = read_csv(CSV_FILE_PATH)

    if not lines:
        print('파일을 읽지 못했습니다. 프로그램 종료')
        return

    print_raw_csv(lines)

    records = parse_csv(lines)

    # 정렬
    sorted_records = sort_by_flammability(records)
    print_records(sorted_records, title='전체 물질 목록 (인화성 높은 순)')

    # 인화성 0.7 이상 필터링
    dangerous_records = filter_dangerous(sorted_records)
    print_records(
        dangerous_records,
        title=f'인화성 {FLAMMABILITY_THRESHOLD} 이상 물질')

    # 위험 물질 CSV 파일로 저장
    save_danger_csv(dangerous_records, DANGER_CSV_PATH)

    # 이진 파일로 저장
    save_binary(sorted_records, BIN_FILE_PATH)

    # 이진 파일 읽고 출력
    load_and_print_binary(BIN_FILE_PATH)

    print('\n모든 작업 완료')


if __name__ == '__main__':
    main()
