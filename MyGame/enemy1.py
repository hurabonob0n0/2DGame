import random
import math
import game_framework
import game_world
import play_mode
from pico2d import *
from state_machine import StateMachine
from gun import Gun

# --------------------------------------------------------------------------------
# 상수 설정
# --------------------------------------------------------------------------------
PIXEL_PER_METER = (10.0 / 0.3)

# 추적 속도 (빠름)
CHASE_SPEED_KMPH = 15.0
CHASE_SPEED_PPS = (CHASE_SPEED_KMPH * 1000.0 / 60.0 / 60.0 * PIXEL_PER_METER)

# 전투 무빙 속도 (약간 느림 or 비슷함)
BATTLE_SPEED_KMPH = 10.0
BATTLE_SPEED_PPS = (BATTLE_SPEED_KMPH * 1000.0 / 60.0 / 60.0 * PIXEL_PER_METER)

# 애니메이션 속도
TIME_PER_FRAME = 0.2
FRAMES_PER_SECOND = 1.0 / TIME_PER_FRAME

# 넉백 관련
HIT_DURATION_SEC = 0.5
DEATH_DURATION_SEC = 1.0
KNOCKBACK_SPEED_PPS = 200.0
DEATH_KNOCKBACK_SPEED_PPS = 200.0

# 💖 [추가] 거리 기준 상수 (300 픽셀)
COMBAT_RANGE = 300.0
COMBAT_RANGE_SQ = COMBAT_RANGE ** 2


# --------------------------------------------------------------------------------
# 이벤트 함수
# --------------------------------------------------------------------------------
def close_range(e):
    return e[0] == 'CLOSE_RANGE'


def long_range(e):
    return e[0] == 'LONG_RANGE'


def hit_by_sword(e):
    return e[0] == 'HIT_BY_SWORD'


def death_blow(e):
    return e[0] == 'DEATH_BLOW'


def timeout(e):
    return e[0] == 'TIMEOUT'


# --------------------------------------------------------------------------------
# 상태 클래스: Chase (멀 때 -> 무조건 추적)
# --------------------------------------------------------------------------------
class Chase:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.enemy.frame = 0.0

    def exit(self, e):
        pass

    def do(self):
        # 1. 플레이어 방향 벡터 계산
        dx = self.enemy.player.x - self.enemy.x
        dy = self.enemy.player.y - self.enemy.y
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist > 0:
            dx /= dist
            dy /= dist

        # 2. 플레이어 쪽으로 이동
        self.enemy.x += dx * CHASE_SPEED_PPS * game_framework.frame_time
        self.enemy.y += dy * CHASE_SPEED_PPS * game_framework.frame_time

        # 3. 애니메이션 및 방향 처리
        self.enemy.update_animation_direction()
        self.enemy.update_frame()

    def draw(self, camera):
        self.enemy.draw_sprite(self.enemy.anim_direction, camera)


# --------------------------------------------------------------------------------
# 상태 클래스: BattleMove (가까울 때 -> 무빙)
# --------------------------------------------------------------------------------
class BattleMove:
    def __init__(self, enemy):
        self.enemy = enemy
        self.move_timer = 0.0
        self.dir_x = 0.0
        self.dir_y = 0.0

    def enter(self, e):
        self.enemy.frame = 0.0
        self.set_random_direction()

    def exit(self, e):
        pass

    def set_random_direction(self):
        # -1.0 ~ 1.0 사이의 랜덤 벡터
        self.dir_x = random.uniform(-1.0, 1.0)
        self.dir_y = random.uniform(-1.0, 1.0)
        # 정규화 (일정한 속도를 위해)
        mag = math.sqrt(self.dir_x ** 2 + self.dir_y ** 2)
        if mag > 0:
            self.dir_x /= mag
            self.dir_y /= mag

    def do(self):
        # 1. 일정 시간(0.5 ~ 1.5초)마다 방향 전환
        self.move_timer += game_framework.frame_time
        if self.move_timer > random.uniform(0.5, 1.5):
            self.set_random_direction()
            self.move_timer = 0.0

        # 2. 이동 (랜덤 방향)
        self.enemy.x += self.dir_x * BATTLE_SPEED_PPS * game_framework.frame_time
        self.enemy.y += self.dir_y * BATTLE_SPEED_PPS * game_framework.frame_time

        # 3. 애니메이션 및 방향 처리 (이동 방향이 아니라 플레이어를 바라보는 방향 기준)
        self.enemy.update_animation_direction()
        self.enemy.update_frame()

    def draw(self, camera):
        self.enemy.draw_sprite(self.enemy.anim_direction, camera)


