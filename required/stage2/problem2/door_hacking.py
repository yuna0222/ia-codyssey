"""
caesar_cipher.py - 카이사르 암호 해독기
password.txt 를 읽어서 26가지 자리수로 해독 결과를 출력하고,
눈으로 확인 후 번호를 입력하면 result.txt 로 저장한다.
"""

# 텍스트 사전 — 이 단어가 해독 결과에 포함되면 멈출지 여부를 묻는다 (보너스 과제)
DICTIONARY = [
    'the', 'is', 'are', 'was', 'have', 'has',
    'password', 'open', 'door', 'storage', 'emergency',
    'mars', 'base', 'key', 'access', 'code',
]

PASSWORD_FILE = 'decode/password.txt'
RESULT_FILE = 'result.txt'


def read_password(filepath=PASSWORD_FILE):
    """password.txt 파일을 읽어서 반환한다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없습니다: {filepath}')
        return None
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')
        return None


def save_result(text, shift, filepath=RESULT_FILE):
    """해독된 결과를 result.txt 에 저장한다."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'[자리수] {shift}\n')
            f.write(f'[결과] {text}\n')
        print(f'[저장] {filepath} 저장 완료')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def decode_shift(text, shift):
    """
    주어진 문자열을 shift 자리수만큼 뒤로 밀어서 해독한다.
    알파벳만 변환하고 나머지 문자는 그대로 유지한다.
    """
    result = ''

    for ch in text:
        if ch.isalpha():
            base = 'A' if ch.isupper() else 'a'
            result += chr((ord(ch) - ord(base) - shift) % 26 + ord(base))
        else:
            result += ch

    return result


def contains_dictionary_word(text):
    """해독 결과에 사전 단어가 포함되어 있으면 해당 단어를 반환한다. (보너스 과제)"""
    lower = text.lower()

    for word in DICTIONARY:
        if word in lower:
            return word

    return None


def caesar_cipher_decode(target_text):
    """
    카이사르 암호를 해독한다.
    알파벳 수(26)만큼 자리수를 바꿔가며 해독 결과를 출력한다.
    사전 단어가 발견되면 멈출지 여부를 사용자에게 묻는다. (보너스 과제)

    Args:
        target_text (str): 해독할 암호 문자열
    """
    print('=' * 50)
    print('  카이사르 암호 해독기')
    print('=' * 50)
    print(f'[원문] {target_text}')
    print('-' * 50)

    for shift in range(1, 26):
        decoded = decode_shift(target_text, shift)
        print(f'[자리수 {shift:2d}] {decoded}')

        # 사전 단어 발견 시 멈출지 여부를 묻는다 (보너스 과제)
        found_word = contains_dictionary_word(decoded)
        if found_word:
            print(f'\n[사전 감지] 자리수 {shift} — "{found_word}" 발견!')
            stop = input('반복을 멈추고 이 결과를 저장할까요? (y/n): ').strip().lower()
            if stop == 'y':
                save_result(decoded, shift)
                return

    print('-' * 50)

    # 눈으로 확인 후 번호 입력
    try:
        num = int(input('몇 번째 자리수가 정답인가요? (1~25): ').strip())
        if 1 <= num <= 25:
            decoded = decode_shift(target_text, num)
            print(f'[선택] 자리수 {num}: {decoded}')
            save_result(decoded, num)
        else:
            print('[오류] 1~25 사이의 숫자를 입력해 주세요.')
    except ValueError:
        print('[오류] 숫자를 입력해 주세요.')


def main():
    text = read_password()
    if text:
        caesar_cipher_decode(text)


if __name__ == '__main__':
    main()