# player.py
import math
from game_framework import pygame, GameObject, SpriteRenderer


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__("Player", x, y)
        self.move_speed = 200.0
        # 충돌 박스용 스케일 (렌더링은 SpriteRenderer가 알아서 비율 유지함)
        self.scale = [14, 23]

        # SpriteRenderer 컴포넌트 추가
        self.renderer = self.add_component(SpriteRenderer)

        # --- 애니메이션 등록 ---
        base_path = "./resources/Player/"

        # 1. Idle (대기) - 4프레임
        self.renderer.add_animation("Idle_B", base_path + "PLAYER_IDLE_B_12X23X4.png", 4, 1)
        self.renderer.add_animation("Idle_F", base_path + "PLAYER_IDLE_F_16X23X4.png", 4, 1)
        self.renderer.add_animation("Idle_RB", base_path + "PLAYER_IDLE_RB_15X23X4.png", 4, 1)
        self.renderer.add_animation("Idle_RF", base_path + "PLAYER_IDLE_RF_18X23X4.png", 4, 1)

        # 2. Walk (걷기) - 3프레임 (파일명 끝이 X3 임에 주의!)
        self.renderer.add_animation("Walk_B", base_path + "PLAYER_WALK_B_14X23X3.png", 3, 1)
        self.renderer.add_animation("Walk_F", base_path + "PLAYER_WALK_F_14X30X3.png", 3, 1)
        self.renderer.add_animation("Walk_RB", base_path + "PLAYER_WALK_RB_17X26X3.png", 3, 1)
        # 이미지 파일명을 보니 RF는 17X25 크기네요
        self.renderer.add_animation("Walk_RF", base_path + "PLAYER_WALK_RF_17X25X3.png", 3, 1)

        # 초기 설정
        self.renderer.set_scale(1.75)
        self.renderer.play("Idle_F")

    def update(self, dt):
        super().update(dt)

        # 1. 이동 처리
        keys = pygame.key.get_pressed()
        velocity = [0, 0]

        if keys[pygame.K_LEFT]: velocity[0] -= 1
        if keys[pygame.K_RIGHT]: velocity[0] += 1
        if keys[pygame.K_UP]: velocity[1] += 1
        if keys[pygame.K_DOWN]: velocity[1] -= 1

        is_moving = False
        if velocity[0] != 0 or velocity[1] != 0:
            is_moving = True
            # 대각선 이동 시 속도 일정하게 (정규화는 하지 않더라도 이동 처리 적용)
            self.position[0] += velocity[0] * self.move_speed * dt
            self.position[1] += velocity[1] * self.move_speed * dt

        # 2. 마우스 각도 및 이동 상태에 따른 애니메이션 변경
        self._update_animation_by_mouse(is_moving)

    def _update_animation_by_mouse(self, is_moving):
        mouse_pos = pygame.mouse.get_pos()

        # 플레이어 기준 마우스 벡터
        dx = mouse_pos[0] - self.position[0]
        # 화면 좌표계(Y가 아래로 증가) -> 수학 좌표계(Y가 위로 증가) 변환
        dy = -(mouse_pos[1] - self.position[1])

        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360

        # --- 상태 접두사 결정 ---
        # 움직이고 있으면 "Walk", 아니면 "Idle"
        state_prefix = "Walk" if is_moving else "Idle"

        # --- 각도별 방향 접미사 결정 ---
        direction_suffix = ""
        flip = False

        if 0 <= angle < 60:
            direction_suffix = "_RB"  # 우측 상단
            flip = False
        elif 60 <= angle < 120:
            direction_suffix = "_B"  # 상단 (뒤)
            flip = False
        elif 120 <= angle < 180:
            direction_suffix = "_RB"  # 좌측 상단 (우측 반전)
            flip = True
        elif 180 <= angle < 240:
            direction_suffix = "_RF"  # 좌측 하단 (우측 반전)
            flip = True
        elif 240 <= angle < 300:
            direction_suffix = "_F"  # 하단 (앞)
            flip = False
        else:  # 300 ~ 360
            direction_suffix = "_RF"  # 우측 하단
            flip = False

        # 최종 애니메이션 이름 조합 (예: Walk_RB, Idle_F)
        target_anim = f"{state_prefix}{direction_suffix}"

        self.renderer.play(target_anim)
        self.renderer.flip_x = flip