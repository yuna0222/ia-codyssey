import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QGridLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


# ──────────────────────────────────────────────
# 버튼 배치 정의
# 각 튜플: (표시 텍스트, 버튼 종류)
#   'func' → 회색  (AC, +/-, %)
#   'op'   → 주황색 (÷, ×, −, +, =)
#   'num'  → 어두운 회색 (숫자, .)
# ──────────────────────────────────────────────
BUTTON_LAYOUT = [
    [('AC', 'func'),  ('+/-', 'func'), ('%', 'func'),  ('÷', 'op')],
    [('7',  'num'),   ('8',   'num'),  ('9',  'num'),  ('×', 'op')],
    [('4',  'num'),   ('5',   'num'),  ('6',  'num'),  ('−', 'op')],
    [('1',  'num'),   ('2',   'num'),  ('3',  'num'),  ('+', 'op')],
    [('0',  'num'),   ('.',   'num'),  ('=',  'op')],
]

# 버튼 종류별 색상 (배경색, 글자색, 호버/눌림색)
COLORS = {
    'func': ('#a5a5a5', '#000000', '#c0c0c0'),
    'op':   ('#ff9f0a', '#ffffff', '#ffb340'),
    'num':  ('#333333', '#ffffff', '#4d4d4d'),
}

# 표시용 연산자 → Python 연산자 변환 테이블
OP_MAP = {
    '÷': '/',
    '×': '*',
    '−': '-',
    '+': '+',
}

# Python 연산자 → 표시용 연산자 역변환 (수식 재구성에 사용)
OP_DISPLAY = {v: k for k, v in OP_MAP.items()}


