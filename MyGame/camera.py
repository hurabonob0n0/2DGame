import game_framework
from pico2d import clamp  # clamp 함수를 사용하기 위해 import


# 💖 [삭제] import math (더 이상 사용하지 않음)

class Camera:
    def __init__(self):
        # 캔버스 크기 (1920x1080 기준)
        self.canvas_width = 1920
        self.canvas_height = 1080

        # 캔버스 중앙값 (계산에 사용)
        self.center_x = self.canvas_width // 2
        self.center_y = self.canvas_height // 2

        # 💖 [수정] 마우스를 따라갈 최대 오프셋 (400 -> 200)
        self.max_offset = 200

        # 카메라가 비추는 월드 좌표계의 '좌측 하단' 좌표
        self.world_l = 0
        self.world_b = 0

    def update(self, player, mouse_x, mouse_y):
        """ 플레이어와 마우스 위치를 받아 카메라의 위치를 업데이트합니다. """

        # 1. 화면 중앙에서 마우스까지의 벡터 계산
        mouse_vec_x = mouse_x - self.center_x
        mouse_vec_y = mouse_y - self.center_y

        # 2. 마우스 위치의 화면 중앙 대비 비율 계산 ( -1.0 ~ 1.0 )
        ratio_x = 0.0
        if self.center_x != 0:
            ratio_x = mouse_vec_x / self.center_x

        ratio_y = 0.0
        if self.center_y != 0:
            ratio_y = mouse_vec_y / self.center_y

        # 💖 [수정] Ease-In (제곱) 효과 적용
        # (중앙 근처에서는 매우 느리게, 가장자리로 갈수록 가속도가 붙습니다)
        # (ratio * abs(ratio)는 부호를 유지하면서 제곱하는 것과 동일한 효과)
        final_ratio_x = ratio_x * abs(ratio_x)
        final_ratio_y = ratio_y * abs(ratio_y)

        # 3. 최종 비율에 따라 최대 오프셋 적용
        # (이전 요청사항 "마우스가 위로 가면 플레이어는 아래로" 반영됨)
        offset_x = clamp(-self.max_offset, final_ratio_x * self.max_offset, self.max_offset)
        offset_y = clamp(-self.max_offset, final_ratio_y * self.max_offset, self.max_offset)

        # 4. 카메라가 바라볼 최종 위치 (플레이어 위치 + 오프셋)
        look_at_x = player.x + offset_x
        look_at_y = player.y + offset_y

        # 5. 카메라의 좌측 하단 (world_l, world_b) 계산
        self.world_l = look_at_x - self.center_x
        self.world_b = look_at_y - self.center_y

        # (선택사항) 월드 경계가 있다면 카메라가 경계를 벗어나지 않도록 clamp
        # 예: self.world_l = clamp(0, self.world_l, MAX_WORLD_WIDTH - self.canvas_width)
        # 예: self.world_b = clamp(0, self.world_b, MAX_WORLD_HEIGHT - self.canvas_height)