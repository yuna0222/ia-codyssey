import numpy as np

FILE_1 = 'mars_base_main_parts-001.csv'
FILE_2 = 'mars_base_main_parts-002.csv'
FILE_3 = 'mars_base_main_parts-003.csv'
OUTPUT_FILE = 'parts_to_work_on.csv'

# 평균 강도가 이 값보다 작으면 보강 대상이에요
THRESHOLD = 50


def read_csv(file_path):
    # CSV 파일을 numpy ndarray로 읽어서 반환
    return np.genfromtxt(
        file_path,
        delimiter=',',
        dtype=None,
        encoding='utf-8-sig',  # BOM(바이트 순서 표시) 있는 UTF-8 파일 처리
        skip_header=1  # 첫 번째 줄(헤더) 건너뜀
    )


def merge_arrays(arr1, arr2, arr3):
    # 3개의 ndarray를 행 방향으로 합쳐서 반환
    return np.concatenate([arr1, arr2, arr3], axis=0)


def calc_average(parts):
    # 'f0': 첫 번째 필드(부품 이름) 전체
    # np.unique(): 중복 제거 + 정렬된 고유값 목록
    if parts.size == 0:
        return []
    part_names = np.unique(parts['f0'])

    averages = []
    for name in part_names:
        mask = parts['f0'] == name

        # 필터링된 행에서 강도(f1) 뽑아서 float으로 변환
        strengths = parts[mask]['f1'].astype(float)

        avg = round(float(np.mean(strengths)), 2)
        averages.append((name, avg))

    return averages


def save_weak_parts(averages, file_path, threshold=THRESHOLD):
    weak_parts = [(name, avg) for name, avg in averages if avg < threshold]

    print(f'\n평균 강도 {threshold} 미만 부품: {len(weak_parts)}개')
    for name, avg in weak_parts:
        print(f'  {name}: {avg}')

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('parts,average_strength\n')
            for name, avg in weak_parts:
                f.write(f'{name},{avg}\n')


    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없어요: {file_path}')

    except OSError as error:
        print(f'[오류] 파일 저장 중 문제가 생겼어요: {error}')

    return weak_parts


def load_and_transpose_parts(file_path):
    try:
        parts2 = np.genfromtxt(
            file_path,
            delimiter=',',
            dtype=None,
            encoding='utf-8',
            skip_header=1
        )

        print('[보너스] parts2 내용:')
        print(parts2)

        if parts2.size == 0:
            print('[보너스] 전치할 데이터가 없습니다.')
            return

        names_row = parts2['f0'].astype(str)  # 부품 이름 배열
        values_row = parts2['f1'].astype(str)  # 강도 배열 (str로 통일)
        matrix_2d = np.array([names_row, values_row])

        # 전치
        parts3 = matrix_2d.T

        print('parts3 내용 (각 행 = [부품명, 평균강도]):')
        print(parts3)

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없어요: {file_path}')

    except OSError as error:
        print(f'[오류] 파일 읽기 중 문제가 생겼어요: {error}')


def main():
    arr1 = read_csv(FILE_1)
    arr2 = read_csv(FILE_2)
    arr3 = read_csv(FILE_3)

    parts = merge_arrays(arr1, arr2, arr3)

    averages = calc_average(parts)

    print('\n[전체 부품 평균 강도]')
    for name, avg in averages:
        marker = ' [보강 필요]' if avg < THRESHOLD else ''
        print(f'  {name:<30}: {avg:>6.2f}{marker}')

    # 보강 대상 부품 저장
    save_weak_parts(averages, OUTPUT_FILE)

    load_and_transpose_parts(OUTPUT_FILE)


if __name__ == '__main__':
    main()
