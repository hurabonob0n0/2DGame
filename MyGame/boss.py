import random
import math
import game_framework
import game_world
import play_mode
from pico2d import *
from state_machine import StateMachine
from bullet import Bullet

# --------------------------------------------------------------------------------
# 상수 설정
# --------------------------------------------------------------------------------
PIXEL_PER_METER = (10.0 / 0.3)

# 보스 이동 속도 (WALK)
WALK_SPEED_KMPH = 20.0
WALK_SPEED_PPS = (WALK_SPEED_KMPH * 1000.0 / 60.0 / 60.0 * PIXEL_PER_METER)

# 돌진 속도 (빠름, 300)
DASH_SPEED_PPS = 600.0

# 공격 감지 거리 (이 거리 안으로 들어오면 패턴 시작)
ATTACK_RANGE = 500.0  # 적절히 조정


# --------------------------------------------------------------------------------
# 헬퍼 함수
# --------------------------------------------------------------------------------
def get_direction_to_player(boss):
    dx = boss.player.x - boss.x
    dy = boss.player.y - boss.y
    dist = math.sqrt(dx ** 2 + dy ** 2)
    if dist > 0:
        return dx / dist, dy / dist, dist
    return 0, 0, 0


def get_angle_to_player(boss):
    return math.atan2(boss.player.y - boss.y, boss.player.x - boss.x)


# 이벤트 함수들
def finish_jump(e): return e[0] == 'FINISH_JUMP'


def finish_shot(e): return e[0] == 'FINISH_SHOT'


def finish_dash(e): return e[0] == 'FINISH_DASH'


def death_event(e): return e[0] == 'DEATH'


# --------------------------------------------------------------------------------
# 상태: Walk (추적)
# --------------------------------------------------------------------------------
class Walk:
    def __init__(self, boss):
        self.boss = boss
        self.fps = 6.0 / 1.0  # 6프레임 / 1초

    def enter(self, e):
        self.boss.anim_state = 'Walk'

    def exit(self, e):
        pass

    def do(self):
        # 1. 플레이어 추적
        dx, dy, dist = get_direction_to_player(self.boss)
        self.boss.x += dx * WALK_SPEED_PPS * game_framework.frame_time
        self.boss.y += dy * WALK_SPEED_PPS * game_framework.frame_time

        # 2. 애니메이션
        self.boss.update_animation_direction()
        self.boss.frame = (self.boss.frame + self.fps * game_framework.frame_time) % 6

        # 3. 거리 체크 -> 공격 패턴 전환
        if dist <= ATTACK_RANGE:
            # 💖 [수정] 객체를 직접 넘기지 말고, '이벤트 이름'을 랜덤 선택
            next_event = random.choice(['START_JUMP', 'START_SHOT', 'START_DASH'])
            self.boss.state_machine.handle_state_event((next_event, None))

    def draw(self, camera):
        self.boss.draw_sprite('Walk', camera, int(self.boss.frame))


# --------------------------------------------------------------------------------
# 상태: Jump (상승 -> 하강 -> 16방향 발사)
# --------------------------------------------------------------------------------
class Jump:
    def __init__(self, boss):
        self.boss = boss
        self.rise_duration = 1.5
        self.fall_duration = 0.3
        self.rise_height = 100.0

    def enter(self, e):
        self.timer = 0.0
        self.phase = 1  # 1: 상승, 2: 하강
        self.base_y = self.boss.y
        self.boss.frame = 0.0

    def exit(self, e):
        # 💖 EXIT 할 때 16방향 발사
        self.boss.y = self.base_y  # 위치 보정
        for i in range(16):
            angle = math.radians(i * 22.5)  # 360도 / 16 = 22.5도
            self.boss.fire_bullet(angle)

    def do(self):
        self.timer += game_framework.frame_time

        # Phase 1: 상승 (1.5초)
        if self.phase == 1:
            progress = self.timer / self.rise_duration
            # Y축 이동
            self.boss.y = self.base_y + self.rise_height * progress
            # 애니메이션 0~2
            self.boss.frame = (progress * 2) % 3

            if self.timer >= self.rise_duration:
                self.phase = 2
                self.timer = 0.0

        # Phase 2: 하강 (0.3초)
        elif self.phase == 2:
            progress = self.timer / self.fall_duration
            # Y축 이동 (복귀)
            self.boss.y = self.base_y + self.rise_height * (1 - progress)
            # 애니메이션 2~0 (역재생)
            idx = 2 - (progress * 2)
            if idx < 0: idx = 0
            self.boss.frame = idx

            if self.timer >= self.fall_duration:
                self.boss.state_machine.handle_state_event(('FINISH_JUMP', None))

        self.boss.update_animation_direction()

    def draw(self, camera):
        self.boss.draw_sprite('Walk', camera, int(self.boss.frame))


