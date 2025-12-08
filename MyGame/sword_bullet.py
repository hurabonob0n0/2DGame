import math
import game_framework
from pico2d import load_image

# 속도 상수 (총알보다 조금 느리게 설정)
PIXEL_PER_METER = (10.0 / 0.3)
SWORD_BULLET_SPEED_KMPH = 90.0  # 시속 40km
SWORD_BULLET_SPEED_PPS = (SWORD_BULLET_SPEED_KMPH * 1000.0 / 60.0 / 60.0 * PIXEL_PER_METER)


class SwordBullet:
    image = None

    def __init__(self, x, y, angle):
        if SwordBullet.image == None:
            # 💖 [핵심] 칼 이미지 사용
            SwordBullet.image = load_image('./Assets/Weapon/SWORD_AURA_1_64x64.png')

        self.x, self.y = x, y
        self.spawn_x, self.spawn_y = x, y
        self.angle = angle

        self.dx = math.cos(self.angle) * SWORD_BULLET_SPEED_PPS
        self.dy = math.sin(self.angle) * SWORD_BULLET_SPEED_PPS

        # 💖 [설정] 충돌 박스 크기 (칼 형태에 맞춰 직사각형으로)
        self.width = 128
        self.height = 64

        # 사거리 (총알과 동일하게 1920 * 3)
        self.max_range_sq = (1920 * 3) ** 2

    def update(self):
        self.x += self.dx * game_framework.frame_time
        self.y += self.dy * game_framework.frame_time

        # 사거리 체크
        dist_sq = (self.x - self.spawn_x) ** 2 + (self.y - self.spawn_y) ** 2
        if dist_sq > self.max_range_sq:
            import game_world
            game_world.remove_object(self)

    def draw(self, camera):
        # 💖 칼 이미지를 진행 방향(angle)으로 회전시켜 그림
        # clip_composite_draw를 사용해 회전 구현 (원본 크기 사용)
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            self.angle, '',
            self.x - camera.world_l, self.y - camera.world_b,
            128, 128  # 그릴 크기
        )

    def get_bb(self):
        # 중심 기준 BB 계산
        return self.x - self.width / 2, self.y - self.height / 2, self.x + self.width / 2, self.y + self.height / 2

    def handle_collision(self, group, other):
        # 💖 [핵심] 적과 충돌 시 자신 삭제
        if group == 'sword_bullet:enemy':
            import game_world
            game_world.remove_object(self)