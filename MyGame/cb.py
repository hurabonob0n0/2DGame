from PIL import Image, ImageDraw

def create_grid_background():
    width, height = 1000, 1000
    # 짙은 회색 배경
    image = Image.new('RGB', (width, height), color=(50, 50, 50))
    draw = ImageDraw.Draw(image)

    step = 100 # 100픽셀 간격
    # 격자 그리기
    for x in range(0, width, step):
        draw.line((x, 0, x, height), fill=(100, 100, 100), width=2)
    for y in range(0, height, step):
        draw.line((0, y, width, y), fill=(100, 100, 100), width=2)

    image.save('background.png')
    print("background.png 생성 완료!")

if __name__ == '__main__':
    try:
        create_grid_background()
    except ImportError:
        print("Pillow(PIL) 라이브러리가 없습니다.")
        print("터미널에 'pip install pillow'를 입력하거나,")
        print("그림판으로 1920x1080 크기의 background.png를 직접 만들어주세요.")