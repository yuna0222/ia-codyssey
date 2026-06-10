"""
make_png.py - 표준 라이브러리만으로 PNG 이미지를 생성한다.

외부 라이브러리(matplotlib 등) 없이 struct, zlib만 사용하여
화성 날씨 요약 결과를 PNG 파일로 저장한다.
"""

import struct
import zlib


# ─────────────────────────────────────────────────────────────────
# 5x7 비트맵 폰트 (대문자, 숫자, 기호)
# ─────────────────────────────────────────────────────────────────

FONT_5X7 = {
    ' ': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
    '0': [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    '2': [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111],
    '3': [0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110],
    '4': [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    '5': [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    '6': [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    '7': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    '8': [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    '9': [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    'A': [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'C': [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'F': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    'G': [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111],
    'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'I': [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    'J': [0b00111, 0b00010, 0b00010, 0b00010, 0b10010, 0b10010, 0b01100],
    'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'M': [0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001],
    'N': [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    'O': [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'P': [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    'Q': [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'S': [0b01110, 0b10001, 0b10000, 0b01110, 0b00001, 0b10001, 0b01110],
    'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    'W': [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    'X': [0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b01010, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00000],
    ':': [0b00000, 0b00100, 0b00000, 0b00000, 0b00000, 0b00100, 0b00000],
    '-': [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    '/': [0b00000, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b00000],
    '%': [0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b01010, 0b10001],
    '~': [0b00000, 0b00000, 0b01101, 0b10010, 0b00000, 0b00000, 0b00000],
    '>': [0b10000, 0b01000, 0b00100, 0b00010, 0b00100, 0b01000, 0b10000],
    '(': [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ')': [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
}


# ─────────────────────────────────────────────────────────────────
# 캔버스 (픽셀 배열)
# ─────────────────────────────────────────────────────────────────

def make_canvas(width, height, bg=(255, 255, 255)):
    """지정한 크기의 캔버스를 생성한다."""
    return {
        'width': width,
        'height': height,
        'pixels': [bg] * (width * height),
    }


def set_pixel(canvas, x, y, color):
    """캔버스의 (x, y) 위치에 색상을 설정한다."""
    w = canvas['width']
    h = canvas['height']
    if 0 <= x < w and 0 <= y < h:
        canvas['pixels'][y * w + x] = color


def draw_rect(canvas, x, y, w, h, color):
    """사각형을 채워 그린다."""
    for dy in range(h):
        for dx in range(w):
            set_pixel(canvas, x + dx, y + dy, color)


def draw_rect_outline(canvas, x, y, w, h, color, thickness=1):
    """사각형 테두리를 그린다."""
    for t in range(thickness):
        for dx in range(w):
            set_pixel(canvas, x + dx, y + t, color)
            set_pixel(canvas, x + dx, y + h - 1 - t, color)
        for dy in range(h):
            set_pixel(canvas, x + t, y + dy, color)
            set_pixel(canvas, x + w - 1 - t, y + dy, color)


def draw_text(canvas, text, x, y, color, scale=1):
    """비트맵 폰트로 텍스트를 그린다. 인식 불가 문자는 건너뛴다."""
    cx = x
    for ch in text.upper():
        glyph = FONT_5X7.get(ch, FONT_5X7[' '])
        for gy, row_bits in enumerate(glyph):
            for gx in range(5):
                if row_bits & (1 << (4 - gx)):
                    for sy in range(scale):
                        for sx in range(scale):
                            set_pixel(
                                canvas,
                                cx + gx * scale + sx,
                                y + gy * scale + sy,
                                color
                            )
        cx += (5 + 1) * scale
    return cx  # 다음 문자 시작 x 반환


def draw_bar(canvas, x, y, bar_w, bar_h, color):
    """막대 하나를 그린다."""
    draw_rect(canvas, x, y, bar_w, bar_h, color)
    draw_rect_outline(canvas, x, y, bar_w, bar_h, (80, 80, 80))


# ─────────────────────────────────────────────────────────────────
# PNG 인코더 (struct + zlib 만 사용)
# ─────────────────────────────────────────────────────────────────

def encode_png(canvas):
    """캔버스를 PNG 바이너리로 인코딩하여 반환한다."""
    width = canvas['width']
    height = canvas['height']
    pixels = canvas['pixels']

    def make_chunk(tag, data):
        """PNG 청크를 생성한다."""
        crc = zlib.crc32(tag + data) & 0xffffffff
        header = struct.pack('>I', len(data))
        trailer = struct.pack('>I', crc)
        return header + tag + data + trailer

    # IHDR: 너비, 높이, 비트심도(8), 색상타입(2=RGB)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

    # IDAT: 각 행 앞에 필터 바이트 0x00 추가 후 압축
    raw_rows = b''
    for row in range(height):
        raw_rows += b'\x00'
        for col in range(width):
            r, g, b = pixels[row * width + col]
            raw_rows += bytes([r, g, b])

    png = (
        b'\x89PNG\r\n\x1a\n'
        + make_chunk(b'IHDR', ihdr_data)
        + make_chunk(b'IDAT', zlib.compress(raw_rows, 6))
        + make_chunk(b'IEND', b'')
    )
    return png


# ─────────────────────────────────────────────────────────────────
# 화성 날씨 요약 PNG 생성
# ─────────────────────────────────────────────────────────────────

# 색상 팔레트
COLOR_BG = (245, 248, 255)
COLOR_HEADER_BG = (30, 60, 120)
COLOR_HEADER_TEXT = (255, 255, 255)
COLOR_LABEL = (60, 60, 80)
COLOR_VALUE = (20, 80, 180)
COLOR_BORDER = (180, 190, 210)
COLOR_BAR_TEMP_AVG = (76, 155, 232)
COLOR_BAR_TEMP_MIN = (110, 207, 246)
COLOR_BAR_TEMP_MAX = (244, 162, 97)
COLOR_BAR_STORM = (230, 57, 70)
COLOR_AXIS = (100, 100, 100)


def draw_summary_image(summary, out_path='mars_weather_summary.png'):
    """
    요약 딕셔너리를 받아 PNG 이미지를 생성하고 저장한다.

    이미지 구성:
      - 상단 헤더 (제목)
      - 좌측 패널: 요약 텍스트 (총 건수, 기간, 기온, 폭풍)
      - 우측 패널: 막대 차트 (평균/최저/최고 기온, 폭풍 일수)

    Args:
        summary (dict): fetch_summary()가 반환한 요약 딕셔너리
        out_path (str): 저장할 PNG 파일 경로
    """
    w = 800
    h = 400
    canvas = make_canvas(w, h, COLOR_BG)

    # ── 헤더 ────────────────────────────────────────────────────
    draw_rect(canvas, 0, 0, w, 48, COLOR_HEADER_BG)
    draw_text(
        canvas, 'MARS WEATHER DATA SUMMARY',
        x=20, y=14, color=COLOR_HEADER_TEXT, scale=2
    )

    # ── 외곽 테두리 ─────────────────────────────────────────────
    draw_rect_outline(canvas, 0, 0, w, h, COLOR_BORDER, thickness=2)

    # ── 좌측 텍스트 패널 ────────────────────────────────────────
    panel_x = 30
    line_h = 36
    text_scale = 2

    draw_rect(canvas, 20, 60, 370, 320, (235, 240, 255))
    draw_rect_outline(canvas, 20, 60, 370, 320, COLOR_BORDER)

    rows = [
        ('TOTAL', f'{summary["total"]} RECORDS'),
        ('FROM ', summary['date_start'][:10]),
        ('TO   ', summary['date_end'][:10]),
        ('AVG T', f'{summary["temp_avg"]:.1f} C'),
        ('MIN T', f'{summary["temp_min"]} C'),
        ('MAX T', f'{summary["temp_max"]} C'),
        ('STORM', f'{summary["storm_count"]} STORM DAYS'),
    ]

    for i, (label, value) in enumerate(rows):
        ty = 72 + i * line_h
        draw_text(canvas, label, panel_x, ty, COLOR_LABEL, text_scale)
        draw_text(canvas, ':', panel_x + 72, ty, COLOR_LABEL, text_scale)
        draw_text(canvas, value, panel_x + 90, ty, COLOR_VALUE, text_scale)

    # ── 우측 막대 차트 ───────────────────────────────────────────
    chart_x = 420
    chart_y = 70
    chart_w = 350
    chart_h = 290
    bar_area_h = 220  # 막대가 그려지는 최대 높이

    draw_rect(canvas, chart_x, chart_y, chart_w, chart_h, (235, 240, 255))
    draw_rect_outline(canvas, chart_x, chart_y, chart_w, chart_h, COLOR_BORDER)

    # 차트 제목
    draw_text(canvas, 'KEY STATS', chart_x + 90, chart_y + 6,
              COLOR_LABEL, scale=2)

    # 막대 데이터
    bars = [
        ('AVG', summary['temp_avg'], COLOR_BAR_TEMP_AVG),
        ('MIN', float(summary['temp_min']), COLOR_BAR_TEMP_MIN),
        ('MAX', float(summary['temp_max']), COLOR_BAR_TEMP_MAX),
        ('STM', float(summary['storm_count']), COLOR_BAR_STORM),
    ]

    max_val = max(v for _, v, _ in bars)
    bar_w = 54
    gap = 22
    base_y = chart_y + chart_h - 40   # 막대 바닥 y

    for i, (label, val, color) in enumerate(bars):
        bx = chart_x + gap + i * (bar_w + gap)
        bar_h_px = int(val / max_val * bar_area_h) if max_val > 0 else 1
        by = base_y - bar_h_px

        draw_bar(canvas, bx, by, bar_w, bar_h_px, color)

        # 값 표시 (막대 위)
        val_str = f'{val:.0f}'
        draw_text(canvas, val_str,
                  bx + 4, by - 18, COLOR_LABEL, scale=1)

        # 레이블 (막대 아래)
        draw_text(canvas, label,
                  bx + 14, base_y + 6, COLOR_LABEL, scale=1)

    # 축선
    draw_rect(canvas, chart_x + 10, chart_y + 28,
              1, chart_h - 66, COLOR_AXIS)
    draw_rect(canvas, chart_x + 10, base_y,
              chart_w - 20, 1, COLOR_AXIS)

    # ── PNG 저장 ────────────────────────────────────────────────
    png_data = encode_png(canvas)
    with open(out_path, 'wb') as f:
        f.write(png_data)

    print(f'[PNG] 저장 완료: {out_path} ({len(png_data) // 1024}KB)')


# ─────────────────────────────────────────────────────────────────
# 단독 실행 테스트
# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    sample = {
        'total': 1000,
        'date_start': '2050-01-01 00:00:00',
        'date_end': '2052-09-26 00:00:00',
        'temp_avg': 35.4,
        'temp_min': 21,
        'temp_max': 50,
        'storm_count': 312,
    }
    draw_summary_image(sample, 'mars_weather_summary.png')