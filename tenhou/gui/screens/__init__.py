from abc import ABCMeta, abstractmethod


class AbstractScreen(metaclass=ABCMeta):
    """Abstract Base Class for all Screen subclasses."""

    @abstractmethod
    def on_mouse_up(self):
        raise NotImplementedError()

    @abstractmethod
    def on_mouse_motion(self):
        raise NotImplementedError()

    @abstractmethod
    def on_window_resized(self):
        raise NotImplementedError()

    @abstractmethod
    def draw_to_canvas(self, canvas):
        raise NotImplementedError()


class MenuButton(object):
    def __init__(self, text, on_click=None):
        self.text = text
        self.on_click = on_click
        self.hover = False
        self.rect = None