# --------------------------------------------------------------------------------
# 상태: Shot (충전 -> 4방향 4번 발사)
# --------------------------------------------------------------------------------
class Shot:
    def __init__(self, boss):
        self.boss = boss
        self.charge_time = 0.5
        self.fire_time = 1.0  # 1초동안 발사
        self.fire_count = 4  # 4번 발사

    def enter(self, e):
        self.timer = 0.0
        self.phase = 1  # 1: 충전, 2: 발사
        self.fired_count = 0
        self.fire_interval = self.fire_time / self.fire_count

    def exit(self, e):
        pass

    def do(self):
        self.timer += game_framework.frame_time
        self.boss.update_animation_direction()

        # Phase 1: 충전 (0.5초)
        if self.phase == 1:
            progress = self.timer / self.charge_time
            self.boss.frame = (progress * 2) % 3  # 0~2 프레임

            if self.timer >= self.charge_time:
                self.phase = 2
                self.timer = 0.0  # 타이머 리셋

        # Phase 2: 발사 (1초 동안)
        elif self.phase == 2:
            self.boss.frame = 2.0  # 발사 자세 유지

            # 타이밍에 맞춰 발사
            if self.fired_count < self.fire_count:
                if self.timer >= self.fired_count * self.fire_interval:
                    self.fire_spread()
                    self.fired_count += 1

            if self.timer >= self.fire_time:
                self.boss.state_machine.handle_state_event(('FINISH_SHOT', None))

    def fire_spread(self):
        # 플레이어 방향 기준 -20, -10, +10, +20도
        base_angle = get_angle_to_player(self.boss)
        offsets = [-20, -10, 10, 20]
        for deg in offsets:
            rad = math.radians(deg)
            self.boss.fire_bullet(base_angle + rad)

    def draw(self, camera):
        self.boss.draw_sprite('Walk', camera, int(self.boss.frame))


# --------------------------------------------------------------------------------
# 상태: Dash (대기 -> 돌진)
# --------------------------------------------------------------------------------
class Dash:
    def __init__(self, boss):
        self.boss = boss
        self.wait_time = 1.0
        self.dash_time = 2
        self.target_dx = 0
        self.target_dy = 0


    def enter(self, e):
        self.timer = 0.0
        self.phase = 1  # 1: 대기, 2: 돌진
        # 💖 추적했던 플레이어의 '마지막 방향' 저장 (Lock-on)
        self.target_dx, self.target_dy, _ = get_direction_to_player(self.boss)

    def exit(self, e):
        pass

    def do(self):
        self.timer += game_framework.frame_time
        self.boss.update_animation_direction()

        # Phase 1: 대기 (1초 멈춤)
        if self.phase == 1:
            # 0~6 프레임 애니메이션 (파일은 6장이라 0~5로 매핑)
            progress = self.timer / self.wait_time
            self.boss.frame = (progress * 6) % 6

            if self.timer >= self.wait_time:
                self.phase = 2
                self.timer = 0.0

        # Phase 2: 돌진 (1초 이동)
        elif self.phase == 2:
            # 돌진 중 애니메이션 (빠르게)
            progress = self.timer / self.dash_time
            self.boss.frame = (progress * 12) % 6

            # 이동 (저장해둔 방향으로)
            self.boss.x += self.target_dx * DASH_SPEED_PPS * game_framework.frame_time
            self.boss.y += self.target_dy * DASH_SPEED_PPS * game_framework.frame_time

            if self.timer >= self.dash_time:
                self.boss.state_machine.handle_state_event(('FINISH_DASH', None))

    def draw(self, camera):
        self.boss.draw_sprite('Walk', camera, int(self.boss.frame))


