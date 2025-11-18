import random
import math
import game_framework
import game_world
import play_mode  # 💖 [추가] 플레이어 객체(play_mode.player)를 참조하기 위해 import

from pico2d import *
from state_machine import StateMachine

# 💖 [추가] 속도 상수
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour (플레이어 추적 속도)
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# 💖 [추가] 무작위 이동 속도 (추적 속도보다 작게)
RANDOM_MOVE_SPEED_KMPH = 3.0
RANDOM_MOVE_SPEED_MPM = (RANDOM_MOVE_SPEED_KMPH * 1000.0 / 60.0)
RANDOM_MOVE_SPEED_MPS = (RANDOM_MOVE_SPEED_MPM / 60.0)
RANDOM_MOVE_SPEED_PPS = (RANDOM_MOVE_SPEED_MPS * PIXEL_PER_METER)

# 💖 [추가] 애니메이션 속도 (프레임당 0.2초)
TIME_PER_FRAME = 0.2
FRAMES_PER_SECOND = 1.0 / TIME_PER_FRAME  # == 5.0

# 💖 [추가] 상태 지속 시간 및 탐지 범위
HIT_DURATION_SEC = 0.5
DEATH_DURATION_SEC = 1.0
KNOCKBACK_SPEED_PPS = 200.0
DEATH_KNOCKBACK_SPEED_PPS = 200.0  # 💖 [추가] 죽었을 때 밀려나는 속도 (더 강하게)

# --------------------------------------------------------------------------------
# 💖 상태 변경을 위한 이벤트 함수
# --------------------------------------------------------------------------------
def player_in_range(e):
    return e[0] == 'PLAYER_IN_RANGE'


def player_out_of_range(e):
    return e[0] == 'PLAYER_OUT_OF_RANGE'


def timeout(e):
    return e[0] == 'TIMEOUT'


def hit_by_sword(e):
    return e[0] == 'HIT_BY_SWORD'


def death_blow(e):
    return e[0] == 'DEATH_BLOW'


# --------------------------------------------------------------------------------
# 💖 Enemy1 상태 클래스: Idle
# --------------------------------------------------------------------------------
class Idle:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.enemy.frame = 0.0
        # 💖 Idle 애니메이션은 프레임당 0.5초 (천천히)
        self.fps = 2.0  # (1.0 / 0.5)

    def exit(self, e):
        pass

    def do(self):
        # 💖 [추가] 플레이어 위치에 따라 좌우반전 결정
        if self.enemy.x < self.enemy.player.x:
            # 적이 플레이어 왼쪽에 (플레이어가 오른쪽에) 있으면
            self.enemy.anim_flip = 'h'  # 좌우반전
        else:
            self.enemy.anim_flip = ''  # 원본

        # (기존 애니메이션 프레임 업데이트)
        data = self.enemy.sprite_data['Idle']
        self.enemy.frame = (self.enemy.frame + self.fps * game_framework.frame_time) % data['frames']

    def draw(self, camera):
        self.enemy.draw_sprite('Idle', camera)