class Calculator(QWidget):
    """
    아이폰 스타일 계산기.
    디스플레이에 '2+3÷9' 처럼 입력 수식 전체를 보여줍니다.
    """

    def __init__(self):
        """상태 변수 초기화 및 UI 구성."""
        super().__init__()

        # ── 내부 상태 변수 ─────────────────────────
        # _operand1   : 첫 번째 피연산자 (float)
        # _operator   : 현재 연산자 ('/', '*', '-', '+')
        # _operand2   : 두 번째 피연산자 입력 중인 문자열
        # _just_result: True 이면 방금 = 를 눌러 결과가 나온 상태
        self._operand1 = None
        self._operator = None
        self._operand2 = '0'
        self._just_result = False

        self._init_ui()

    # ──────────────────────────────────────────
    # UI 초기화
    # ──────────────────────────────────────────

    def _init_ui(self):
        """윈도우 기본 설정, 레이아웃, 디스플레이, 버튼 그리드를 구성합니다."""
        self.setWindowTitle('계산기')
        self.setFixedSize(320, 520)
        self.setStyleSheet('background-color: #000000;')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # 수식 전체를 보여주는 디스플레이 라벨
        self._label = self._make_display()
        main_layout.addWidget(self._label)

        main_layout.addLayout(self._make_grid())

    def _make_display(self):
        """
        수식 표시 라벨을 생성합니다.
        오른쪽 아래 정렬, 흰색 큰 폰트로 '2+3÷9' 같은 형태를 보여줍니다.
        """
        label = QLabel('0')
        label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        label.setFont(QFont('Arial', 48, 25))
        label.setStyleSheet('color: #ffffff; padding: 10px 12px;')
        label.setFixedHeight(130)
        return label

    def _make_grid(self):
        """버튼 배열을 QGridLayout 으로 구성합니다. 0 버튼은 2칸 너비."""
        grid = QGridLayout()
        grid.setSpacing(8)

        for row_idx, row in enumerate(BUTTON_LAYOUT):
            col_idx = 0
            for text, kind in row:
                btn = self._make_button(text, kind)
                if text == '0':
                    grid.addWidget(btn, row_idx, col_idx, 1, 2)
                    col_idx += 2
                else:
                    grid.addWidget(btn, row_idx, col_idx, 1, 1)
                    col_idx += 1

        return grid

    def _make_button(self, text, kind):
        """
        버튼을 생성하고 스타일과 클릭 이벤트를 연결합니다.

        Args:
            text (str): 버튼에 표시할 텍스트
            kind (str): 버튼 종류 ('func' | 'op' | 'num')
        """
        bg, fg, hover = COLORS[kind]

        btn = QPushButton(text)
        btn.setFixedHeight(65)
        btn.setFont(QFont('Arial', 22, 50))
        btn.setCursor(Qt.PointingHandCursor)

        # 둥근 원형 버튼, 호버/눌림 시 배경색 변경
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

        btn.clicked.connect(lambda _, t=text: self._on_button_clicked(t))
        return btn

    # ──────────────────────────────────────────
    # 디스플레이 수식 조합
    # ──────────────────────────────────────────

    def _build_expression(self):
        """
        현재 상태 변수를 조합해 디스플레이에 표시할 수식 문자열을 만듭니다.

        예)
          operand1=2, operator='+', operand2='3'  → '2+3'
          operand1=None, operand2='0'             → '0'

        Returns:
            str: 화면에 표시할 수식 문자열
        """
        if self._operand1 is None:
            # 아직 연산자를 누르지 않은 상태 → 두 번째 입력란만 표시
            return self._operand2

        # operand1 을 정수처럼 표시할 수 있으면 소수점 없이 보여줌
        op1_str = self._format_number(self._operand1)
        # 연산자를 표시용 기호로 변환 (예: '/' → '÷')
        op_symbol = OP_DISPLAY.get(self._operator, self._operator)

        if self._just_result:
            # = 를 눌러 결과가 나온 직후 → 결과값만 표시
            return self._operand2

        return f'{op1_str}{op_symbol}{self._operand2}'

    # ──────────────────────────────────────────
    # 버튼 이벤트 처리
    # ──────────────────────────────────────────

    def _on_button_clicked(self, text):
        """
        클릭된 버튼 텍스트에 따라 적절한 처리 함수로 분기합니다.

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
            self._input_digit(text)

    def _reset(self):
        """AC: 모든 상태를 초기화하고 화면을 '0' 으로 되돌립니다."""
        self._operand1 = None
        self._operator = None
        self._operand2 = '0'
        self._just_result = False
        self._update_display()

    def _toggle_sign(self):
        """
        +/- : 현재 입력 중인 숫자(_operand2)의 부호를 반전합니다.
        예) '5' → '-5',  '-3.2' → '3.2'
        """
        if self._operand2 not in ('0', ''):
            if self._operand2.startswith('-'):
                self._operand2 = self._operand2[1:]
            else:
                self._operand2 = '-' + self._operand2
            self._update_display()

    def _percent(self):
        """
        % : 현재 입력 중인 숫자를 100으로 나눕니다.
        예) '50' → '0.5'
        """
        try:
            value = float(self._operand2) / 100
            self._operand2 = self._format_number(value)
            self._update_display()
        except ValueError:
            pass

    def _input_digit(self, digit):
        """
        숫자(0~9) 또는 소수점(.) 입력을 처리합니다.
        = 를 누른 직후라면 새 계산을 시작합니다.

        Args:
            digit (str): 입력된 문자
        """
        # = 직후 숫자를 누르면 새 계산 시작 (이전 결과 초기화)
        if self._just_result:
            self._operand1 = None
            self._operator = None
            self._operand2 = '0'
            self._just_result = False

        if digit == '.':
            # 소수점 중복 방지
            if '.' not in self._operand2:
                self._operand2 += '.'
        else:
            if self._operand2 == '0':
                self._operand2 = digit
            elif self._operand2 == '-0':
                self._operand2 = '-' + digit
            else:
                # 최대 9자리 입력 허용 (부호·소수점 제외)
                digits_only = self._operand2.replace('-', '').replace('.', '')
                if len(digits_only) < 9:
                    self._operand2 += digit

        self._update_display()

    def _set_operator(self, op_text):
        """
        연산자(÷ × − +) 버튼 처리.
        - 이미 수식이 완성된 상태라면 먼저 계산하고 연산자를 이어붙입니다.
        - 이미지처럼 '2+3÷9' 형태로 수식이 화면에 쌓입니다.

        Args:
            op_text (str): 버튼에 표시된 연산자 기호
        """
        try:
            if self._operand1 is not None and not self._just_result:
                # 앞에 이미 수식이 있으면 중간 계산 먼저 수행
                self._calculate(keep_chain=True)

            self._operand1 = float(self._operand2)
            self._operator = OP_MAP[op_text]   # 표시용 → Python 연산자
            self._operand2 = '0'               # 두 번째 피연산자 입력 대기
            self._just_result = False
        except ValueError:
            pass

        self._update_display()

    def _calculate(self, keep_chain=False):
        """
        = 버튼 또는 연산자 연속 입력 시 4칙 연산을 수행합니다.

        Args:
            keep_chain (bool):
                True  → 연산자를 연속으로 눌렀을 때의 중간 계산.
                         결과를 _operand1 에 저장하고 수식을 이어갑니다.
                False → = 버튼. 결과를 화면에 표시하고 수식을 종료합니다.
        """
        if self._operator is None or self._operand1 is None:
            return

        try:
            operand2 = float(self._operand2)

            # 0 나누기 처리
            if self._operator == '/' and operand2 == 0:
                self._operand2 = 'Error'
                self._operand1 = None
                self._operator = None
                self._just_result = True
                self._update_display()
                return

            # 4칙 연산 수행
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

            result_str = self._format_number(result)

            if keep_chain:
                # 중간 계산: 결과를 다음 연산의 첫 번째 피연산자로 사용
                self._operand1 = result
                self._operand2 = result_str
            else:
                # = 최종 계산: 결과만 화면에 표시
                self._operand1 = None
                self._operator = None
                self._operand2 = result_str
                self._just_result = True

        except (ValueError, ZeroDivisionError):
            self._operand2 = 'Error'
            self._operand1 = None
            self._operator = None
            self._just_result = True

        self._update_display()

    # ──────────────────────────────────────────
    # 내부 유틸리티
    # ──────────────────────────────────────────

    def _format_number(self, value):
        """
        float 를 표시용 문자열로 변환합니다.
        - 정수이면 소수점 없이 표시 (예: 3.0 → '3')
        - 소수이면 뒤쪽 불필요한 0 제거 (예: 3.500 → '3.5')

        Args:
            value (float): 변환할 숫자

        Returns:
            str: 표시용 문자열
        """
        if value != value:      # NaN 체크
            return 'Error'

        if value == int(value) and abs(value) < 1e10:
            return str(int(value))

        return f'{value:.8f}'.rstrip('0').rstrip('.')

    def _update_display(self):
        """
        _build_expression() 으로 현재 수식을 만들어 라벨에 반영합니다.
        수식 길이에 따라 폰트를 자동으로 줄여 잘리지 않게 합니다.
        """
        text = self._build_expression()
        length = len(text)

        # 글자 수에 따라 폰트 크기 단계적 축소
        if length <= 6:
            font_size = 48
        elif length <= 10:
            font_size = 36
        elif length <= 14:
            font_size = 26
        else:
            font_size = 20

        self._label.setFont(QFont('Arial', font_size, 25))
        self._label.setText(text)


# ──────────────────────────────────────────────
# 진입점
# ──────────────────────────────────────────────

def main():
    """
    QApplication 을 생성하고 계산기 창을 띄운 뒤 이벤트 루프를 시작합니다.
    """
    app = QApplication(sys.argv)
    window = Calculator()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()