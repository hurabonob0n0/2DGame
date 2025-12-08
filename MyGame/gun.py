import math
import random
from pico2d import load_image,load_wav
import game_framework
import game_world
from state_machine import StateMachine
from bullet import Bullet


# -------------------------------------------------------------------
# Gun States (로직은 동일하지만 update_angle 호출 시점 중요)
# -------------------------------------------------------------------

class Idle:
    def __init__(self, gun):
        self.gun = gun

    def enter(self, e): pass

    def exit(self, e): pass

    def do(self):
        self.gun.update_angle()  # 각도 갱신

    def draw(self, camera):
        self.gun.draw_gun(camera, 'Shoot', 0)


class Shoot:
    def __init__(self, gun):
        self.gun = gun
        self.duration = 0.25
        self.total_frames = 4
        self.fps = self.total_frames / self.duration

    def enter(self, e):
        self.timer = 0.0
        self.frame = 0.0
        self.fired = False

    def exit(self, e):
        pass

    def do(self):
        self.gun.update_angle()  # 쏘는 중에도 조준 유지

        self.timer += game_framework.frame_time
        self.frame = self.timer * self.fps

        if self.frame >= 2.0 and not self.fired:
            self.fire_bullet()
            self.fired = True
            self.gun.ammo -= 1

        if self.timer >= self.duration:
            if self.gun.ammo <= 0:
                self.gun.state_machine.handle_state_event(('RELOAD_NEEDED', None))
            else:
                self.gun.state_machine.handle_state_event(('SHOOT_FINISH', None))

    def fire_bullet(self):
        error_deg = random.uniform(-5.0, 5.0)
        final_angle = self.gun.angle + math.radians(error_deg)

        # 💖 [수정] 총구 위치: 이제 총 자체가 공전하므로, 총의 현재 위치(self.x, y)에서 조금 더 앞으로 나간 곳
        # (draw_scale이 커졌으므로 총구 offset도 약간 늘려줍니다)
        spawn_dist = 30
        bx = self.gun.x + math.cos(final_angle) * spawn_dist
        by = self.gun.y + math.sin(final_angle) * spawn_dist

        bullet = Bullet(bx, by, final_angle)
        game_world.add_object(bullet, 2)
        game_world.add_collision_pair('player:enemy_bullet', None, bullet)
        game_world.add_collision_pair('sword:enemy_bullet', None, bullet)

        self.gun.gunsound.play()

    def draw(self, camera):
        cur_frame = int(self.frame) % 4
        self.gun.draw_gun(camera, 'Shoot', cur_frame)


class Reload:
    def __init__(self, gun):
        self.gun = gun
        self.duration = 1.0
        self.total_frames = 5
        self.fps = self.total_frames / self.duration

    def enter(self, e):
        self.timer = 0.0
        self.frame = 0.0

    def exit(self, e):
        self.gun.ammo = 4

    def do(self):
        self.gun.update_angle()  # 재장전 중에도 조준

        self.timer += game_framework.frame_time
        self.frame = self.timer * self.fps

        if self.timer >= self.duration:
            self.gun.state_machine.handle_state_event(('RELOAD_FINISH', None))

    def draw(self, camera):
        cur_frame = int(self.frame) % 5
        self.gun.draw_gun(camera, 'Reload', cur_frame)


# -------------------------------------------------------------------
# Gun Class
# -------------------------------------------------------------------

class Gun:
    def __init__(self, owner):
        self.owner = owner
        self.x, self.y = 0, 0
        self.angle = 0.0
        self.ammo = 4

        # 💖 [수정] 공전 반지름 설정 (적 몸체에서 떨어진 거리)
        self.r = 20

        self.gunsound = load_wav('./Assets/Sounds/gun.wav')
        self.gunsound.set_volume(100)
        # 💖 [수정] 크기 1.5배 확대 (기존 2.0 -> 3.0)
        self.draw_scale = 3.0

        self.images = {
            'Shoot': load_image('./Assets/Weapon/EGUN_SHOT_18X9X4.png'),
            'Reload': load_image('./Assets/Weapon/EGUN_RELOAD_18X17X5.png')
        }
        self.sprite_data = {
            'Shoot': {'w': 18, 'h': 9, 'frames': 4},
            'Reload': {'w': 18, 'h': 17, 'frames': 5}
        }

        self.IDLE = Idle(self)
        self.SHOOT = Shoot(self)
        self.RELOAD = Reload(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    lambda e: e[0] == 'FIRE': self.SHOOT,
                    lambda e: e[0] == 'RELOAD_NEEDED': self.RELOAD
                },
                self.SHOOT: {
                    lambda e: e[0] == 'SHOOT_FINISH': self.IDLE,
                    lambda e: e[0] == 'RELOAD_NEEDED': self.RELOAD
                },
                self.RELOAD: {
                    lambda e: e[0] == 'RELOAD_FINISH': self.IDLE
                }
            }
        )

    def update(self):
        # 1. 상태 업데이트 (여기서 update_angle이 호출되어 self.angle이 결정됨)
        self.state_machine.update()

        # 💖 [수정] 공전 로직 적용
        # Enemy 위치 + (반지름 * 각도) = 총의 위치
        self.x = self.owner.x + self.r * math.cos(self.angle)
        self.y = self.owner.y + self.r * math.sin(self.angle)

    def update_angle(self):
        # 플레이어를 향해 각도 계산
        dx = self.owner.player.x - self.owner.x
        dy = self.owner.player.y - self.owner.y
        self.angle = math.atan2(dy, dx)

    def draw(self, camera):
        self.state_machine.draw(camera)

    def draw_gun(self, camera, key, frame_index):
        data = self.sprite_data[key]
        img = self.images[key]

        abs_deg = abs(math.degrees(self.angle))
        flip = ''
        if 90 < abs_deg:
            flip = 'v'

        img.clip_composite_draw(
            frame_index * data['w'], 0, data['w'], data['h'],
            self.angle, flip,
            self.x - camera.world_l, self.y - camera.world_b,
            data['w'] * self.draw_scale, data['h'] * self.draw_scale
        )

    def fire(self):
        if self.state_machine.cur_state == self.IDLE and self.ammo > 0:
            self.state_machine.handle_state_event(('FIRE', None))