# --------------------------------------------------------------------------------
# 💖 Enemy1 상태 클래스: Walk
# --------------------------------------------------------------------------------
class Walk:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.enemy.frame = 0.0
        # 💖 [추가] 1초마다 무작위 방향 갱신
        self.random_move_timer = 1.0
        self.update_random_dir()

    def exit(self, e):
        pass

    def update_random_dir(self):
        # 💖 -1.0 ~ 1.0 사이의 무작위 방향 벡터 설정
        self.enemy.random_move_dir_x = random.uniform(-1.0, 1.0)
        self.enemy.random_move_dir_y = random.uniform(-1.0, 1.0)
        self.random_move_timer = 0.0  # 타이머 초기화

    def do(self):
        # 1. 💖 무작위 방향 갱신 (1초마다)
        self.random_move_timer += game_framework.frame_time
        if self.random_move_timer > 1.0:
            self.update_random_dir()

        # 2. 💖 플레이어 방향 벡터 (정규화)
        pdx = self.enemy.player.x - self.enemy.x
        pdy = self.enemy.player.y - self.enemy.y
        player_dist = math.sqrt(pdx ** 2 + pdy ** 2)

        if player_dist > 0:
            pdx /= player_dist
            pdy /= player_dist

        # 3. 💖 최종 이동 (플레이어 방향 + 무작위 방향)
        # (무작위 방향은 정규화하지 않아 속도에 영향을 줌)
        move_x = (pdx * RUN_SPEED_PPS) + (self.enemy.random_move_dir_x * RANDOM_MOVE_SPEED_PPS)
        move_y = (pdy * RUN_SPEED_PPS) + (self.enemy.random_move_dir_y * RANDOM_MOVE_SPEED_PPS)

        self.enemy.x += move_x * game_framework.frame_time
        self.enemy.y += move_y * game_framework.frame_time

        if self.enemy.x < self.enemy.player.x:
            # 적이 플레이어 왼쪽에 (플레이어가 오른쪽에) 있으면
            self.enemy.anim_flip = 'h'  # 좌우반전
        else:
            # 적이 플레이어 오른쪽에 (플레이어가 왼쪽에) 있으면
            self.enemy.anim_flip = ''  # 원본

            # 5. 💖 [수정] 애니메이션 방향 및 프레임 업데이트 (Y축 로직 반대로)
        if self.enemy.y > self.enemy.player.y:
            # 💖 [수정] 적이 플레이어보다 위에 있으면: F (앞모습)
            self.enemy.anim_direction = 'Walk_F'
        else:
            # 💖 [수정] 적이 플레이어보다 아래 있거나 같으면: B (뒷모습)
            self.enemy.anim_direction = 'Walk_B'

        data = self.enemy.sprite_data[self.enemy.anim_direction]
        # 💖 요청사항: 프레임당 0.2초 (== 5 FPS)
        self.enemy.frame = (self.enemy.frame + FRAMES_PER_SECOND * game_framework.frame_time) % data['frames']

        data = self.enemy.sprite_data[self.enemy.anim_direction]
        # 💖 요청사항: 프레임당 0.2초 (== 5 FPS)
        self.enemy.frame = (self.enemy.frame + FRAMES_PER_SECOND * game_framework.frame_time) % data['frames']

    def draw(self, camera):
        self.enemy.draw_sprite(self.enemy.anim_direction, camera)


# --------------------------------------------------------------------------------
# 💖 Enemy1 상태 클래스: Hit
# --------------------------------------------------------------------------------
class Hit:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.timer = 0.0
        self.enemy.frame = 0.0  # 'Hit'는 1프레임짜리

        # 💖 [추가] 넉백 방향에 따라 플립 결정
        if self.enemy.knockback_dir_x > 0:
            # 오른쪽으로 넉백 (플레이어가 왼쪽)
            self.enemy.anim_flip = ''
        else:
            # 왼쪽으로 넉백 (플레이어가 오른쪽)
            self.enemy.anim_flip = 'h'

    def exit(self, e):
        pass

    def do(self):
        # 1. 💖 넉백 적용
        self.enemy.x += self.enemy.knockback_dir_x * KNOCKBACK_SPEED_PPS * game_framework.frame_time
        self.enemy.y += self.enemy.knockback_dir_y * KNOCKBACK_SPEED_PPS * game_framework.frame_time

        # 2. 💖 0.3초가 지나면 TIMEOUT
        self.timer += game_framework.frame_time
        if self.timer > HIT_DURATION_SEC:
            self.enemy.state_machine.handle_state_event(('TIMEOUT', None))

    def draw(self, camera):
        self.enemy.draw_sprite('Hit', camera)


