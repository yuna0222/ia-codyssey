# -*- coding: utf-8 -*-
"""
TCP/IP 멀티쓰레드 채팅 서버
"""

import socket
import threading


clients = {}  # {client_socket: nickname}
lock = threading.Lock()


def broadcast(message, sender_socket=None):
    """모든 클라이언트에게 메시지를 전송한다."""
    with lock:
        for client_socket in list(clients.keys()):
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except OSError:
                    remove_client(client_socket)


def send_to_client(client_socket, message):
    """특정 클라이언트에게 메시지를 전송한다."""
    try:
        client_socket.send(message.encode('utf-8'))
    except OSError:
        remove_client(client_socket)


def remove_client(client_socket):
    """클라이언트를 목록에서 제거한다."""
    with lock:
        if client_socket in clients:
            del clients[client_socket]
            client_socket.close()


def handle_client(client_socket):
    """클라이언트의 메시지를 처리한다."""
    try:
        # 닉네임 수신
        nickname = client_socket.recv(1024).decode('utf-8').strip()

        with lock:
            clients[client_socket] = nickname

        enter_msg = f'{nickname}님이 입장하셨습니다.'
        print(enter_msg)
        send_to_client(client_socket, enter_msg)
        broadcast(enter_msg, sender_socket=client_socket)

        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = data.decode('utf-8').strip()

            if message == '/종료':
                exit_msg = f'{nickname}님이 퇴장하셨습니다.'
                print(exit_msg)
                broadcast(exit_msg)
                break

            # 귓속말: /귓속말 대상닉네임 메시지 (보너스)
            elif message.startswith('/귓속말 '):
                parts = message.split(' ', 2)
                if len(parts) >= 3:
                    target_nickname = parts[1]
                    whisper_text = parts[2]
                    target_socket = None
                    with lock:
                        for sock, nick in clients.items():
                            if nick == target_nickname:
                                target_socket = sock
                                break
                    if target_socket:
                        send_to_client(
                            target_socket,
                            f'[귓속말] {nickname}> {whisper_text}'
                        )
                        send_to_client(
                            client_socket,
                            f'[귓속말 → {target_nickname}] {nickname}> {whisper_text}'
                        )
                    else:
                        send_to_client(
                            client_socket,
                            f'{target_nickname}님을 찾을 수 없습니다.'
                        )
                else:
                    send_to_client(client_socket, '귓속말 형식: /귓속말 닉네임 메시지')

            else:
                chat_msg = f'{nickname}> {message}'
                print(chat_msg)
                broadcast(chat_msg, sender_socket=client_socket)
                send_to_client(client_socket, chat_msg)

    except OSError:
        pass
    finally:
        remove_client(client_socket)


def bind_socket(server_socket, host):
    """소켓 바인드를 시도하고 실패 시 사용자에게 포트를 입력받는다."""
    port = 999

    while True:
        try:
            server_socket.bind((host, port))
            return port
        except (PermissionError, OSError):
            user_input = input(
                f'포트 {port}번 사용 불가. 다른 포트 번호 입력 (Enter: 9999): '
            ).strip()
            port = int(user_input) if user_input.isdigit() else 9999


def run_server():
    """채팅 서버를 실행한다."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('소캣 생성완료')

    host = socket.gethostname()
    print(host)

    port = bind_socket(server_socket, host)
    server_socket.listen(3)
    print(f'채팅 서버가 {host}:{port} 에서 대기 중입니다...')

    while True:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(client_socket,),
            daemon=True
        )
        thread.start()


if __name__ == '__main__':
    run_server()