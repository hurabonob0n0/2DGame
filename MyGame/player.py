import math
from pico2d import load_image, draw_rectangle, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_RIGHT  # 💖 우클릭 상수 추가
from sdl2 import SDL_KEYDOWN, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_UP, SDLK_DOWN, SDL_MOUSEMOTION, SDLK_a, SDLK_d, \
    SDLK_w, SDLK_s

import game_world
import game_framework

from state_machine import StateMachine
from sword import Sword


# --------------------------------------------------------------------------------
# 이벤트 함수
# --------------------------------------------------------------------------------

def event_stop(e):
    return e[0] == 'STOP'


def event_run(e):
    return e[0] == 'RUN'


# 💖 [추가] 구르기 이벤트 함수 (우클릭 감지)
# 주의: 쿨타임 체크는 Player.handle_event나 update에서 선행되어야 함, 여기서는 입력만 확인
def event_roll(e):
    return e[0] == 'INPUT' and e[1].type == SDL_MOUSEBUTTONDOWN and e[1].button == SDL_BUTTON_RIGHT


def event_roll_finish_idle(e):
    return e[0] == 'ROLL_FINISH_IDLE'

def event_roll_finish_run(e):
    return e[0] == 'ROLL_FINISH_RUN'


# --------------------------------------------------------------------------------
# 상수
# --------------------------------------------------------------------------------
PIXEL_PER_METER = (10.0 / 0.3)
RUN_SPEED_KMPH = 30.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
WALK_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.75
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 8


# --------------------------------------------------------------------------------
# 💖 [추가] Roll 상태 클래스
# --------------------------------------------------------------------------------
class Roll:
    def __init__(self, player):
        self.player = player
        self.roll_dir_x = 0.0
        self.roll_dir_y = 0.0
        # 9프레임 애니메이션
        self.total_frames = 9.0

        # 💖 애니메이션 속도: 구르기는 좀 더 빠르게 재생 (예: 0.5초 안에 9프레임 소화)
        self.duration = 0.5
        self.fps = self.total_frames / self.duration

    def enter(self, e):
        self.player.frame = 0.0

        # 💖 1. 구르는 방향 고정 (클릭 순간의 마우스 방향)
        # (update_mouse_direction은 애니메이션 방향만 정하므로, 실제 이동 벡터를 계산해야 함)
        mx, my = self.player.mouse_world_x, self.player.mouse_world_y
        dx = mx - self.player.x
        dy = my - self.player.y
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist > 0:
            self.roll_dir_x = dx / dist
            self.roll_dir_y = dy / dist
        else:
            self.roll_dir_x = 1.0  # 예외 처리
            self.roll_dir_y = 0.0

        # 💖 2. 구르는 방향에 맞춰 애니메이션 방향('F', 'B' 등) 설정
        # (기존 update_mouse_direction 로직을 재활용하되, 마우스 위치가 아닌 '고정된 방향' 기준이어야 하지만,
        #  여기서는 enter 시점의 마우스 위치가 곧 이동 방향이므로 한 번 호출해주면 됨)
        self.player.update_mouse_direction()

    def exit(self, e):
        # 💖 구르기가 끝나면 쿨타임 시작 (0.5초)
        self.player.roll_cooldown = 0.5

    def do(self):
        # 1. 프레임 진행
        self.player.frame += self.fps * game_framework.frame_time

        # 💖 2. 애니메이션 종료 체크
        if self.player.frame >= self.total_frames:
            # 마지막 프레임 고정 후 종료
            self.player.frame = self.total_frames - 1
            # 💖 [수정] 이동 키가 눌려있는지 확인하여 이벤트를 분기합니다.
            if self.player.xdir != 0 or self.player.ydir != 0:
                self.player.state_machine.handle_state_event(('ROLL_FINISH_RUN', None))
            else:
                self.player.state_machine.handle_state_event(('ROLL_FINISH_IDLE', None))
            return

        # 💖 3. 가변 속도 계산 (Lerp)
        # 프레임 인덱스 (0 ~ 8.xx)
        cur_idx = int(self.player.frame)

        # 기본 걷기 속도
        base_speed = WALK_SPEED_PPS
        current_speed = 0.0

        # 중간 프레임(4)을 기준으로 속도 변화
        if cur_idx <= 4:
            # 0~4 프레임: 0.5배 -> 2.5배 가속
            # 진행률 (0.0 ~ 1.0)
            alpha = cur_idx / 4.0
            speed_mult = (1.0 - alpha) * 0.5 + alpha * 2.5
        else:
            # 5~8 프레임: 2.5배 -> 0.5배 감속
            # 진행률 (0.0 ~ 1.0)
            alpha = (cur_idx - 4) / 4.0
            speed_mult = (1.0 - alpha) * 2.5 + alpha * 0.5

        current_speed = base_speed * speed_mult

        # 4. 이동 적용
        self.player.x += self.roll_dir_x * current_speed * game_framework.frame_time
        self.player.y += self.roll_dir_y * current_speed * game_framework.frame_time

    def draw(self, camera):
        self.player.draw_sprite('Roll', camera)