# --------------------------------------------------------------------------------
# 💖 Enemy1 상태 클래스: Death
# --------------------------------------------------------------------------------
class Death:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.timer = 0.0
        self.enemy.frame = 0.0

        # 💖 [추가] 넉백 방향에 따라 플립 결정
        if self.enemy.knockback_dir_x > 0:
            # 오른쪽으로 넉백 (플레이어가 왼쪽)
            self.enemy.anim_flip = ''
        else:
            # 왼쪽으로 넉백 (플레이어가 오른쪽)
            self.enemy.anim_flip = 'h'

    def exit(self, e):
        pass

    def do(self):
        # 💖 [수정] 애니메이션 데이터를 먼저 가져옵니다.
        data = self.enemy.sprite_data['Death']
        total_frames = data['frames']

        # 💖 [수정] 마지막 프레임에 도달했는지 확인 (0, 1, 2, 3 -> 마지막 프레임 인덱스는 3)
        is_animation_finished = (self.enemy.frame >= total_frames - 1)

        # 💖 [수정] 애니메이션이 끝나지 않았을 때만 넉백과 프레임 업데이트를 수행
        if not is_animation_finished:
            # 1. 💖 넉백 적용
            self.enemy.x += self.enemy.knockback_dir_x * DEATH_KNOCKBACK_SPEED_PPS * game_framework.frame_time
            self.enemy.y += self.enemy.knockback_dir_y * DEATH_KNOCKBACK_SPEED_PPS * game_framework.frame_time

            # 2. 💖 죽음 애니메이션 재생 (0.7초 동안)
            fps_for_death = total_frames / DEATH_DURATION_SEC
            self.enemy.frame = (self.enemy.frame + fps_for_death * game_framework.frame_time)

            # 💖 프레임이 끝나면 마지막 프레임으로 멈춤 (루프 방지)
            if self.enemy.frame >= total_frames:
                self.enemy.frame = total_frames - 1

        # 3. 💖 0.7초가 지나면 객체 제거 (이 타이머는 애니메이션과 별개로 항상 동작)
        self.timer += game_framework.frame_time
        if self.timer > DEATH_DURATION_SEC:
            game_world.remove_object(self.enemy)

    def draw(self, camera):
        self.enemy.draw_sprite('Death', camera)


