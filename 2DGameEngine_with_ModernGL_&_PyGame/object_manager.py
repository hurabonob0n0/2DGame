# object_manager.py

class ObjectManager:
    def __init__(self):
        self.objects = {}  # Key: name, Value: List[GameObject]

    def add(self, obj):
        if obj.name not in self.objects:
            self.objects[obj.name] = []
        self.objects[obj.name].append(obj)

    def remove(self, obj):
        if obj.name in self.objects:
            if obj in self.objects[obj.name]:
                self.objects[obj.name].remove(obj)

    def update_all(self, dt):
        for name, obj_list in self.objects.items():
            for obj in obj_list:
                if obj.active:
                    obj.update(dt)

    def render_all(self):
        for name, obj_list in self.objects.items():
            for obj in obj_list:
                if obj.active:
                    obj.render()

    def clear(self):
        self.objects.clear()


# 싱글톤 인스턴스
sys_objects = ObjectManager()