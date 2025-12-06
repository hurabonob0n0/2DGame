# resources.py
import moderngl
from PIL import Image
from graphic_sys import sys_graphics


class TextureManager:
    def __init__(self):
        self.textures = {}

    def load(self, path):
        if path in self.textures:
            return self.textures[path]

        # sys_graphics가 초기화된 상태여야 함
        ctx = sys_graphics.ctx
        if not ctx:
            raise Exception("Graphics context not initialized yet.")

        try:
            img = Image.open(path).convert('RGBA')
            texture = ctx.texture(img.size, 4, img.tobytes())
            texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.textures[path] = texture
            return texture
        except FileNotFoundError:
            print(f"Error: Texture not found at {path}")
            return None


# 모듈 레벨 싱글톤 인스턴스
sys_textures = TextureManager()