# --------------------------------------------------------------------------------
# 💖 Enemy1 메인 클래스
# --------------------------------------------------------------------------------
class Enemy1:
    images = None
    sprite_data = None

    def load_resources(self):
        if Enemy1.images is None:
            Enemy1.images = {}
            Enemy1.sprite_data = {}

            # --- IDLE ---
            Enemy1.images['Idle'] = load_image('./Assets/Enemy/E1_IDLE_12x23x2.png')
            Enemy1.sprite_data['Idle'] = {'w': 12, 'h': 23, 'frames': 2}

            # --- WALK ---
            Enemy1.images['Walk_F'] = load_image('./Assets/Enemy/E1_WALK_F_16x24x6.png')
            Enemy1.sprite_data['Walk_F'] = {'w': 16, 'h': 24, 'frames': 6}

            Enemy1.images['Walk_B'] = load_image('./Assets/Enemy/E1_WALK_B_15x24x7.png')
            Enemy1.sprite_data['Walk_B'] = {'w': 15, 'h': 24, 'frames': 7}

            # --- HIT ---
            Enemy1.images['Hit'] = load_image('./Assets/Enemy/E1_HIT_15x23x1.png')
            Enemy1.sprite_data['Hit'] = {'w': 15, 'h': 23, 'frames': 1}

            # --- DEATH ---
            Enemy1.images['Death'] = load_image('./Assets/Enemy/E1_DEATH_23x23x4.png')
            Enemy1.sprite_data['Death'] = {'w': 23, 'h': 23, 'frames': 4}

    def __init__(self):
        # 💖 스폰 위치 (임시로 중앙 근처 무작위)
        self.x = random.randint(800, 1200)
        self.y = random.randint(400, 800)
        self.hp = 3
        self.frame = 0.0
        self.draw_scale = 2.5
        self.anim_direction = 'Walk_F'  # (Walk 상태에서 덮어쓸 임시값)
        self.anim_flip = ''  # 💖 [추가] 좌우반전 상태 ('h' 또는 '')

        detection_range = random.uniform(300.0, 600.0)
        self.detection_range_sq = detection_range ** 2

        self.load_resources()

        # 💖 [추가] 플레이어 참조
        self.player = play_mode.player

        # 💖 [추가] 이동 관련 변수
        self.random_move_dir_x = 0.0
        self.random_move_dir_y = 0.0
        self.knockback_dir_x = 0.0
        self.knockback_dir_y = 0.0

        # 💖 [추가] 상태 머신 정의
        self.IDLE = Idle(self)
        self.WALK = Walk(self)
        self.HIT = Hit(self)
        self.DEATH = Death(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    player_in_range: self.WALK,
                    hit_by_sword: self.HIT,
                    death_blow: self.DEATH
                },
                self.WALK: {
                    player_out_of_range: self.IDLE,
                    hit_by_sword: self.HIT,
                    death_blow: self.DEATH
                },
                self.HIT: {
                    timeout: self.IDLE
                },
                self.DEATH: {
                    # 💖 Death 상태에서는 다른 이벤트/전환 없음
                }
            }
        )

    def draw_sprite(self, image_key, camera):
        """ 헬퍼 함수: 현재 프레임과 상태에 맞는 스프라이트 그리기 """
        if image_key not in self.images: return  # (혹시 모를 오류 방지)

        data = self.sprite_data[image_key]
        image = self.images[image_key]

        # 💖 [수정] clip_draw -> clip_composite_draw
        image.clip_composite_draw(
            int(self.frame) * data['w'], 0, data['w'], data['h'],
            0, self.anim_flip,  # 💖 0, '' (또는 flip 값) 전달
            self.x - camera.world_l, self.y - camera.world_b,
            data['w'] * self.draw_scale, data['h'] * self.draw_scale
        )

    def update(self):
        # 💖 [추가] 플레이어와의 거리 계산
        dist_sq = (self.player.x - self.x) ** 2 + (self.player.y - self.y) ** 2

        # 💖 [추가] 거리에 따라 FSM 이벤트 발생
        if self.state_machine.cur_state not in (self.HIT, self.DEATH):
            if dist_sq < self.detection_range_sq:
                self.state_machine.handle_state_event(('PLAYER_IN_RANGE', None))
            else:
                self.state_machine.handle_state_event(('PLAYER_OUT_OF_RANGE', None))

        self.state_machine.update()

    def draw(self, camera):
        self.state_machine.draw(camera)
        # 💖 [추가] 디버깅용 BBox
        l, b, r, t = self.get_bb()
        draw_rectangle(l - camera.world_l, b - camera.world_b, r - camera.world_l, t - camera.world_b)

    def handle_event(self, event):
        pass  # Enemy1은 스스로 판단하므로 외부 이벤트는 받지 않음

    def get_bb(self):
        # 💖 스프라이트 크기 기반으로 BBox 설정 (Idle/Hit 기준)
        w_half = (15 * self.draw_scale) / 2
        h_half = (23 * self.draw_scale) / 2
        return self.x - w_half, self.y - h_half, self.x + w_half, self.y + h_half

    def handle_collision(self, group, other):
        # 💖 'other'는 충돌한 객체
        if group == 'sword:enemy':
            # 💖 [수정] 1. 이미 Hit 또는 Death 상태면 무시
            if self.state_machine.cur_state in (self.HIT, self.DEATH):
                return

            # 💖 [수정] 2. Sword가 Cooldown 상태면 무시
            if other.state_machine.cur_state == other.COOLDOWN:
                return

            # 💖 [수정] 3. Sword가 'SWING' 상태일 때만 데미지
            if other.state_machine.cur_state == other.SWING:
                self.hp -= 1

                # 💖 [수정] 넉백 방향 계산 (플레이어 -> 적)
                dx = self.x - other.player.x
                dy = self.y - other.player.y
                dist = math.sqrt(dx ** 2 + dy ** 2)

                if dist > 0:
                    self.knockback_dir_x = dx / dist
                    self.knockback_dir_y = dy / dist
                else:
                    self.knockback_dir_x = 1.0  # (혹시 모를 예외처리)
                    self.knockback_dir_y = 0.0

                # 💖 [수정] HP에 따라 상태 전이
                if self.hp <= 0:
                    self.state_machine.handle_state_event(('DEATH_BLOW', None))
                else:
                    self.state_machine.handle_state_event(('HIT_BY_SWORD', None))