# --------------------------------------------------------------------------------
# 상태 클래스: Hit, Death (기존 유지)
# --------------------------------------------------------------------------------
class Hit:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.timer = 0.0
        self.enemy.frame = 0.0
        if self.enemy.knockback_dir_x > 0:
            self.enemy.anim_flip = ''
        else:
            self.enemy.anim_flip = 'h'

    def exit(self, e):
        pass

    def do(self):
        self.enemy.x += self.enemy.knockback_dir_x * KNOCKBACK_SPEED_PPS * game_framework.frame_time
        self.enemy.y += self.enemy.knockback_dir_y * KNOCKBACK_SPEED_PPS * game_framework.frame_time
        self.timer += game_framework.frame_time
        if self.timer > HIT_DURATION_SEC:
            self.enemy.state_machine.handle_state_event(('TIMEOUT', None))

    def draw(self, camera):
        self.enemy.draw_sprite('Hit', camera)


class Death:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.timer = 0.0
        self.enemy.frame = 0.0
        if self.enemy.knockback_dir_x > 0:
            self.enemy.anim_flip = ''
        else:
            self.enemy.anim_flip = 'h'

    def exit(self, e):
        pass

    def do(self):
        data = self.enemy.sprite_data['Death']
        if self.enemy.frame < data['frames'] - 1:
            self.enemy.x += self.enemy.knockback_dir_x * DEATH_KNOCKBACK_SPEED_PPS * game_framework.frame_time
            self.enemy.y += self.enemy.knockback_dir_y * DEATH_KNOCKBACK_SPEED_PPS * game_framework.frame_time
            fps = data['frames'] / DEATH_DURATION_SEC
            self.enemy.frame += fps * game_framework.frame_time
        else:
            self.enemy.frame = data['frames'] - 1

        self.timer += game_framework.frame_time
        if self.timer > DEATH_DURATION_SEC:
            game_world.remove_object(self.enemy)

    def draw(self, camera):
        self.enemy.draw_sprite('Death', camera)


