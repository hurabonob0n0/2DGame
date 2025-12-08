from pico2d import load_image


class Map:
    def __init__(self):
        # 1. 생성된 배경 이미지 로드
        self.image = load_image('background.png')
        self.w = self.image.w
        self.h = self.image.h

    def update(self):
        # 배경은 움직이지 않으므로 업데이트 로직 불필요
        pass

    def draw(self, camera):
        # 💖 [핵심 로직] 무한 타일링 렌더링

        # 1. 카메라가 비추는 영역(ViewPort)이 월드 좌표계의 어디인지 파악
        # (예: world_l이 2500이면, 1920짜리 이미지의 2번째 장(index 1)부터 그려야 함)

        # 그리기를 시작할 타일 인덱스 (왼쪽, 아래)
        start_x = int(camera.world_l // self.w)
        start_y = int(camera.world_b // self.h)

        # 그리기를 끝낼 타일 인덱스 (오른쪽, 위)
        # (+1을 해주는 이유는 화면 걸쳐있는 타일까지 그려야 하므로)
        end_x = int((camera.world_l + camera.canvas_width) // self.w) + 1
        end_y = int((camera.world_b + camera.canvas_height) // self.h) + 1

        # 2. 필요한 타일만 반복해서 그림
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                # 월드 좌표상의 그릴 위치
                world_pos_x = x * self.w
                world_pos_y = y * self.h

                # 화면 좌표로 변환하여 그리기 (draw_to_origin은 좌측하단 기준)
                self.image.draw_to_origin(
                    world_pos_x - camera.world_l,
                    world_pos_y - camera.world_b,
                    self.w,
                    self.h
                )