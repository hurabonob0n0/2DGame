import random
import math
import game_framework
import game_world

from pico2d import *

# from arrow import Arrow # 💖 [삭제] Arrow를 더 이상 사용하지 않음

# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 25.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 100
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]

    # 1. __init__ 수정
    def __init__(self):
        self.x, self.y = 1920 // 2, 1080 // 2
        self.load_images()
        self.frame = random.randint(0, 9)
        self.face_dir = random.choice([-1, 1])  # (draw에서 사용)

        # 💖 [주석 처리] Arrow 생성 및 추가 제거
        # self.arrow = Arrow()
        # game_world.add_object(self.arrow, 2)

        # 💖 [주석 처리] 하트 경로 변수 제거
        # self.heart_t = 0.0
        # self.heart_scale = 15
        # self.heart_center_x, self.heart_center_y = self.x, self.y
        # self.heart_steps = 100.0

        # 💖 [주석 처리] 첫 번째 지점 설정 제거
        # next_x, next_y = self.get_next_heart_point()
        # self.arrow.x, self.arrow.y = next_x, next_y

        # 💖 [주석 처리] 이동 관련 변수 제거
        # self.t = 0.0
        # self.sx, self.sy = self.x, self.y
        # self.distance = math.sqrt((self.arrow.x - self.x) ** 2 + (self.arrow.y - self.y) ** 2)
        # if self.distance == 0: self.distance = 0.01

    # 2. 💖 하트 경로 계산 메서드 (남아있지만 호출되지 않음)
    def get_next_heart_point(self):
        """ 하트 방정식에 따라 다음 목표 지점을 계산하고 반환합니다. """

        # turtle 예제의 하트 방정식
        t_rad = self.heart_t
        heart_x = 16 * (math.sin(t_rad) ** 3)
        heart_y = 13 * math.cos(t_rad) - 5 * math.cos(2 * t_rad) - 2 * math.cos(3 * t_rad) - math.cos(4 * t_rad)

        # 다음 t 값 계산
        self.heart_t += (2 * math.pi) / self.heart_steps
        if self.heart_t > 2 * math.pi:  # 한 바퀴 돌면 초기화
            self.heart_t -= 2 * math.pi

        # 최종 좌표 반환 (중심 + 스케일 적용)
        final_x = self.heart_center_x + heart_x * self.heart_scale
        final_y = self.heart_center_y + heart_y * self.heart_scale
        return final_x, final_y

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50

    # 3. update 메서드 수정
    def update(self):
        # 💖 프레임 애니메이션만 남기고 이동 로직 모두 제거
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION

        # 💖 [주석 처리] 이동 로직
        # if self.t < 1.0:
        #     self.t += RUN_SPEED_PPS * game_framework.frame_time / self.distance
        #     self.x = self.sx * (1.0 - self.t) + (self.arrow.x * self.t)
        #     self.y = self.sy * (1.0 - self.t) + (self.arrow.y * self.t)
        # else:
        #     self.x, self.y = self.arrow.x, self.arrow.y
        #     self.t = 0.0
        #     next_x, next_y = self.get_next_heart_point()
        #     self.arrow.x, self.arrow.y = next_x, next_y
        #     self.sx, self.sy = self.x, self.y
        #     self.distance = math.sqrt((self.arrow.x - self.x) ** 2 + (self.arrow.y - self.y) ** 2)
        #     if self.distance == 0: self.distance = 0.01

    # 💖💖💖 [수정된 부분] 💖💖💖
    def draw(self, camera):  # 💖 [수정] camera 매개변수 추가
        # 💖 [수정] Arrow.x 대신 self.face_dir을 기준으로 방향 결정
        if self.face_dir == -1:
            Zombie.images['Walk'][int(self.frame)].composite_draw(0, 'h', self.x - camera.world_l,
                                                                  self.y - camera.world_b, 100, 100)
        else:
            Zombie.images['Walk'][int(self.frame)].draw(self.x - camera.world_l, self.y - camera.world_b, 100, 100)

        # 💖 [수정] 디버깅용 BBox 그리기
        l, b, r, t = self.get_bb()
        draw_rectangle(l - camera.world_l, b - camera.world_b, r - camera.world_l, t - camera.world_b)

    # 💖💖💖 [수정 완료] 💖💖💖

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        pass