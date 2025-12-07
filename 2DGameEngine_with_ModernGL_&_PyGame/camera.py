import numpy as np
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from transform import create_ortho_projection

# [수정 전] 순환 참조의 원인
# from game_framework import GameObject

# [수정 후] 직접 원본 파일에서 가져오기
from game_object import GameObject

# 현재 활성화된 카메라를 담을 전역 변수
active_camera = None

class Camera(GameObject):
    def __init__(self, x=0, y=0):
        # 1. GameObject 상속 (이제 카메라 위치는 self.position에 저장됨)
        super().__init__("Camera", x, y)
        self.zoom = 1.0

        # 투영 행렬 (Projection)
        self.projection = create_ortho_projection(
            left=0, right=SCREEN_WIDTH,
            bottom=SCREEN_HEIGHT, top=0,
            near=-1.0, far=1.0
        )

        # 생성되자마자 자신을 메인 카메라로 등록
        global active_camera
        if active_camera is None:
            active_camera = self

    def update(self, dt):
        super().update(dt)
        # 카메라 흔들림(Shake) 효과 등이 필요하면 여기에 구현

    def get_view_projection_matrix(self):
        # 1. 뷰 변환 (카메라 위치가 세상의 중심이 되도록 이동)
        # self.position은 GameObject의 속성 사용
        cam_x = self.position[0]
        cam_y = self.position[1]

        # 2. 화면 중앙 보정 (Center Offset)
        # 카메라 좌표가 화면의 '중앙'을 가리키도록 함
        # 이 보정이 없으면 플레이어가 화면 좌상단(0,0)에 박혀있게 됨
        offset_x = SCREEN_WIDTH / 2
        offset_y = SCREEN_HEIGHT / 2

        # 3. 행렬 생성 (역행렬 개념: 카메라는 반대로 이동해야 세상이 움직여 보임)
        # 이동: (-CameraPos + ScreenCenter)
        view_translate = np.identity(4, dtype='f4')
        view_translate[3, 0] = -cam_x * self.zoom + offset_x
        view_translate[3, 1] = -cam_y * self.zoom + offset_y

        # 줌 (Scale)
        view_scale = np.identity(4, dtype='f4')
        view_scale[0, 0] = self.zoom
        view_scale[1, 1] = self.zoom

        # 순서: Zoom -> Translate (여기선 단순화를 위해 결합된 로직 사용)
        view_matrix = view_scale @ view_translate

        # VP 행렬 반환
        return self.projection @ view_matrix