# --------------------------------------------------------------------------------
# 상태: Death
# --------------------------------------------------------------------------------
class Death:
    def __init__(self, boss):
        self.boss = boss
        self.duration = 2.0
        self.total_frames = 3

    def enter(self, e):
        self.timer = 0.0
        self.boss.frame = 0.0

    def exit(self, e):
        game_world.remove_object(self.boss)

    def do(self):
        self.timer += game_framework.frame_time
        progress = self.timer / self.duration
        self.boss.frame = progress * self.total_frames

        if self.timer >= self.duration:
            self.boss.state_machine.cur_state.exit(None)

    def draw(self, camera):
        self.boss.draw_sprite('Death', camera, int(self.boss.frame))


# --------------------------------------------------------------------------------
# Boss Class
# --------------------------------------------------------------------------------
class Boss:
    images = None
    sprite_data = None

    def load_resources(self):
        if Boss.images is None:
            Boss.images = {}
            Boss.sprite_data = {}

            # 💖 보내주신 파일명 기반 로드
            Boss.images['Walk'] = load_image('./Assets/Enemy/BOSS_WALK_50X60X6.png')
            Boss.sprite_data['Walk'] = {'w': 50, 'h': 60, 'frames': 6}

            # 💖 보내주신 파일명 기반 로드
            Boss.images['Death'] = load_image('./Assets/Enemy/BOSS_DEATH_46X60X3.png')
            Boss.sprite_data['Death'] = {'w': 46, 'h': 60, 'frames': 3}

    def __init__(self):
        self.x, self.y = 1000, 600
        self.hp = 20
        self.draw_scale = 3.0
        self.frame = 0.0
        self.anim_flip = ''

        self.load_resources()
        self.player = play_mode.player

        self.WALK = Walk(self)
        self.JUMP = Jump(self)
        self.SHOT = Shot(self)
        self.DASH = Dash(self)
        self.DEATH = Death(self)

        self.state_machine = StateMachine(
            self.WALK,
            {
                self.WALK: {
                    # 💖 [수정] 람다 함수 대신 명확한 이벤트 매핑으로 변경
                    lambda e: e[0] == 'START_JUMP': self.JUMP,
                    lambda e: e[0] == 'START_SHOT': self.SHOT,
                    lambda e: e[0] == 'START_DASH': self.DASH,
                    death_event: self.DEATH
                },
                self.JUMP: {finish_jump: self.WALK, death_event: self.DEATH},
                self.SHOT: {finish_shot: self.WALK, death_event: self.DEATH},
                self.DASH: {finish_dash: self.WALK, death_event: self.DEATH},
                self.DEATH: {}
            }
        )

    def update(self):
        self.state_machine.update()

    def update_animation_direction(self):
        if self.x < self.player.x:
            self.anim_flip = 'h'  # 플레이어가 오른쪽이면 뒤집기
        else:
            self.anim_flip = ''

    def draw_sprite(self, key, camera, frame_index):
        if key not in self.images: return
        data = self.sprite_data[key]
        img = self.images[key]

        # 안전 장치: 프레임 초과 방지
        idx = frame_index % data['frames']

        img.clip_composite_draw(
            idx * data['w'], 0, data['w'], data['h'],
            0, self.anim_flip,
            self.x - camera.world_l, self.y - camera.world_b,
            data['w'] * self.draw_scale, data['h'] * self.draw_scale
        )

    def draw(self, camera):
        self.state_machine.draw(camera)

    def fire_bullet(self, angle):
        bullet = Bullet(self.x, self.y, angle)
        game_world.add_object(bullet, 2)
        # 💖 보스가 쏜 총알은 player와, player의 sword와 충돌함
        game_world.add_collision_pair('player:enemy_bullet', None, bullet)
        game_world.add_collision_pair('sword:enemy_bullet', None, bullet)

    def get_bb(self):
        w = (50 * self.draw_scale) * 0.5
        h = (60 * self.draw_scale) * 0.8
        return self.x - w / 2, self.y - h / 2, self.x + w / 2, self.y + h / 2

    def handle_collision(self, group, other):
        # 이미 죽었으면 무시
        if self.state_machine.cur_state == self.DEATH: return

        # 칼이나 검기에 맞았을 때
        if group == 'sword:enemy' or group == 'sword_bullet:enemy':
            # sword:enemy 일 경우 Swing 상태 확인
            if group == 'sword:enemy':
                if other.state_machine.cur_state != other.SWING:
                    return

            self.hp -= 1
            if self.hp <= 0:
                self.state_machine.handle_state_event(('DEATH', None))