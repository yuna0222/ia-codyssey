import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QGridLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


# ──────────────────────────────────────────────
# 버튼 정의
# 각 튜플: (표시 텍스트, 버튼 종류)
#   종류: 'func'  → 회색  (AC, +/-, %)
#         'op'    → 주황색 (÷, ×, −, +, =)
#         'num'   → 어두운 회색 (숫자, .)
# ──────────────────────────────────────────────
BUTTON_LAYOUT = [
    [('AC', 'func'),  ('+/-', 'func'), ('%', 'func'),  ('÷', 'op')],
    [('7',  'num'),   ('8',   'num'),  ('9',  'num'),  ('×', 'op')],
    [('4',  'num'),   ('5',   'num'),  ('6',  'num'),  ('−', 'op')],
    [('1',  'num'),   ('2',   'num'),  ('3',  'num'),  ('+', 'op')],
    [('0',  'num'),   ('.',   'num'),  ('=',  'op')],   # 0 버튼은 넓게 처리
]

# 버튼 종류별 색상 (배경색, 글자색, 호버색)
COLORS = {
    'func': ('#a5a5a5', '#000000', '#c0c0c0'),
    'op':   ('#ff9f0a', '#ffffff', '#ffb340'),
    'num':  ('#333333', '#ffffff', '#4d4d4d'),
}

# 실제 연산에 쓸 기호 매핑 (표시용 → Python 연산자)
OP_MAP = {
    '÷': '/',
    '×': '*',
    '−': '-',
    '+': '+',
}