# --------------------------------------------------------------------------------
# Enemy1 메인 클래스
# --------------------------------------------------------------------------------
class Enemy1:
    images = None
    sprite_data = None

    def load_resources(self):
        if Enemy1.images is None:
            Enemy1.images = {}
            Enemy1.sprite_data = {}
            # Idle은 삭제되었지만 리소스는 Walk나 다른 곳에서 재활용 가능
            # 여기서는 Walk 리소스를 Chase/BattleMove가 공통으로 사용

            Enemy1.images['Walk_F'] = load_image('./Assets/Enemy/E1_WALK_F_16x24x6.png')
            Enemy1.sprite_data['Walk_F'] = {'w': 16, 'h': 24, 'frames': 6}

            Enemy1.images['Walk_B'] = load_image('./Assets/Enemy/E1_WALK_B_15x24x7.png')
            Enemy1.sprite_data['Walk_B'] = {'w': 15, 'h': 24, 'frames': 7}

            Enemy1.images['Hit'] = load_image('./Assets/Enemy/E1_HIT_15x23x1.png')
            Enemy1.sprite_data['Hit'] = {'w': 15, 'h': 23, 'frames': 1}

            Enemy1.images['Death'] = load_image('./Assets/Enemy/E1_DEATH_23x23x4.png')
            Enemy1.sprite_data['Death'] = {'w': 23, 'h': 23, 'frames': 4}

            if 'Shadow' not in Enemy1.images:
                Enemy1.images['Shadow'] = load_image('./Assets/Shadow/EShadow.png')

    def __init__(self):
        self.x = random.randint(800, 1200)
        self.y = random.randint(400, 800)
        self.hp = 3
        self.frame = 0.0
        self.draw_scale = 2.5
        self.anim_direction = 'Walk_F'
        self.anim_flip = ''

        # 감지 범위 (이 범위 안에서는 총을 쏨)
        self.detection_range_sq = 600 ** 2

        self.load_resources()
        self.player = play_mode.player

        self.knockback_dir_x = 0.0
        self.knockback_dir_y = 0.0

        # 총 생성
        self.gun = Gun(self)
        self.attack_timer = 0.0

        # 💖 [수정] 상태 정의: Chase, BattleMove, Hit, Death
        self.CHASE = Chase(self)
        self.BATTLE_MOVE = BattleMove(self)  # (구 IDLE 대체)
        self.HIT = Hit(self)
        self.DEATH = Death(self)

        self.state_machine = StateMachine(
            self.CHASE,  # 시작은 추적 상태로
            {
                self.CHASE: {
                    close_range: self.BATTLE_MOVE,  # 가까워지면 무빙
                    hit_by_sword: self.HIT,
                    death_blow: self.DEATH
                },
                self.BATTLE_MOVE: {
                    long_range: self.CHASE,  # 멀어지면 다시 추적
                    hit_by_sword: self.HIT,
                    death_blow: self.DEATH
                },
                self.HIT: {
                    timeout: self.CHASE  # 히트 후 다시 추적부터 시작 (거리 체크 후 바로 전환됨)
                },
                self.DEATH: {}
            }
        )

    # 헬퍼 함수: 플레이어 위치에 따른 방향 설정 (공통 사용)
    def update_animation_direction(self):
        if self.x < self.player.x:
            self.anim_flip = 'h'
        else:
            self.anim_flip = ''

        if self.y > self.player.y:
            self.anim_direction = 'Walk_F'
        else:
            self.anim_direction = 'Walk_B'

    # 헬퍼 함수: 프레임 업데이트 (공통 사용)
    def update_frame(self):
        data = self.sprite_data[self.anim_direction]
        self.frame = (self.frame + FRAMES_PER_SECOND * game_framework.frame_time) % data['frames']

    def draw_sprite(self, image_key, camera):
        if image_key not in self.images: return
        data = self.sprite_data[image_key]
        image = self.images[image_key]
        image.clip_composite_draw(
            int(self.frame) * data['w'], 0, data['w'], data['h'],
            0, self.anim_flip,
            self.x - camera.world_l, self.y - camera.world_b,
            data['w'] * self.draw_scale, data['h'] * self.draw_scale
        )

    def update(self):
        # 1. 플레이어와의 거리 계산
        dist_sq = (self.player.x - self.x) ** 2 + (self.player.y - self.y) ** 2

        # 2. 💖 거리 기반 상태 전환 이벤트 발생 (Hit/Death 아닐 때만)
        if self.state_machine.cur_state not in (self.HIT, self.DEATH):
            if dist_sq <= COMBAT_RANGE_SQ:  # 300px 이내
                self.state_machine.handle_state_event(('CLOSE_RANGE', None))
            else:  # 300px 밖
                self.state_machine.handle_state_event(('LONG_RANGE', None))

            # 3. 공격 로직 (감지 범위 내라면 발사)
            if dist_sq < self.detection_range_sq:
                self.attack_timer += game_framework.frame_time
                if self.attack_timer > 1.5:
                    self.gun.fire()
                    self.attack_timer = 0.0

        self.state_machine.update()
        self.gun.update()

    def draw(self, camera):
        if 'Shadow' in self.images:
            self.images['Shadow'].draw(self.x - camera.world_l, self.y - camera.world_b  - 33,40,20)
        self.state_machine.draw(camera)
        self.gun.draw(camera)

        # 디버그: 전투 범위(빨간색), 감지 범위(초록색)
        # draw_rectangle(...) # 필요시 추가

    def get_bb(self):
        w_half = (15 * self.draw_scale) / 2
        h_half = (23 * self.draw_scale) / 2
        return self.x - w_half, self.y - h_half, self.x + w_half, self.y + h_half

    def handle_collision(self, group, other):
        if group == 'sword_bullet:enemy':
            if self.state_machine.cur_state in (self.HIT, self.DEATH): return

            # 데미지 처리
            self.hp -= 1

            # 넉백 방향 계산 (투사체 진행 방향)
            self.knockback_dir_x = other.dx
            self.knockback_dir_y = other.dy
            # 정규화
            dist = math.sqrt(self.knockback_dir_x ** 2 + self.knockback_dir_y ** 2)
            if dist > 0:
                self.knockback_dir_x /= dist
                self.knockback_dir_y /= dist

            # 상태 전환
            if self.hp <= 0:
                self.state_machine.handle_state_event(('DEATH_BLOW', None))
            else:
                self.state_machine.handle_state_event(('HIT_BY_SWORD', None))
            return  # 처리 완료
        if group == 'sword:enemy':
            if self.state_machine.cur_state in (self.HIT, self.DEATH): return
            if other.state_machine.cur_state == other.COOLDOWN: return

            if other.state_machine.cur_state == other.SWING:
                self.hp -= 1
                dx = self.x - other.player.x
                dy = self.y - other.player.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist > 0:
                    self.knockback_dir_x = dx / dist
                    self.knockback_dir_y = dy / dist
                else:
                    self.knockback_dir_x = 1.0
                    self.knockback_dir_y = 0.0

                if self.hp <= 0:
                    self.state_machine.handle_state_event(('DEATH_BLOW', None))
                else:
                    self.state_machine.handle_state_event(('HIT_BY_SWORD', None))

    def handle_event(self, event):
        pass