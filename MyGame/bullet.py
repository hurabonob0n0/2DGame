import math
import game_framework
from pico2d import load_image, draw_rectangle

import player

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
        self.spawn_x, self.spawn_y = x, y
        self.angle = angle

        self.dx = math.cos(self.angle) * BULLET_SPEED_PPS
        self.dy = math.sin(self.angle) * BULLET_SPEED_PPS

        self.radius = 32
        self.max_range_sq = (1920 * 2) ** 2

    def update(self):
        self.x += self.dx * game_framework.frame_time
        self.y += self.dy * game_framework.frame_time

        dist_sq = (self.x - self.spawn_x)**2 + (self.y - self.spawn_y)**2
        if dist_sq > self.max_range_sq:
            import game_world
            game_world.remove_object(self)

    def draw(self, camera):
        self.image.draw(self.x - camera.world_l, self.y - camera.world_b, self.radius, self.radius)

    def get_bb(self):
        return self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius

    def handle_collision(self, group, other):
        if group == 'player:enemy_bullet':
            if other.state_machine.cur_state == other.ROLL:
                return
            import game_world
            game_world.remove_object(self)

        elif group == 'sword:enemy_bullet':
            # 💖 [수정] 칼로 총알을 베었을 때 play_mode에 알림
            import game_world
            import play_mode
            play_mode.stage_1_cleared_condition = True # 미션 1 클리어 조건 달성
            game_world.remove_object(self)