class Calculator(QWidget):
    """
    아이폰 스타일 계산기 메인 윈도우.
    PyQt5 의 QWidget 을 상속받아 UI 와 계산 로직을 함께 담당합니다.
    """

    def __init__(self):
        """윈도우 초기화 및 UI 구성."""
        super().__init__()

        # ── 계산기 내부 상태 변수 ──────────────────
        self._display_text = '0'    # 화면에 표시되는 문자열
        self._operand1 = None       # 첫 번째 피연산자 (숫자)
        self._operator = None       # 현재 선택된 연산자 문자열 (+, -, *, /)
        self._new_number = True     # True 이면 다음 숫자 입력 시 화면을 초기화

        self._init_ui()

    # ──────────────────────────────────────────
    # UI 초기화
    # ──────────────────────────────────────────

    def _init_ui(self):
        """윈도우 크기·제목·배경색·레이아웃을 설정하고 버튼을 생성합니다."""
        self.setWindowTitle('계산기')
        self.setFixedSize(320, 520)

        # 전체 배경을 검정으로 설정
        self.setStyleSheet('background-color: #000000;')

        # 수직 레이아웃: 상단 디스플레이 + 하단 버튼 그리드
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # 디스플레이 라벨 생성
        self._label = self._make_display()
        main_layout.addWidget(self._label)

        # 버튼 그리드 생성
        grid = self._make_grid()
        main_layout.addLayout(grid)

    def _make_display(self):
        """
        숫자가 표시되는 상단 라벨을 만들어 반환합니다.
        아이폰 계산기처럼 오른쪽 정렬, 큰 흰색 폰트입니다.
        """
        label = QLabel('0')
        label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        label.setFont(QFont('Arial', 52, 25))
        label.setStyleSheet('color: #ffffff; padding: 10px 12px;')
        label.setFixedHeight(130)
        return label

    def _make_grid(self):
        """
        버튼 배열(BUTTON_LAYOUT)을 읽어 QGridLayout 을 구성해 반환합니다.
        0 버튼은 열 2칸을 차지합니다(아이폰 스타일).
        """
        grid = QGridLayout()
        grid.setSpacing(8)

        for row_idx, row in enumerate(BUTTON_LAYOUT):
            col_idx = 0
            for text, kind in row:
                btn = self._make_button(text, kind)

                # '0' 버튼은 가로로 2칸 차지
                if text == '0':
                    grid.addWidget(btn, row_idx, col_idx, 1, 2)
                    col_idx += 2
                else:
                    grid.addWidget(btn, row_idx, col_idx, 1, 1)
                    col_idx += 1

        return grid

    def _make_button(self, text, kind):
        """
        버튼 하나를 생성하고 스타일 및 클릭 이벤트를 연결합니다.

        Args:
            text (str): 버튼에 표시할 텍스트
            kind (str): 버튼 종류 ('func' | 'op' | 'num')

        Returns:
            QPushButton: 스타일이 적용된 버튼
        """
        bg, fg, hover = COLORS[kind]

        btn = QPushButton(text)
        btn.setFixedHeight(65)
        btn.setFont(QFont('Arial', 22, 50))
        btn.setCursor(Qt.PointingHandCursor)

        # 둥근 원형 버튼 (border-radius 를 높이의 절반으로 설정)
        # 버튼이 눌렸을 때 배경색을 밝게 해 눌림 효과 표현
        btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border-radius: 32px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {hover};
            }}
        ''')

        # 버튼 클릭 시 on_button_clicked 호출 (lambda 로 text 캡처)
        btn.clicked.connect(lambda _, t=text: self._on_button_clicked(t))
        return btn

    # ──────────────────────────────────────────
    # 이벤트 처리
    # ──────────────────────────────────────────

    def _on_button_clicked(self, text):
        """
        버튼이 눌렸을 때 호출되는 중앙 디스패처.
        버튼 텍스트에 따라 적절한 처리 함수로 분기합니다.

        Args:
            text (str): 클릭된 버튼의 텍스트
        """
        if text == 'AC':
            self._reset()
        elif text == '+/-':
            self._toggle_sign()
        elif text == '%':
            self._percent()
        elif text in OP_MAP:
            self._set_operator(text)
        elif text == '=':
            self._calculate()
        else:
            # 숫자 또는 소수점
            self._input_digit(text)

    def _reset(self):
        """
        AC 버튼: 모든 상태를 초기화하고 화면을 '0'으로 되돌립니다.
        """
        self._display_text = '0'
        self._operand1 = None
        self._operator = None
        self._new_number = True
        self._update_display()

    def _toggle_sign(self):
        """
        +/- 버튼: 현재 표시 숫자의 부호를 반전합니다.
        예) 5 → -5, -3.2 → 3.2
        """
        if self._display_text not in ('0', ''):
            if self._display_text.startswith('-'):
                # 이미 음수이면 '-' 제거
                self._display_text = self._display_text[1:]
            else:
                # 양수이면 '-' 추가
                self._display_text = '-' + self._display_text
            self._update_display()

    def _percent(self):
        """
        % 버튼: 현재 표시 숫자를 100으로 나눕니다.
        예) 50 → 0.5
        """
        try:
            value = float(self._display_text) / 100
            # 불필요한 소수점 제거 (예: 0.50 → 0.5, 1.0 → 1)
            self._display_text = self._format_number(value)
            self._update_display()
        except ValueError:
            pass

    def _input_digit(self, digit):
        """
        숫자 또는 소수점 버튼: 현재 화면에 입력값을 추가합니다.

        Args:
            digit (str): 입력된 문자 ('0'~'9' 또는 '.')
        """
        # 연산자를 눌렀거나 방금 계산을 완료한 경우 → 새 숫자 입력 시작
        if self._new_number:
            self._display_text = '0'
            self._new_number = False

        if digit == '.':
            # 이미 소수점이 있으면 추가하지 않음
            if '.' not in self._display_text:
                self._display_text += '.'
        else:
            if self._display_text == '0':
                # 화면이 '0'일 때 숫자를 누르면 대체
                self._display_text = digit
            else:
                # 최대 9자리까지만 입력 허용
                if len(self._display_text.replace('-', '').replace('.', '')) < 9:
                    self._display_text += digit

        self._update_display()

    def _set_operator(self, op_text):
        """
        연산자 버튼(+, −, ×, ÷): 현재 숫자를 첫 번째 피연산자로 저장하고
        연산자를 기억합니다. 연산자를 연속으로 누르면 마지막 것으로 덮어씁니다.

        Args:
            op_text (str): 버튼 텍스트 ('÷', '×', '−', '+')
        """
        try:
            # 이미 첫 번째 피연산자와 연산자가 있는 상태에서
            # 새 연산자를 누르면 중간 계산 먼저 수행
            if self._operand1 is not None and not self._new_number:
                self._calculate()

            self._operand1 = float(self._display_text)
            self._operator = OP_MAP[op_text]  # '×' → '*' 등으로 변환
            self._new_number = True           # 다음 숫자 입력 시 화면 초기화
        except ValueError:
            pass

    def _calculate(self):
        """
        = 버튼: 저장된 피연산자와 현재 화면 숫자로 4칙 연산을 수행합니다.
        0으로 나누기 시도 시 'Error' 를 표시합니다.
        """
        # 연산자나 첫 번째 피연산자가 없으면 아무것도 하지 않음
        if self._operator is None or self._operand1 is None:
            return

        try:
            operand2 = float(self._display_text)

            # 0으로 나누기 예외 처리
            if self._operator == '/' and operand2 == 0:
                self._display_text = 'Error'
                self._reset_state()
                self._update_display()
                return

            # 실제 계산 수행 (eval 대신 명시적 분기로 안전하게 처리)
            if self._operator == '+':
                result = self._operand1 + operand2
            elif self._operator == '-':
                result = self._operand1 - operand2
            elif self._operator == '*':
                result = self._operand1 * operand2
            elif self._operator == '/':
                result = self._operand1 / operand2
            else:
                return

            self._display_text = self._format_number(result)
            self._reset_state()   # 연산 완료 후 상태 초기화
            self._new_number = True
            self._update_display()

        except (ValueError, ZeroDivisionError):
            self._display_text = 'Error'
            self._reset_state()
            self._update_display()

    # ──────────────────────────────────────────
    # 내부 유틸리티
    # ──────────────────────────────────────────

    def _reset_state(self):
        """
        피연산자와 연산자 상태만 초기화합니다.
        디스플레이 텍스트는 건드리지 않습니다.
        """
        self._operand1 = None
        self._operator = None

    def _format_number(self, value):
        """
        숫자를 화면에 표시할 문자열로 변환합니다.
        - 정수이면 소수점 없이 표시 (예: 3.0 → '3')
        - 소수이면 불필요한 0 제거 (예: 3.500 → '3.5')
        - 매우 크거나 작은 수는 지수 표기법 사용

        Args:
            value (float): 변환할 숫자

        Returns:
            str: 표시용 문자열
        """
        if value != value:  # NaN 체크
            return 'Error'

        # 정수 여부 확인
        if value == int(value) and abs(value) < 1e10:
            return str(int(value))

        # 소수점 포함 시 최대 8자리, 불필요한 뒤쪽 0 제거
        formatted = f'{value:.8f}'.rstrip('0').rstrip('.')
        return formatted

    def _update_display(self):
        """
        내부 상태 변수 _display_text 를 화면 라벨에 반영합니다.
        텍스트 길이에 따라 폰트 크기를 자동으로 조절합니다.
        """
        text = self._display_text
        length = len(text)

        # 글자 수에 따라 폰트 크기 조절 (긴 숫자일수록 작게)
        if length <= 6:
            font_size = 52
        elif length <= 9:
            font_size = 40
        else:
            font_size = 28

        self._label.setFont(QFont('Arial', font_size, 25))
        self._label.setText(text)


# ──────────────────────────────────────────────
# 진입점
# ──────────────────────────────────────────────

def main():
    """
    프로그램 진입점.
    QApplication 을 생성하고 계산기 윈도우를 띄운 뒤 이벤트 루프를 시작합니다.
    """
    app = QApplication(sys.argv)

    window = Calculator()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()