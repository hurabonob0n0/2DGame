# scene_system.py

class Scene:
    def enter(self): pass
    def exit(self): pass
    def update(self, dt): pass
    def render(self): pass

class SceneManager:
    def __init__(self):
        self.current_scene = None

    def change_scene(self, scene):
        if self.current_scene:
            self.current_scene.exit()
        self.current_scene = scene
        self.current_scene.enter()

    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)

    def render(self):
        if self.current_scene:
            self.current_scene.render()

# 모듈 레벨 싱글톤 인스턴스
sys_scenes = SceneManager()