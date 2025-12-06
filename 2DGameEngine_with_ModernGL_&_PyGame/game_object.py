from object_manager import sys_objects

# --- Game Object ---
class GameObject:
    def __init__(self, name="GameObject", x=0, y=0):
        self.name = name
        self.position = [x, y]
        self.scale = [100, 100]
        self.components = []
        self.active = True
        sys_objects.add(self)

    def add_component(self, component_cls, name=None, *args, **kwargs):
        component = component_cls(self, *args, **kwargs)
        if name:
            component.name = name
        self.components.append(component)
        return component

    def get_component(self, name):
        for c in self.components:
            if c.name == name:
                return c
        return None

    def get_component_by_type(self, component_cls):
        for c in self.components:
            if isinstance(c, component_cls):
                return c
        return None

    def update(self, dt):
        for component in self.components:
            if component.active:
                component.update(dt)

    def render(self):
        for component in self.components:
            if component.active:
                component.render()





