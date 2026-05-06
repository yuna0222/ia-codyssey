"""
cctv.py - 화성 기지 CCTV 이미지 뷰어 + 사람 탐지
- 문제 9: 좌/우 방향키로 이미지 탐색
- 문제 10: OpenCV DNN YOLOv3로 사람 탐지, 엔터키로 다음 사진 검색
"""

import os
import urllib.request
import zipfile
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk


class MasImageHelper:
    """CCTV 이미지 목록 관리 및 ZIP 압축 해제를 담당하는 클래스."""

    EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    DEFAULT_FOLDER = 'CCTV'
    DEFAULT_ZIP = 'cctv.zip'

    def __init__(self, folder=DEFAULT_FOLDER, zip_path=DEFAULT_ZIP):
        """폴더가 없으면 ZIP을 해제한 뒤 이미지 목록을 로드한다."""
        if not os.path.exists(folder):
            self._extract(zip_path)
        if not os.path.exists(folder):
            raise FileNotFoundError(
                f'ZIP 해제 후에도 {folder} 폴더를 찾을 수 없습니다. '
                'ZIP 파일 안에 CCTV 폴더가 있는지 확인해 주세요.'
            )
        self.files = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(self.EXTENSIONS)  # 이미지 형식 아닌 건 무시
        )
        if not self.files:
            raise ValueError(f'이미지 파일이 없습니다: {folder}')
        self.index = 0

    # ── 내부 유틸 ──────────────────────────────────────────────
    def _extract(self, zip_path):
        """ZIP 파일을 현재 디렉터리에 압축 해제한다."""
        if not os.path.exists(zip_path):
            raise FileNotFoundError(
                f'CCTV 폴더와 ZIP 파일({zip_path}) 모두 찾을 수 없습니다. '
                f'{self.DEFAULT_ZIP} 파일을 이 스크립트와 같은 폴더에 넣어 주세요.'
            )
        with zipfile.ZipFile(zip_path, 'r') as z:
            names = z.namelist()
            # 폴더 구조 없이 파일만 있으면 DEFAULT_FOLDER 안에 직접 해제
            has_folder = any('/' in n for n in names)
            target = '.' if has_folder else self.DEFAULT_FOLDER
            os.makedirs(target, exist_ok=True)
            z.extractall(target)
        print(f'압축 해제 완료: {zip_path} → {target}')

    # ── 탐색 ───────────────────────────────────────────────────
    def move(self, step):
        """인덱스를 step만큼 이동한다 (순환)."""
        self.index = (self.index + step) % len(self.files)

    def has_next(self):
        """마지막 이미지가 아니면 True를 반환한다."""
        return self.index < len(self.files) - 1

    # ── 현재 이미지 정보 ───────────────────────────────────────
    def current_image(self):
        """현재 이미지를 PIL Image로 반환한다."""
        try:
            return Image.open(self.files[self.index])
        except (OSError, SyntaxError):
            raise OSError(f'이미지를 열 수 없습니다: {self.files[self.index]}')

    def current_path(self):
        """현재 이미지 파일 경로를 반환한다."""
        return self.files[self.index]

    def status(self):
        """'파일명 (현재/전체)' 형식의 상태 문자열을 반환한다."""
        name = os.path.basename(self.files[self.index])
        return f'{name}  ({self.index + 1} / {len(self.files)})'


