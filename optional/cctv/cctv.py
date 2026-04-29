"""
cctv.py - 화성 기지 CCTV 이미지 뷰어
좌/우 방향키로 이미지를 탐색한다.
"""

import os
import zipfile
import tkinter as tk
from PIL import Image, ImageTk


class MarsImageHelper:
    """CCTV 이미지 목록 관리 및 ZIP 압축 해제를 담당하는 클래스."""

    EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

    def __init__(self, folder='CCTV', zip_path='CCTV.zip'):
        """폴더가 없으면 ZIP을 해제한 뒤 이미지 목록을 로드한다."""
        if not os.path.exists(folder):
            self._extract(zip_path)
        self.files = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(self.EXTENSIONS)
        )
        if not self.files:
            raise ValueError(f'이미지 파일 없음: {folder}')
        self.index = 0

    # ── 내부 유틸 ──────────────────────────────────────────────
    def _extract(self, zip_path):
        """ZIP 파일을 현재 디렉터리에 압축 해제한다."""
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall('.')
        print(f'압축 해제 완료: {zip_path}')

    # ── 탐색 ───────────────────────────────────────────────────
    def move(self, step):
        """인덱스를 step만큼 이동한다 (순환)."""
        self.index = (self.index + step) % len(self.files)

    # ── 현재 이미지 정보 ───────────────────────────────────────
    def current_image(self):
        """현재 이미지를 PIL Image로 반환한다."""
        return Image.open(self.files[self.index])

    def status(self):
        """'파일명 (현재/전체)' 형식의 상태 문자열을 반환한다."""
        name = os.path.basename(self.files[self.index])
        return f'{name}  ({self.index + 1} / {len(self.files)})'


class CCTVViewer:
    """tkinter 기반 CCTV 이미지 뷰어 GUI."""

    W, H = 860, 600  # 캔버스 크기

    def __init__(self, root, helper):
        """윈도우·위젯을 구성하고 첫 이미지를 표시한다."""
        self.helper = helper
        self._build_ui(root)
        self._show()

    # ── UI 구성 ────────────────────────────────────────────────
    def _build_ui(self, root):
        """윈도우, 캔버스, 버튼, 레이블을 생성한다."""
        root.title('화성 기지 CCTV 뷰어')
        root.configure(bg='#1a1a2e')
        root.resizable(False, False)

        # 제목
        tk.Label(root, text='🔴 화성 기지 CCTV',
                 font=('Arial', 15, 'bold'),
                 fg='#e94560', bg='#1a1a2e').pack(pady=(10, 0))

        # 이미지 캔버스
        self.canvas = tk.Canvas(root, width=self.W, height=self.H,
                                bg='#16213e', highlightthickness=2,
                                highlightbackground='#e94560')
        self.canvas.pack(pady=8)

        # 하단 버튼 · 상태 레이블
        bar = tk.Frame(root, bg='#1a1a2e')
        bar.pack(pady=4)

        # 버튼 생성 헬퍼 (step: -1=이전, +1=다음)
        def make_btn(text, step):
            return tk.Button(
                bar, text=text, command=lambda: self._nav(step),
                font=('Arial', 11, 'bold'), fg='white', bg='#e94560',
                activebackground='#c73652', relief='flat',
                padx=18, pady=5, cursor='hand2')

        make_btn('◀ 이전', -1).grid(row=0, column=0, padx=12)
        self.lbl = tk.Label(bar, text='', width=34,
                            font=('Arial', 10), fg='#a8dadc', bg='#1a1a2e')
        self.lbl.grid(row=0, column=1)
        make_btn('다음 ▶', +1).grid(row=0, column=2, padx=12)

        # 키보드 단축키 안내 레이블
        tk.Label(root, text='← 이전   |   → 다음',
                 font=('Arial', 8), fg='#555577', bg='#1a1a2e').pack()

        # 방향키 바인딩
        root.bind('<Left>',  lambda e: self._nav(-1))
        root.bind('<Right>', lambda e: self._nav(+1))

    # ── 이미지 표시 ────────────────────────────────────────────
    def _show(self):
        """현재 이미지를 캔버스 크기에 맞춰 표시하고 상태를 갱신한다."""
        img = self.helper.current_image()
        img.thumbnail((self.W, self.H), Image.LANCZOS)  # 비율 유지 리사이즈
        self._photo = ImageTk.PhotoImage(img)            # GC 방지용 참조 보관
        self.canvas.delete('all')
        self.canvas.create_image(self.W // 2, self.H // 2,
                                 anchor='center', image=self._photo)
        self.lbl.config(text=self.helper.status())

    # ── 탐색 ───────────────────────────────────────────────────
    def _nav(self, step):
        """step 방향으로 이동 후 이미지를 새로 표시한다."""
        self.helper.move(step)
        self._show()


def main():
    """MarsImageHelper와 CCTVViewer를 초기화하고 이벤트 루프를 시작한다."""
    helper = MarsImageHelper()   # ZIP 해제 + 이미지 목록 로드
    root = tk.Tk()
    CCTVViewer(root, helper)     # GUI 구성 + 첫 이미지 표시
    root.mainloop()


if __name__ == '__main__':
    main()