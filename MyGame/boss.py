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
WALK_SPEED_KMPH = 60.0
WALK_SPEED_PPS = (WALK_SPEED_KMPH * 1000.0 / 60.0 / 60.0 * PIXEL_PER_METER)

# 돌진 속도 (빠름, 300)
DASH_SPEED_PPS = 900.0

# 공격 감지 거리 (이 거리 안으로 들어오면 패턴 시작)
ATTACK_RANGE = 800.0  # 적절히 조정


HP_BAR_Y_OFFSET = 450 # 화면 중앙에서 아래로 450px
HP_BAR_WIDTH = 1000   # (BossHPBAR.png의 대략적인 너비, 실제 파일 크기에 맞춰 조정 필요)
HP_BAR_HEIGHT = 100    # (게이지 높이)

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
        offsets = [-20, -10,0, 10, 20]
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

            if 'Shadow' not in Boss.images:
                Boss.images['Shadow'] = load_image('./Assets/Shadow/EShadow.png')

                # 💖 [수정] HP바 관련 이미지 2장 로드
            if 'HP_BAR_BG' not in Boss.images:
                Boss.images['HP_BAR_BG'] = load_image('./Assets/UI/BossHPBAR.png')
            if 'HP_BAR_FILL' not in Boss.images:
                Boss.images['HP_BAR_FILL'] = load_image('./Assets/UI/BossHPBARINSIDE.png')

    def __init__(self):
        self.x, self.y = 1000, 600
        self.hp = 20
        self.max_hp = 20  # 💖 최대 HP 저장
        self.draw_scale = 3.0
        self.frame = 0.0
        self.anim_flip = ''

        self.hit_timer = 0.0

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
        if self.hit_timer > 0:
            self.hit_timer -= game_framework.frame_time
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
        # 💖 [추가] 깜빡임 효과 (0.1초 간격으로 그리기 on/off)
        # HP바는 항상 보여야 하므로, 그림자와 본체만 깜빡이게 처리
        visible = True
        if self.hit_timer > 0:
            if int(self.hit_timer * 10) % 2 != 0:
                visible = False

        if visible:
            if 'Shadow' in self.images:
                # ... (기존 그림자 그리기 코드 유지) ...
                # (이전 대화의 그림자 로직 그대로 사용하세요)
                shadow = self.images['Shadow']
                shadow_y = self.y
                shadow_scale = 5.0
                if isinstance(self.state_machine.cur_state, Jump):
                    shadow_y = self.JUMP.base_y
                    height_diff = self.y - shadow_y
                    ratio = height_diff / self.JUMP.rise_height
                    current_scale_factor = (1.0 - ratio) * 1.0 + ratio * 0.5
                    shadow_scale = 2.0 * current_scale_factor  # 2.0배가 적당 (코드엔 5.0이라 되어있는데 2~3배 추천)

                shadow.draw(
                    self.x - camera.world_l,
                    shadow_y - camera.world_b - 100,  # 오프셋 조정 필요할 수 있음
                    shadow.w * shadow_scale,
                    shadow.h * shadow_scale
                )

            # 본체 그리기
            self.state_machine.draw(camera)

        # 💖 HP바는 깜빡이지 않고 항상 그림
        self.draw_hp_bar()

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

        # 💖 [추가] 플레이어와 부딪혔을 때 (보스는 데미지 안 입고 밀어내기만 함, 혹은 아무것도 안 함)
        if group == 'player:boss':
            return  # 보스 몸이 플레이어보다 강하므로 보스는 멀쩡함

        # 칼이나 검기에 맞았을 때
        if group == 'sword:enemy' or group == 'sword_bullet:enemy':
            # 💖 [추가] 무적 시간이면 데미지 무시 (연타 방지)
            if self.hit_timer > 0:
                return

            # sword:enemy 일 경우 Swing 상태 확인
            if group == 'sword:enemy':
                if other.state_machine.cur_state != other.SWING:
                    return

            self.hp -= 1
            # 💖 [추가] 피격 시 1초간 무적/깜빡임 설정
            self.hit_timer = 1.0

            if self.hp <= 0:
                self.state_machine.handle_state_event(('DEATH', None))

    def draw_hp_bar(self):
        # 화면 중앙 하단 위치 계산
        screen_center_x = 1920 // 2
        screen_center_y = 1080 // 2

        # 바의 중심 위치 (화면 중앙에서 아래로 450px)
        bar_x = screen_center_x
        bar_y = screen_center_y - 450

        # 1. HP바 배경(틀) 그리기
        if 'HP_BAR_BG' in self.images:
            bg_img = self.images['HP_BAR_BG']
            bg_img.draw(bar_x, bar_y)

            # 💖 [핵심] 배경 이미지 크기 가져오기
            bg_w = bg_img.w
            bg_h = bg_img.h
        else:
            bg_w, bg_h = 800, 20  # 기본값

        # 2. HP 게이지(내용물) 그리기
        if 'HP_BAR_FILL' in self.images:
            fill_img = self.images['HP_BAR_FILL']

            # HP 비율 계산 (0.0 ~ 1.0)
            hp_ratio = self.hp / self.max_hp
            if hp_ratio < 0: hp_ratio = 0

            # 💖 [핵심] "내용물이 그려질 최대 영역" 크기 정의
            # 배경 이미지(껍데기) 크기에서 테두리 두께만큼 뺍니다.
            # (좌우 10px, 상하 5px 씩 뺀다고 가정 -> 전체 너비 -20, 높이 -10)
            # 이 수치만 조절하면 껍데기 안에 딱 맞게 들어갑니다.
            inner_max_w = bg_w - 15
            inner_max_h = bg_h - 15

            # 현재 HP에 따른 실제 너비 계산
            current_w = int(inner_max_w * hp_ratio)

            # 💖 그리기 시작 위치 (좌측 하단) 계산
            # 중심(bar_x)에서 '최대 너비의 절반'만큼 왼쪽으로 이동하면
            # 배경의 테두리 안쪽 시작점과 정확히 일치합니다.
            draw_x = bar_x - (inner_max_w // 2)
            draw_y = bar_y - (inner_max_h // 2)

            # 잘라서 그리기 (왼쪽 정렬 효과)
            if current_w > 0:
                fill_img.clip_draw_to_origin(
                    0, 0, current_w, fill_img.h,  # 원본 자를 영역
                    draw_x, draw_y,  # 화면 그릴 위치
                    current_w, inner_max_h  # 화면 그릴 크기 (높이도 inner_max_h로 맞춤)
                )