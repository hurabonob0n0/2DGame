import math
import game_framework
from pico2d import load_image, draw_rectangle

# 속도 상수
PIXEL_PER_METER = (10.0 / 0.3)
BULLET_SPEED_KMPH = 60.0
BULLET_SPEED_PPS = (BULLET_SPEED_KMPH * 1000.0 / 60.0 / 60.0 * PIXEL_PER_METER)

class Bullet:
    image = None

    def __init__(self, x, y, angle):
        if Bullet.image == None:
            Bullet.image = load_image('./Assets/Weapon/BULLET_32X32X1.png')

        self.x, self.y = x, y
        # 💖 [추가] 사거리 계산을 위한 시작 위치 저장
        self.spawn_x, self.spawn_y = x, y
        self.angle = angle

        self.dx = math.cos(self.angle) * BULLET_SPEED_PPS
        self.dy = math.sin(self.angle) * BULLET_SPEED_PPS

        self.radius = 10
        # 💖 [수정] 총알 삭제 거리 (1920 * 3 = 5760픽셀)
        self.max_range_sq = (1920 * 3) ** 2

    def update(self):
        self.x += self.dx * game_framework.frame_time
        self.y += self.dy * game_framework.frame_time

        # 💖 [수정] 화면 밖 체크 대신 이동 거리 체크
        dist_sq = (self.x - self.spawn_x)**2 + (self.y - self.spawn_y)**2
        if dist_sq > self.max_range_sq:
            import game_world
            game_world.remove_object(self)

    def draw(self, camera):
        # 💖 [수정] 크기 1.3배 적용 (32 * 1.3 = 41.6 -> 약 42)
        draw_size = 32 * 1.3
        self.image.draw(self.x - camera.world_l, self.y - camera.world_b, draw_size, draw_size)

    def get_bb(self):
        return self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius

    def handle_collision(self, group, other):
        if group == 'player:enemy_bullet':
            import game_world
            game_world.remove_object(self)