class PersonDetector:
    """OpenCV DNN + YOLOv3 기반 사람 탐지 클래스."""

    # YOLOv3 모델 파일 경로 (cctv.py 와 같은 폴더에 위치)
    WEIGHTS = 'yolov3.weights'
    CONFIG = 'yolov3.cfg'
    NAMES = 'coco.names'
    # 탐지 설정
    CONFIDENCE_THRESHOLD = 0.15  # 신뢰도 임계값 (낮을수록 더 많이 감지)
    NMS_THRESHOLD = 0.3          # NMS 중복 제거 임계값
    INPUT_SIZE = (608, 608)      # YOLO 입력 크기 (클수록 작은 객체 잘 감지)

    # YOLOv3 모델 파일 다운로드 URL
    URLS = {
        'yolov3.weights': 'https://pjreddie.com/media/files/yolov3.weights',
        'yolov3.cfg': 'https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg',
        'coco.names': 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names',
    }

    @classmethod
    def download_models(cls):
        """
        YOLOv3 모델 파일 3개를 urllib로 자동 다운로드한다.
        성공하면 True, 실패하면 False를 반환한다.
        """
        for filename, url in cls.URLS.items():
            if os.path.exists(filename):
                print(f'이미 존재: {filename} (건너뜀)')
                continue
            print(f'다운로드 중: {filename} ...')
            try:
                urllib.request.urlretrieve(url, filename)
                print(f'완료: {filename}')
            except Exception as e:
                print(f'다운로드 실패: {filename} — {e}')
                return False
        return True

    def __init__(self):
        """YOLOv3 모델과 클래스 목록을 로드한다."""
        if not all(os.path.exists(f) for f in
                   (self.WEIGHTS, self.CONFIG, self.NAMES)):
            raise FileNotFoundError(
                'YOLOv3 파일이 없습니다. '
                'yolov3.weights / yolov3.cfg / coco.names 를 '
                'cctv.py 와 같은 폴더에 넣어 주세요.'
            )
        # DNN 네트워크 로드
        self._net = cv2.dnn.readNet(self.WEIGHTS, self.CONFIG)
        # 출력 레이어 이름 추출
        layer_names = self._net.getLayerNames()
        self._output_layers = [
            layer_names[i - 1]
            for i in self._net.getUnconnectedOutLayers().flatten()
        ]
        # 클래스 이름 로드 (person 클래스만 사용)
        with open(self.NAMES) as f:
            self._classes = [line.strip() for line in f]

    def detect(self, image_path):
        """
        이미지에서 사람을 탐지하고 박스가 그려진 PIL Image와 감지 수를 반환한다.

        Args:
            image_path (str): 이미지 파일 경로

        Returns:
            tuple: (PIL Image, int) — 박스가 그려진 이미지, 감지된 사람 수
        """
        img = cv2.imread(image_path)
        if img is None:
            raise OSError(f'이미지를 읽을 수 없습니다: {image_path}')

        h, w = img.shape[:2]

        # YOLO 입력 블롭 생성
        blob = cv2.dnn.blobFromImage(
            img, 1 / 255.0, self.INPUT_SIZE, swapRB=True, crop=False
        )
        self._net.setInput(blob)
        outputs = self._net.forward(self._output_layers)

        # 감지 결과 파싱 (person 클래스만 필터링)
        boxes, confidences = [], []
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = int(scores.argmax())
                confidence = float(scores[class_id])
                if (self._classes[class_id] == 'person'
                        and confidence > self.CONFIDENCE_THRESHOLD):
                    cx, cy, bw, bh = (detection[:4] * [w, h, w, h]).astype(int)
                    x, y = cx - bw // 2, cy - bh // 2
                    boxes.append([x, y, bw, bh])
                    confidences.append(confidence)

        # NMS로 중복 박스 제거
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.CONFIDENCE_THRESHOLD, self.NMS_THRESHOLD
        )
        final_boxes = [boxes[i] for i in indices.flatten()] if len(indices) else []

        # 감지된 사람마다 빨간 사각형 + 신뢰도 표시 (보너스 과제)
        for i, (x, y, bw, bh) in enumerate(final_boxes):
            cv2.rectangle(img, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
            label = f'person {confidences[indices.flatten()[i]]:.0%}'
            cv2.putText(img, label, (x, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # OpenCV BGR → PIL RGB 변환
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img_rgb), len(final_boxes)


class CCTVViewer:
    """tkinter 기반 CCTV 이미지 뷰어 GUI (문제 9)."""

    # 캔버스 크기
    W, H = 860, 600
    # 색상
    BG = '#1a1a2e'
    BG_CANVAS = '#16213e'
    COLOR_ACCENT = '#e94560'
    COLOR_ACCENT_DARK = '#c73652'
    COLOR_INFO = '#a8dadc'
    COLOR_HINT = '#555577'
    # 텍스트
    TITLE = '화성 기지 CCTV 뷰어'
    TITLE_LABEL = '🔴 화성 기지 CCTV'
    HINT_LABEL = '← 이전   |   → 다음   |   S: 사람 탐지 시작'
    # 버튼 색상
    BTN_BG = '#333333'
    BTN_FG = 'white'

    def __init__(self, root, helper):
        """윈도우·위젯을 구성하고 첫 이미지를 표시한다."""
        self.helper = helper
        self._build_ui(root)
        self._show()

    # ── UI 구성 ────────────────────────────────────────────────
    def _build_ui(self, root):
        """윈도우, 캔버스, 버튼, 레이블을 생성한다."""
        root.title(self.TITLE)
        root.configure(bg=self.BG)
        root.resizable(False, False)

        # 제목
        tk.Label(root, text=self.TITLE_LABEL,
                 font=('Arial', 15, 'bold'),
                 fg=self.COLOR_ACCENT, bg=self.BG).pack(pady=(10, 0))

        # 이미지 캔버스
        self.canvas = tk.Canvas(root, width=self.W, height=self.H,
                                bg=self.BG_CANVAS, highlightthickness=2,
                                highlightbackground=self.COLOR_ACCENT)
        self.canvas.pack(pady=8)

        # 하단 버튼 · 상태 레이블
        bar = tk.Frame(root, bg=self.BG)
        bar.pack(pady=4)

        # Canvas 버튼 생성 헬퍼 (색상이 맥/윈도우 모두 고정됨)
        def make_btn(parent, text, command, width=120):
            """Canvas로 직접 그린 버튼 — 맥/윈도우 색상 일관성 보장."""
            c = tk.Canvas(parent, width=width, height=42,
                          bg=self.BG, highlightthickness=0, cursor='hand2')
            rect = c.create_rectangle(0, 0, width, 42,
                                      fill=self.BTN_BG, outline='')
            label = c.create_text(width // 2, 21, text=text,
                                  fill=self.BTN_FG,
                                  font=('Arial', 13, 'bold'))
            # 클릭
            c.tag_bind(rect, '<Button-1>', lambda e: command())
            c.tag_bind(label, '<Button-1>', lambda e: command())
            return c

        make_btn(bar, '◀  이전', lambda: self._nav(-1)).grid(
            row=0, column=0, padx=12)
        self.lbl = tk.Label(bar, text='', width=28,
                            font=('Arial', 12),
                            fg=self.COLOR_INFO, bg=self.BG)
        self.lbl.grid(row=0, column=1)
        make_btn(bar, '다음  ▶', lambda: self._nav(+1)).grid(
            row=0, column=2, padx=12)

        # 사람 탐지 버튼 (넓게)
        make_btn(root, '🔍  사람 탐지 시작 (S)',
                 self._start_detection, width=260).pack(pady=(4, 2))

        # 키보드 단축키 안내 레이블
        tk.Label(root, text=self.HINT_LABEL,
                 font=('Arial', 9), fg=self.COLOR_HINT, bg=self.BG).pack(pady=(0, 6))

        # 키 바인딩
        root.bind('<Left>',  lambda e: self._nav(-1))
        root.bind('<Right>', lambda e: self._nav(+1))
        root.bind('s',       lambda e: self._start_detection())
        root.bind('S',       lambda e: self._start_detection())

    # ── 이미지 표시 ────────────────────────────────────────────
    def _show(self, pil_image=None):
        """
        이미지를 캔버스에 표시한다.
        pil_image가 주어지면 그것을, 없으면 현재 helper 이미지를 사용한다.
        """
        try:
            img = pil_image if pil_image else self.helper.current_image()
        except OSError as e:
            self.lbl.config(text=f'오류: {e}')
            return
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

    # ── 사람 탐지 시작 ─────────────────────────────────────────
    def _start_detection(self):
        """사람 탐지 모드를 별도 창으로 시작한다. 인덱스를 0으로 초기화한다."""
        try:
            detector = PersonDetector()  # 모델 파일 없으면 FileNotFoundError
        except FileNotFoundError:
            # 모델 파일 없을 때 다운로드 여부를 팝업으로 확인
            ok = messagebox.askyesno(
                'YOLOv3 파일 없음',
                'YOLOv3 모델 파일이 없습니다.\n\n'
                '자동으로 다운로드할까요? (약 236MB, 시간이 걸릴 수 있습니다)'
            )
            if not ok:
                return
            # 다운로드 진행 안내 팝업
            messagebox.showinfo(
                '다운로드 중',
                '터미널에서 다운로드를 시작합니다.\n'
                '완료될 때까지 기다려 주세요.\n\n'
                '완료 후 자동으로 탐지가 시작됩니다.'
            )
            if not PersonDetector.download_models():
                messagebox.showerror('다운로드 실패', '모델 파일 다운로드에 실패했습니다.\n인터넷 연결을 확인해 주세요.')
                return
            try:
                detector = PersonDetector()  # 다운로드 후 재시도
            except FileNotFoundError as e:
                messagebox.showerror('오류', str(e))
                return
        self.helper.index = 0
        DetectionViewer(tk.Toplevel(), self.helper, detector)


class DetectionViewer:
    """
    사람 탐지 결과를 순차적으로 보여주는 뷰어 (문제 10).

    동작 방식:
    - 사진을 순차 탐색하며 사람이 발견된 사진만 화면에 출력한다.
    - 사람이 없는 사진은 자동으로 건너뛴다.
    - 사람이 발견되면 멈추고 엔터키를 기다린다.
    - 마지막 사진까지 탐지가 끝나면 완료 메시지를 표시한다.
    """

    # 캔버스 크기
    W, H = 860, 600
    # 색상
    BG = '#0d0d1a'
    BG_CANVAS = '#111122'
    COLOR_ACCENT = '#e94560'
    COLOR_INFO = '#a8dadc'
    COLOR_FOUND = '#00ff88'
    COLOR_NONE = '#aaaaaa'

    def __init__(self, root, helper, detector):
        """탐지 창을 구성하고 첫 번째 이미지부터 탐지를 시작한다."""
        self.helper = helper
        self.detector = detector
        self._root = root
        self._build_ui(root)
        self._search_next()  # 사람이 있는 사진을 찾을 때까지 순차 탐색 시작

    # ── UI 구성 ────────────────────────────────────────────────
    def _build_ui(self, root):
        """탐지 전용 창 UI를 구성한다."""
        root.title('사람 탐지 - 화성 기지 CCTV')
        root.configure(bg=self.BG)
        root.resizable(False, False)

        tk.Label(root, text='🔍 사람 탐지 중',
                 font=('Arial', 15, 'bold'),
                 fg=self.COLOR_ACCENT, bg=self.BG).pack(pady=(10, 0))

        # 이미지 캔버스
        self.canvas = tk.Canvas(root, width=self.W, height=self.H,
                                bg=self.BG_CANVAS, highlightthickness=2,
                                highlightbackground=self.COLOR_ACCENT)
        self.canvas.pack(pady=8)

        # 탐지 결과 레이블
        self.result_lbl = tk.Label(root, text='탐지 중...',
                                   font=('Arial', 12, 'bold'),
                                   fg=self.COLOR_INFO, bg=self.BG)
        self.result_lbl.pack()

        # 엔터키 안내 레이블
        self.hint_lbl = tk.Label(root, text='Enter: 다음 사진 탐지',
                                 font=('Arial', 9),
                                 fg='#555577', bg=self.BG)
        self.hint_lbl.pack(pady=(2, 8))

        # 엔터키 → 다음 탐색
        root.bind('<Return>', lambda e: self._on_enter())

    # ── 탐지 로직 ──────────────────────────────────────────────
    def _search_next(self):
        """
        사람이 발견될 때까지 사진을 순차적으로 탐색한다.
        사람이 발견되면 화면에 출력하고 엔터 입력을 기다린다.
        모든 사진을 탐색하면 완료 메시지를 표시한다.
        """
        while True:
            path = self.helper.current_path()
            name = os.path.basename(path)
            idx = self.helper.index + 1
            total = len(self.helper.files)

            try:
                img, count = self.detector.detect(path)
            except OSError as e:
                # 손상된 이미지는 건너뜀
                self.result_lbl.config(text=f'오류 (건너뜀): {e}',
                                       fg='#ff4444')
                if not self.helper.has_next():
                    self._done()
                    return
                self.helper.move(+1)
                continue

            if count > 0:
                # 사람 발견 → 이미지 출력 후 엔터 대기
                self._show(img)
                msg = f'✅ [{name}] ({idx}/{total}) — 사람 {count}명 발견!'
                self.result_lbl.config(text=msg, fg=self.COLOR_FOUND)
                return  # 엔터 입력 대기 (루프 종료)

            # 사람 없음 → 자동으로 다음 사진으로
            if not self.helper.has_next():
                self._done()
                return
            self.helper.move(+1)

    def _on_enter(self):
        """엔터키 입력 시 다음 사진부터 탐색을 재개한다."""
        if not self.helper.has_next():
            self._done()
            return
        self.helper.move(+1)
        self._search_next()

    def _done(self):
        """모든 사진 탐지 완료 메시지를 표시하고 엔터 바인딩을 해제한다."""
        self.result_lbl.config(text='🔚 모든 사진 탐지 완료!',
                               fg=self.COLOR_ACCENT)
        self.hint_lbl.config(text='창을 닫아 주세요.')
        self._root.unbind('<Return>')

    # ── 이미지 표시 ────────────────────────────────────────────
    def _show(self, pil_image):
        """PIL Image를 캔버스 크기에 맞춰 표시한다."""
        pil_image.thumbnail((self.W, self.H), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(pil_image)  # GC 방지용 참조 보관
        self.canvas.delete('all')
        self.canvas.create_image(self.W // 2, self.H // 2,
                                 anchor='center', image=self._photo)


def main():
    """MasImageHelper, CCTVViewer를 초기화하고 이벤트 루프를 시작한다."""
    try:
        helper = MasImageHelper()          # ZIP 해제 + 이미지 목록 로드
    except (FileNotFoundError, ValueError) as e:
        # ZIP 파일 또는 이미지가 없을 때 GUI 에러 창으로 안내 후 종료
        root = tk.Tk()
        root.withdraw()                     # 빈 메인 윈도우 숨김
        messagebox.showerror('오류', str(e))
        return

    root = tk.Tk()
    CCTVViewer(root, helper)                # GUI 구성 + 첫 이미지 표시
    root.mainloop()


if __name__ == '__main__':
    main()