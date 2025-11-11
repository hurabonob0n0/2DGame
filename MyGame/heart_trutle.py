import turtle
import random
import math  # 하트 계산을 위해 math 모듈을 가져옵니다.


def stop():
    turtle.bye()


def prepare_turtle_canvas():
    turtle.setup(1024, 768)
    turtle.bgcolor(0.2, 0.2, 0.2)
    turtle.penup()
    turtle.hideturtle()
    turtle.shape('arrow')
    turtle.shapesize(2)
    turtle.pensize(5)
    turtle.color(1, 0, 0)
    turtle.speed(100)  # 축 그리는 속도
    turtle.goto(-500, 0)
    turtle.pendown()
    turtle.goto(480, 0)
    turtle.stamp()
    turtle.penup()
    turtle.goto(0, -360)
    turtle.pendown()
    turtle.goto(0, 360)
    turtle.setheading(90)
    turtle.stamp()
    turtle.penup()
    turtle.home()

    turtle.shape('circle')
    turtle.pensize(1)
    turtle.color(0, 0, 0)
    turtle.speed(50)  # 기본 속도 설정

    turtle.onkey(stop, 'Escape')
    turtle.listen()


def draw_big_point(p):
    turtle.goto(p)
    turtle.color(0.8, 0.9, 0)
    turtle.dot(15)
    turtle.write('     ' + str(p))


def draw_point(p):
    turtle.goto(p)
    turtle.dot(5, 1, random.random(), random.random())


def draw_line(p1, p2):
    # 이 함수는 하트 그리기에는 사용되지 않지만, 원본 코드로 남겨둡니다.
    draw_big_point(p1)

    draw_big_point(p2)
    x1, y1 = p1
    x2, y2 = p2
    for i in range(0, 100 + 1, 4):
        t = i / 100
        x = (1 - t) * x1 + t * x2
        y = (1 - t) * y1 + t * y2
        draw_point((x, y))

    draw_point(p2)


# 하트를 그리는 새 함수 (점으로 찍도록 수정)
def draw_heart():
    turtle.penup()
    # draw_point 함수가 자체적으로 색상을 랜덤으로 설정하므로
    # turtle.color(1, 0, 0) 설정은 무시됩니다.
    # turtle.pensize(2) 설정도 dot을 사용하므로 무시됩니다.
    turtle.speed(0)  # 하트 그리는 속도 설정 (0이 가장 빠름, 10은 적당히 빠름)

    scale = 15  # 하트 크기 조절

    # t = 0 일 때의 시작점으로 이동 (pen is up)
    t = 0
    x = 16 * (math.sin(t) ** 3)
    y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)

    # draw_point 함수가 goto와 dot을 모두 처리합니다.
    # turtle.goto(x * scale, y * scale)
    # turtle.pendown() # -> 필요 없음

    # 0부터 2*pi 까지 t 값을 증가시키며 하트를 그립니다.
    steps = 100  # 360단계로 나누어 부드럽게 그립니다.
    for i in range(0, steps + 1):  # 0부터 시작해서 첫 점도 찍도록 합니다.
        # t 값을 라디안으로 계산
        t = (i / steps) * 2 * math.pi

        # 매개변수 방정식
        x = 16 * (math.sin(t) ** 3)
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)

        # 계산된 좌표로 이동 (크기 조절) 및 점 찍기
        draw_point((x * scale, y * scale))

    turtle.penup()


prepare_turtle_canvas()

# --- 여기를 채웠습니다 ---
# p1 = 100, 100
# p2 = 300, 200
# draw_line(p1, p2) # 기존 라인 그리기 코드는 주석 처리

draw_heart()  # 하트 그리기 함수 호출
# --------------------

turtle.done()