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
#   'func' → 회색   (AC, +/-, %)
#   'op'   → 주황색 (÷, ×, −, +, =)
#   'num'  → 어두운 회색 (숫자, .)
# ──────────────────────────────────────────────
BUTTON_LAYOUT = [
    [('AC', 'func'), ('+/-', 'func'), ('%', 'func'), ('÷', 'op')],
    [('7', 'num'), ('8', 'num'), ('9', 'num'), ('×', 'op')],
    [('4', 'num'), ('5', 'num'), ('6', 'num'), ('−', 'op')],
    [('1', 'num'), ('2', 'num'), ('3', 'num'), ('+', 'op')],
    [('0', 'num'), ('.', 'num'), ('=', 'op')],
]

# 버튼 종류별 색상 (배경색, 글자색, 호버/눌림색)
COLORS = {
    'func': ('#a5a5a5', '#000000', '#c0c0c0'),
    'op': ('#ff9f0a', '#ffffff', '#ffb340'),
    'num': ('#333333', '#ffffff', '#4d4d4d'),
}

# 표시용 연산자 → Python 연산자 변환 (계산 시 사용)
OP_MAP = {
    '÷': '/',
    '×': '*',
    '−': '-',
    '+': '+',
}


class Calculator(QWidget):
    """
    아이폰 스타일 계산기.
    버튼을 누를 때마다 수식 문자열에 그대로 추가하고,
    = 를 눌렀을 때만 계산 결과를 표시합니다.
    """

    def __init__(self):
        """상태 변수 초기화 및 UI 구성."""
        super().__init__()

        # 화면에 보이는 수식 문자열 (예: '2+3÷9')
        # 숫자와 연산자를 그냥 이어붙여서 관리합니다.
        self._expression = '0'

        # = 를 눌러 결과가 나온 직후인지 나타내는 플래그.
        # True 상태에서 숫자를 누르면 새 수식을 시작합니다.
        self._just_result = False

        self._init_ui()

    # ──────────────────────────────────────────
    # UI 초기화
    # ──────────────────────────────────────────

    def _init_ui(self):
        """윈도우 설정, 디스플레이 라벨, 버튼 그리드를 구성합니다."""
        self.setWindowTitle('계산기')
        self.setFixedSize(320, 520)
        self.setStyleSheet('background-color: #000000;')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._label = self._make_display()
        main_layout.addWidget(self._label)
        main_layout.addLayout(self._make_grid())

    def _make_display(self):
        """
        수식을 표시하는 상단 라벨을 생성합니다.
        오른쪽 아래 정렬, 흰색 큰 폰트.
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
    # 버튼 이벤트 처리
    # ──────────────────────────────────────────

    def _on_button_clicked(self, text):
        """
        클릭된 버튼에 따라 처리를 분기합니다.

        Args:
            text (str): 클릭된 버튼 텍스트
        """
        if text == 'AC':
            self._reset()
        elif text == '+/-':
            self._toggle_sign()
        elif text == '%':
            self._percent()
        elif text == '=':
            self._calculate()
        elif text in OP_MAP:
            self._append_operator(text)
        else:
            # 숫자 또는 소수점
            self._append_digit(text)

    def _reset(self):
        """AC: 수식을 초기화하고 화면을 '0' 으로 되돌립니다."""
        self._expression = '0'
        self._just_result = False
        self._update_display()

    def _toggle_sign(self):
        """
        +/-: 수식의 마지막 숫자 부분의 부호를 반전합니다.
        예) '12' → '-12',  '3+5' → '3+-5'
        """
        # 수식 끝의 숫자 토큰만 추출해서 부호 반전
        last = self._last_number_str()
        if last and last != '0':
            if last.startswith('-'):
                new_last = last[1:]
            else:
                new_last = '-' + last
            # 수식에서 마지막 숫자 부분을 교체
            self._expression = self._expression[:-len(last)] + new_last
            self._update_display()

    def _percent(self):
        """
        %: 수식의 마지막 숫자를 100으로 나눕니다.
        예) '50' → '0.5',  '3+50' → '3+0.5'
        """
        last = self._last_number_str()
        if last:
            try:
                value = float(last) / 100
                new_last = self._format_number(value)
                self._expression = self._expression[:-len(last)] + new_last
                self._update_display()
            except ValueError:
                pass

    def _append_digit(self, digit):
        """
        숫자(0~9) 또는 소수점(.)을 수식 문자열 끝에 추가합니다.

        Args:
            digit (str): 입력된 문자
        """
        # = 직후 숫자를 누르면 새 수식 시작
        if self._just_result:
            self._expression = ''
            self._just_result = False

        if digit == '.':
            last = self._last_number_str()
            # 마지막 숫자에 이미 소수점이 있으면 무시
            if '.' not in last:
                # 수식이 비거나 연산자로 끝나면 '0.' 으로 시작
                if not last:
                    self._expression += '0.'
                else:
                    self._expression += '.'
        else:
            last = self._last_number_str()
            if last == '0':
                # '0' 하나만 있을 때 숫자를 누르면 대체
                self._expression = self._expression[:-1] + digit
            elif len(last.replace('-', '').replace('.', '')) >= 9:
                # 최대 9자리 제한
                pass
            else:
                if self._expression == '0':
                    # 초기 상태의 '0' 을 대체
                    self._expression = digit
                else:
                    self._expression += digit

        self._update_display()

    def _append_operator(self, op_text):
        """
        연산자(÷ × − +)를 수식 문자열 끝에 추가합니다.
        수식이 이미 연산자로 끝나면 마지막 연산자를 교체합니다.

        Args:
            op_text (str): 버튼에 표시된 연산자 기호 ('÷', '×', '−', '+')
        """
        # = 직후 연산자를 누르면 결과에 이어서 수식 작성
        self._just_result = False

        # 수식이 연산자로 끝나면 마지막 연산자를 새 연산자로 교체
        if self._expression and self._expression[-1] in OP_MAP:
            self._expression = self._expression[:-1] + op_text
        else:
            self._expression += op_text

        self._update_display()

    def _calculate(self):
        """
        = 버튼: 현재 수식 문자열을 계산해 결과를 화면에 표시합니다.

        표시용 기호(÷ × −)를 Python 연산자(/ * -)로 치환한 뒤
        eval() 없이 직접 토큰을 파싱해 안전하게 계산합니다.
        """
        try:
            result = self._eval_expression(self._expression)
            self._expression = self._format_number(result)
            self._just_result = True
        except Exception:
            self._expression = 'Error'
            self._just_result = True

        self._update_display()

    # ──────────────────────────────────────────
    # 수식 계산 (eval 미사용, 직접 파싱)
    # ──────────────────────────────────────────

    def _eval_expression(self, expr):
        """
        수식 문자열을 직접 파싱해 4칙 연산을 계산합니다.
        eval() 을 사용하지 않고 토큰 분리 → 곱셈·나눗셈 먼저 → 덧셈·뺄셈 순으로 처리합니다.
        (예: '2+3×4' → 2 + (3×4) = 14)

        Args:
            expr (str): 표시용 수식 문자열 (예: '2+3÷9')

        Returns:
            float: 계산 결과

        Raises:
            ValueError: 파싱 실패
            ZeroDivisionError: 0으로 나누기
        """
        # 표시용 기호 → Python 연산자로 변환
        expr = expr.replace('÷', '/').replace('×', '*').replace('−', '-')

        # 수식을 숫자와 연산자 토큰으로 분리
        # 예: '2+3/-9' → ['2', '+', '3', '/', '-9']
        tokens = self._tokenize(expr)
        if not tokens:
            raise ValueError('빈 수식')

        # 숫자 토큰 리스트와 연산자 리스트로 분리
        numbers = [float(tokens[i]) for i in range(0, len(tokens), 2)]
        operators = [tokens[i] for i in range(1, len(tokens), 2)]

        # 1단계: 곱셈과 나눗셈 먼저 처리 (연산자 우선순위)
        i = 0
        while i < len(operators):
            if operators[i] in ('*', '/'):
                if operators[i] == '/' and numbers[i + 1] == 0:
                    raise ZeroDivisionError('0으로 나누기')
                if operators[i] == '*':
                    result = numbers[i] * numbers[i + 1]
                else:
                    result = numbers[i] / numbers[i + 1]
                numbers[i] = result
                numbers.pop(i + 1)
                operators.pop(i)
            else:
                i += 1

        # 2단계: 남은 덧셈·뺄셈 처리 (왼쪽에서 오른쪽)
        result = numbers[0]
        for i, op in enumerate(operators):
            if op == '+':
                result += numbers[i + 1]
            elif op == '-':
                result -= numbers[i + 1]

        return result

    def _tokenize(self, expr):
        """
        수식 문자열을 숫자와 연산자 토큰 리스트로 분리합니다.
        음수 처리를 위해 수식 앞이나 연산자 직후의 '-' 는 숫자에 포함합니다.

        Args:
            expr (str): Python 연산자로 치환된 수식 문자열

        Returns:
            list[str]: 토큰 리스트 (예: ['2', '+', '-3', '/', '9'])
        """
        tokens = []
        current = ''
        ops = set('+-*/')

        for i, ch in enumerate(expr):
            if ch in ops:
                # '-' 가 맨 앞이거나 직전 토큰이 연산자이면 음수 부호로 처리
                if ch == '-' and (not tokens and not current
                                  or tokens and not current):
                    current += ch
                else:
                    if current:
                        tokens.append(current)
                        current = ''
                    tokens.append(ch)
            else:
                current += ch

        if current:
            tokens.append(current)

        return tokens

    # ──────────────────────────────────────────
    # 내부 유틸리티
    # ──────────────────────────────────────────

    def _last_number_str(self):
        """
        수식 문자열(_expression)에서 마지막 숫자 부분을 문자열로 반환합니다.
        +/- 와 % 처리에서 마지막 숫자만 수정할 때 사용합니다.

        예) '3+52'  → '52'
            '10÷-3' → '-3'
            '÷'     → ''

        Returns:
            str: 마지막 숫자 문자열 (없으면 빈 문자열)
        """
        # 뒤에서부터 숫자·소수점·부호 문자를 읽어 숫자 토큰을 추출
        result = ''
        for ch in reversed(self._expression):
            if ch.isdigit() or ch == '.':
                result = ch + result
            elif ch == '-' and not result:
                # 부호 '-' 는 앞에 연산자가 있을 때만 숫자의 일부
                result = '-'
                break
            else:
                break
        return result

    def _format_number(self, value):
        """
        float 를 화면 표시용 문자열로 변환합니다.
        - 정수이면 소수점 없이 (예: 3.0 → '3')
        - 소수이면 뒤쪽 불필요한 0 제거 (예: 3.500 → '3.5')

        Args:
            value (float): 변환할 숫자

        Returns:
            str: 표시용 문자열
        """
        if value != value:  # NaN 체크
            return 'Error'
        if value == int(value) and abs(value) < 1e10:
            return str(int(value))
        return f'{value:.8f}'.rstrip('0').rstrip('.')

    def _update_display(self):
        """
        _expression 을 라벨에 반영합니다.
        문자열 길이에 따라 폰트 크기를 자동으로 줄입니다.
        """
        text = self._expression
        length = len(text)

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
    """QApplication 생성 후 계산기 창을 띄우고 이벤트 루프를 시작합니다."""
    app = QApplication(sys.argv)
    window = Calculator()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
