# -*- coding: utf-8 -*-
"""
TCP/IP 소켓 통신 서버 (챗봇 기능 포함)
"""

import socket


# 챗봇 키워드 응답 사전
CHATBOT_RESPONSES = {
    '안녕': '안녕하세요! 저는 화성 통신 챗봇입니다.',
    '이름': '저는 화성 궤도 위성 통신 챗봇입니다.',
    '날씨': '화성의 날씨는 평균 -60도입니다. 방한복을 챙기세요!',
    '도움': '사용 가능한 키워드: 안녕, 이름, 날씨, 도움, quit(종료)',
    'hello': 'Hello! I am the Mars communication chatbot.',
}


def get_chatbot_response(message):
    """메시지에서 키워드를 찾아 챗봇 응답을 반환한다."""
    for keyword, response in CHATBOT_RESPONSES.items():
        if keyword in message:
            return response
    return message  # 키워드 없으면 에코


def bind_socket(server_socket, host):
    """소켓 바인드를 시도하고 실패 시 사용자에게 포트를 입력받는다."""
    port = 999

    while True:
        try:
            server_socket.bind((host, port))
            return port
        except PermissionError:
            print(f'포트 {port}번은 root 권한이 필요합니다.')
            print('  - 1024 미만 포트(예: 999)를 사용하려면 sudo로 실행하세요.')
            print('  - 포트 번호를 입력하거나 Enter를 누르면 기본 포트(9999)를 사용합니다.')
            user_input = input('포트 번호 입력: ').strip()
            port = int(user_input) if user_input.isdigit() else 9999
        except OSError as e:
            print(f'포트 {port}번 사용 불가: {e}')
            user_input = input('다른 포트 번호 입력 (Enter: 9999): ').strip()
            port = int(user_input) if user_input.isdigit() else 9999


def run_server():
    """TCP/IP 소켓 서버를 실행한다."""
    # 소켓 생성
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('소캣 생성완료')

    # 호스트 이름 가져오기 및 출력
    host = socket.gethostname()
    print(host)

    # 소켓 바인드 및 리슨
    port = bind_socket(server_socket, host)
    server_socket.listen(3)  # 커넥션 개수 3개 제한
    print(f'서버가 {host}:{port} 에서 대기 중입니다...')

    while True:
        client_socket, client_address = server_socket.accept()

        # 클라이언트 연결 메시지 출력 (서버)
        print('클라이언트와 연결 되었습니다.')

        # 클라이언트에게 연결 메시지 전송
        connect_msg = '클라이언트와 연결 되었습니다.'
        client_socket.send(connect_msg.encode('utf-8'))

        # 클라이언트 메시지 수신 및 에코/챗봇 응답
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = data.decode('utf-8')

            if message.lower() == 'quit':
                client_socket.send('quit'.encode('utf-8'))
                break

            response = get_chatbot_response(message)
            client_socket.send(response.encode('utf-8'))

        client_socket.close()
        print('클라이언트와의 연결이 종료되었습니다.')


if __name__ == '__main__':
    run_server()