# --------------------------------------------------------------------------------
# 기존 상태 클래스 (Idle, Walk) - 변경 없음 (생략)
# --------------------------------------------------------------------------------
class Idle:
    def __init__(self, player):
        self.player = player

    def enter(self, e): pass

    def exit(self, e): pass

    def do(self):
        self.player.update_mouse_direction()
        self.player.update_animation_frame('Idle')

    def draw(self, camera):
        self.player.draw_sprite('Idle', camera)


class Walk:
    def __init__(self, player):
        self.player = player

    def enter(self, e): pass

    def exit(self, e): pass

    def do(self):
        self.player.update_mouse_direction()
        self.player.update_animation_frame('Walk')
        move_x = self.player.xdir
        move_y = self.player.ydir
        magnitude = math.sqrt(move_x ** 2 + move_y ** 2)
        if magnitude > 0:
            move_x /= magnitude
            move_y /= magnitude
        self.player.x += move_x * WALK_SPEED_PPS * game_framework.frame_time
        self.player.y += move_y * WALK_SPEED_PPS * game_framework.frame_time

    def draw(self, camera):
        self.player.draw_sprite('Walk', camera)


# --------------------------------------------------------------------------------
# 플레이어 메인 클래스
# --------------------------------------------------------------------------------

class Player:
    def __init__(self):
        self.x, self.y = 1920 // 2, 1080 // 2
        self.frame = 0.0
        self.xdir, self.ydir = 0, 0
        self.mouse_x, self.mouse_y = 0, 0
        self.mouse_world_x, self.mouse_world_y = 0, 0
        self.draw_scale = 2.5
        self.anim_direction = 'F'
        self.anim_flip = ''

        # 💖 [추가] 구르기 쿨타임 타이머
        self.roll_cooldown = 0.0

        self.images = {}
        self.sprite_data = {}
        self.load_resources()

        # 상태 인스턴스
        self.IDLE = Idle(self)
        self.WALK = Walk(self)
        self.ROLL = Roll(self)  # 💖 [추가]

        # 💖 [수정] 상태 머신 전환 규칙
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    event_run: self.WALK,
                    event_roll: self.ROLL
                },
                self.WALK: {
                    event_stop: self.IDLE,
                    event_roll: self.ROLL
                },
                self.ROLL: {
                    # 💖 [수정] 상황에 따라 두 갈래로 나뉩니다.
                    event_roll_finish_idle: self.IDLE,  # 키 입력 없으면 Idle로
                    event_roll_finish_run: self.WALK  # 키 입력 있으면 바로 Walk로
                }
            }
        )

        self.sword = Sword(self)
        game_world.add_object(self.sword, 1)

    def load_resources(self):
        self.images = {'Idle': {}, 'Walk': {}, 'Roll': {}}  # 💖 Roll 추가
        self.sprite_data = {'Idle': {}, 'Walk': {}, 'Roll': {}}  # 💖 Roll 추가

        # --- IDLE & WALK (기존 코드 유지) ---
        # (기존 경로 유지...)
        self.images['Idle']['F'] = load_image('./Assets/Player/PLAYER_IDLE_F_16X23X4.png')
        self.sprite_data['Idle']['F'] = {'w': 16, 'h': 23, 'frames': 4}
        self.images['Idle']['B'] = load_image('./Assets/Player/PLAYER_IDLE_B_12X23X4.png')
        self.sprite_data['Idle']['B'] = {'w': 12, 'h': 23, 'frames': 4}
        self.images['Idle']['RF'] = load_image('./Assets/Player/PLAYER_IDLE_RF_18X23X4.png')
        self.sprite_data['Idle']['RF'] = {'w': 18, 'h': 23, 'frames': 4}
        self.images['Idle']['RB'] = load_image('./Assets/Player/PLAYER_IDLE_RB_15X23X4.png')
        self.sprite_data['Idle']['RB'] = {'w': 15, 'h': 23, 'frames': 4}

        self.images['Walk']['F'] = load_image('./Assets/Player/PLAYER_WALK_F_14X30X3.png')
        self.sprite_data['Walk']['F'] = {'w': 14, 'h': 30, 'frames': 3}
        self.images['Walk']['B'] = load_image('./Assets/Player/PLAYER_WALK_B_14X23X3.png')
        self.sprite_data['Walk']['B'] = {'w': 14, 'h': 23, 'frames': 3}
        self.images['Walk']['RF'] = load_image('./Assets/Player/PLAYER_WALK_RF_17X25X3.png')
        self.sprite_data['Walk']['RF'] = {'w': 17, 'h': 25, 'frames': 3}
        self.images['Walk']['RB'] = load_image('./Assets/Player/PLAYER_WALK_RB_17X26X3.png')
        self.sprite_data['Walk']['RB'] = {'w': 17, 'h': 26, 'frames': 3}

        # 💖 [추가] ROLL 이미지 로드 (보내주신 파일명과 크기 반영) -----------------------

        # 1. PLAYER_ROLL_F_20X26X9.png
        self.images['Roll']['F'] = load_image('./Assets/Player/PLAYER_ROLL_F_20X26X9.png')
        self.sprite_data['Roll']['F'] = {'w': 20, 'h': 26, 'frames': 9}

        # 2. PLAYER_ROLL_B_23X27X9.png
        self.images['Roll']['B'] = load_image('./Assets/Player/PLAYER_ROLL_B_23X27X9.png')
        self.sprite_data['Roll']['B'] = {'w': 23, 'h': 27, 'frames': 9}

        # 3. PLAYER_ROLL_RF_21X24X9.png
        self.images['Roll']['RF'] = load_image('./Assets/Player/PLAYER_ROLL_RF_21X24X9.png')
        self.sprite_data['Roll']['RF'] = {'w': 21, 'h': 24, 'frames': 9}

        # 4. PLAYER_ROLL_RB_21X26X9.png
        self.images['Roll']['RB'] = load_image('./Assets/Player/PLAYER_ROLL_RB_21X26X9.png')
        self.sprite_data['Roll']['RB'] = {'w': 21, 'h': 26, 'frames': 9}

    def update_mouse_direction(self):
        # (기존 코드 유지)
        look_dir_x = self.mouse_world_x - self.x
        look_dir_y = self.mouse_world_y - self.y
        angle_rad = math.atan2(look_dir_y, look_dir_x)
        angle_deg = math.degrees(angle_rad)

        if -120.0 <= angle_deg < -60.0:  # 남(F)
            self.anim_direction = 'F';
            self.anim_flip = ''
        elif 60.0 <= angle_deg < 120.0:  # 북(B)
            self.anim_direction = 'B';
            self.anim_flip = ''
        elif -60.0 <= angle_deg < 0.0:  # 남동(RF)
            self.anim_direction = 'RF';
            self.anim_flip = ''
        elif 0.0 <= angle_deg < 60.0:  # 북동(RB)
            self.anim_direction = 'RB';
            self.anim_flip = ''
        elif -180.0 <= angle_deg < -120.0:  # 남서(RF + h)
            self.anim_direction = 'RF';
            self.anim_flip = 'h'
        else:  # 북서(RB + h)
            self.anim_direction = 'RB';
            self.anim_flip = 'h'

    def update_animation_frame(self, state_name):
        data = self.sprite_data[state_name][self.anim_direction]
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % data['frames']

    def draw_sprite(self, state_name, camera):
        data = self.sprite_data[state_name][self.anim_direction]
        image = self.images[state_name][self.anim_direction]
        image.clip_composite_draw(
            int(self.frame) * data['w'], 0, data['w'], data['h'],
            0, self.anim_flip,
            self.x - camera.world_l, self.y - camera.world_b,
            data['w'] * self.draw_scale, data['h'] * self.draw_scale
        )

    def update(self):
        # 💖 [추가] 쿨타임 감소
        if self.roll_cooldown > 0:
            self.roll_cooldown -= game_framework.frame_time

        self.state_machine.update()
        #self.sword.update()

    def handle_event(self, event):
        if event.type == SDL_MOUSEMOTION:
            self.mouse_x, self.mouse_y = event.x, 1080 - 1 - event.y

        # 💖 [추가] 우클릭(구르기) 처리
        # - 현재 상태가 ROLL이 아니고
        # - 쿨타임이 0 이하일 때만 이벤트를 넘겨줌
        if (event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_RIGHT):
            if self.state_machine.cur_state != self.ROLL and self.roll_cooldown <= 0:
                self.state_machine.handle_state_event(('INPUT', event))
                return  # 구르기가 실행되면 아래 이동 로직은 스킵

        # 기존 이동(WASD) 로직
        if event.key in (SDLK_a, SDLK_d, SDLK_w, SDLK_s):
            cur_xdir, cur_ydir = self.xdir, self.ydir
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_a:
                    self.xdir -= 1
                elif event.key == SDLK_d:
                    self.xdir += 1
                elif event.key == SDLK_w:
                    self.ydir += 1
                elif event.key == SDLK_s:
                    self.ydir -= 1
            elif event.type == SDL_KEYUP:
                if event.key == SDLK_a:
                    self.xdir += 1
                elif event.key == SDLK_d:
                    self.xdir -= 1
                elif event.key == SDLK_w:
                    self.ydir -= 1
                elif event.key == SDLK_s:
                    self.ydir += 1

            if cur_xdir != self.xdir or cur_ydir != self.ydir:
                if self.xdir == 0 and self.ydir == 0:
                    self.state_machine.handle_state_event(('STOP', None))
                else:
                    self.state_machine.handle_state_event(('RUN', None))

        self.sword.handle_event(event)

    def draw(self, camera):
        self.state_machine.draw(camera)
        self.sword.draw(camera)

        # 디버그용 (필요시 주석 해제)
        l, b, r, t = self.get_bb()
        draw_rectangle(l - camera.world_l, b - camera.world_b, r - camera.world_l, t - camera.world_b)

    def get_bb(self):
        return self.x - 15, self.y - 25, self.x + 15, self.y + 25

    def handle_collision(self, group, other):
        pass