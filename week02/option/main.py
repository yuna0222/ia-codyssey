PI = 3.141592653589793

# 화성 중력은 지구의 약 37.9%
MARS_GRAVITY_RATIO = 0.379

# 재질별 밀도
MATERIAL_DENSITY = {
    '유리': 2.4,
    '알루미늄': 2.7,
    '탄소강': 7.85,
}

material = ''  # 재질
diameter = 0.0  # 지름 (m)
thickness = 0.0  # 두께 (cm)
area = 0.0  # 반구 곡면적 (m²)
weight = 0.0  # 화성 기준 무게 (kg)


#
#   반구(Hemisphere) 곡면적 공식:
#     구의 전체 겉넓이 = 4 * π * r²
#     반구 곡면적     = 2 * π * r² // 바닥 원판 제외
#
#   무게 계산:
#     부피(cm³) = 곡면적(cm²) × 두께(cm)
#     지구 무게(g) = 부피 × 밀도(g/cm³)
#     화성 무게(kg) = 지구 무게 × 화성 중력 비율 ÷ 1000
#

def sphere_area(diameter, material='유리', thickness=1.0):
    global area, weight

    # 반지름 = 지름 ÷ 2
    radius = diameter / 2

    # ★ 반구 곡면적 (m²) = 2 * π * r²
    dome_area = 2 * PI * (radius ** 2)

    # 면적 단위 변환: m² → cm²  (1m² = 10,000cm²)
    area_cm2 = dome_area * 10000

    # 부피 (cm³) = 곡면적 (cm²) × 두께 (cm)
    volume_cm3 = area_cm2 * thickness

    # 재질 밀도 가져오기 (목록에 없으면 유리 기본값 2.4 사용)
    density = MATERIAL_DENSITY.get(material, 2.4)

    # 지구 기준 무게 (g) = 부피 × 밀도
    earth_weight_g = volume_cm3 * density

    # 화성 기준 무게 (g) = 지구 무게 × 화성/지구 중력 비율
    mars_weight_g = earth_weight_g * MARS_GRAVITY_RATIO

    # g → kg 변환
    mars_weight_kg = mars_weight_g / 1000

    # 전역변수에 결과 저장
    area = dome_area
    weight = mars_weight_kg

    return dome_area, mars_weight_kg


def print_result():
    print('\n[계산 결과]')
    print(
        f'재질: {material}\n'
        f'지름: {diameter:.3f}\n'
        f'두께: {thickness:.3f}\n'
        f'면적: {area:.3f}\n'
        f'무게: {weight:.3f} kg'
    )


def get_diameter():
    while True:
        raw = input('  지름을 입력하세요 (m, 0 초과 / 종료: q): ').strip()

        if raw.lower() == 'q':
            return None

        try:
            value = float(raw)
        except ValueError:
            print('  [오류] 숫자를 입력해 주세요! (예: 10 또는 10.5)')
            continue

        if value <= 0:
            print('  [오류] 지름은 0보다 커야 해요!')
            continue

        return value


def get_material():
    print('  사용 가능한 재질: 유리, 알루미늄, 탄소강')
    raw = input('  재질을 입력하세요 (Enter = 유리): ').strip()

    if raw in MATERIAL_DENSITY:
        return raw

    if raw == '':
        print('  재질 입력 없음 → 기본값 [유리] 사용')
    else:
        print(f'  [{raw}]은(는) 목록에 없어요 → 기본값 [유리] 사용')

    return '유리'


def get_thickness():
    raw = input('  두께를 입력하세요 (cm, Enter = 1.0): ').strip()

    if raw == '':
        print('  두께 입력 없음 → 기본값 [1.0 cm] 사용')
        return 1.0

    try:
        value = float(raw)
    except ValueError:
        print('  [오류] 숫자가 아니에요 → 기본값 [1.0 cm] 사용')
        return 1.0

    if value <= 0:
        print('  [오류] 두께는 0보다 커야 해요 → 기본값 [1.0 cm] 사용')
        return 1.0

    return value


def main():
    global material, diameter, thickness

    print('=' * 55)
    print('  화성 기지 돔 설계 계산기')
    print('  종료하려면 지름 입력 시 q 를 입력하세요.')
    print('=' * 55)

    while True:
        print('\n' + '-' * 55)

        result = get_diameter()
        if result is None:
            print('\n  프로그램을 종료합니다.')
            break
        diameter = result

        # 재질 입력
        material = get_material()

        # 두께 입력
        thickness = get_thickness()

        # 계산 실행
        sphere_area(diameter, material, thickness)

        # 결과 출력
        print_result()


if __name__ == '__main__':
    main()
