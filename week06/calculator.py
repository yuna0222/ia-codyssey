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

# 처리 가능한 숫자 최대 범위
MAX_VALUE = 1e99


# ──────────────────────────────────────────────
# Calculator: 순수 계산 로직 클래스 (UI 없음)
# ──────────────────────────────────────────────

class Calculator:
    def __init__(self):
        self.reset()

    def reset(self):
        """AC: 수식을 초기화하고 '0' 으로 되돌립니다."""
        self._expression = '0'
        self._just_result = False

    def add(self):
        """덧셈 연산자를 수식에 추가합니다."""
        self._append_operator('+')

    def subtract(self):
        """뺄셈 연산자를 수식에 추가합니다."""
        self._append_operator('−')

    def multiply(self):
        """곱셈 연산자를 수식에 추가합니다."""
        self._append_operator('×')

    def divide(self):
        """나눗셈 연산자를 수식에 추가합니다."""
        self._append_operator('÷')

    def negative_positive(self):
        """
        +/-: 수식의 마지막 숫자 부분의 부호를 반전합니다.
        예) '12' → '-12',  '3+5' → '3+-5'
        """
        last = self._last_number_str()
        if last and last != '0':
            if last.startswith('-'):
                new_last = last[1:]
            else:
                new_last = '-' + last
            self._expression = self._expression[:-len(last)] + new_last

    def percent(self):
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
            except ValueError:
                self._expression = 'Error'

    def equal(self):
        """
        =: 현재 수식을 계산하고 결과를 저장합니다.
        0으로 나누거나 범위를 초과하면 오류 메시지를 표시합니다.
        """
        if self._expression[-1] in OP_MAP:
            return
        try:
            result = self._eval_expression(self._expression)

            if abs(result) > MAX_VALUE:
                self._expression = 'Error: 범위 초과'
                self._just_result = True
                return

            self._expression = self._format_number(result)
            self._just_result = True
        except ZeroDivisionError:
            self._expression = 'Error: 0으로 나누기'
            self._just_result = True
        except Exception:
            self._expression = 'Error'
            self._just_result = True

    def input_digit(self, digit):
        """
        숫자(0~9)를 수식 문자열 끝에 누적합니다.
        = 직후이거나 Error 상태이면 새 수식을 시작합니다.

        Args:
            digit (str): 입력된 숫자 문자
        """
        if self._just_result or self._expression.startswith('Error'):
            self._expression = ''
            self._just_result = False

        last = self._last_number_str()
        if last == '0':
            # '0' 하나만 있을 때 숫자를 누르면 대체
            self._expression = self._expression[:-1] + digit
        elif len(last.replace('-', '').replace('.', '')) >= 9:
            # 최대 9자리 제한
            pass
        else:
            if self._expression == '0':
                self._expression = digit
            else:
                self._expression += digit

    def input_decimal(self):
        """
        소수점(.)을 입력합니다.
        이미 소수점이 있으면 무시합니다.
        = 직후이거나 Error 상태이면 '0.' 으로 새 수식을 시작합니다.
        """
        if self._just_result or self._expression.startswith('Error'):
            self._expression = '0.'
            self._just_result = False
            return

        last = self._last_number_str()
        if '.' not in last:
            if not last:
                self._expression += '0.'
            else:
                self._expression += '.'

    def get_display(self):
        """현재 화면에 표시할 문자열을 반환합니다."""
        return self._expression

    # ── 내부 헬퍼 메소드 ──────────────────────────

    def _append_operator(self, op_text):
        """
        연산자(÷ × − +)를 수식 문자열 끝에 추가합니다.
        수식이 이미 연산자로 끝나면 마지막 연산자를 교체합니다.

        Args:
            op_text (str): 버튼에 표시된 연산자 기호 ('÷', '×', '−', '+')
        """

        if self._expression.startswith('Error'):
            self._expression = ''

        self._just_result = False

        if self._expression and self._expression[-1] in OP_MAP:
            self._expression = self._expression[:-1] + op_text
        else:
            self._expression += op_text

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
        expr = expr.replace('÷', '/').replace('×', '*').replace('−', '-')

        tokens = self._tokenize(expr)
        if not tokens:
            raise ValueError('빈 수식')

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
        수식 문자열을 숫자 토큰과 연산자 토큰으로 분리합니다.
        음수 부호(-)를 올바르게 처리합니다.
        예: '2+3/-9' → ['2', '+', '3', '/', '-9']
        """
        tokens = []
        current = ''
        ops = set('+-*/')

        for ch in expr:
            if ch in ops:
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
        result = ''
        for ch in reversed(self._expression):
            if ch.isdigit() or ch == '.':
                result = ch + result
            elif ch == '-' and not result:
                result = '-'
                break
            else:
                break
        return result

    def _format_number(self, value):
        """
        숫자를 화면 표시용 문자열로 변환합니다.
        소수점 6자리 이하로 반올림하고, 정수이면 정수로 표시합니다.
        """
        if value != value:  # NaN 체크
            return 'Error'
        # 소수점 6자리 반올림 (보너스 과제)
        rounded = round(value, 6)
        if rounded == int(rounded) and abs(rounded) < 1e15:
            return str(int(rounded))
        return str(rounded)


# ──────────────────────────────────────────────
# CalculatorApp: UI 담당 클래스
# Calculator 클래스를 내부에서 사용합니다.
# ──────────────────────────────────────────────

class CalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self._calc = Calculator()
        self._init_ui()

    def _init_ui(self):
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

    def _on_button_clicked(self, text):
        """클릭된 버튼에 따라 Calculator 클래스의 메소드를 호출합니다."""
        if text == 'AC':
            self._calc.reset()
        elif text == '+/-':
            self._calc.negative_positive()
        elif text == '%':
            self._calc.percent()
        elif text == '=':
            self._calc.equal()
        elif text == '÷':
            self._calc.divide()
        elif text == '×':
            self._calc.multiply()
        elif text == '−':
            self._calc.subtract()
        elif text == '+':
            self._calc.add()
        elif text == '.':
            self._calc.input_decimal()
        else:
            self._calc.input_digit(text)

        self._update_display()

    def _update_display(self):
        """Calculator 에서 표시 문자열을 받아 화면을 갱신합니다. 길이에 따라 폰트 크기 자동 조절."""
        text = self._calc.get_display()
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


def main():
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
