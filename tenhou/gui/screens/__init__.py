from abc import ABCMeta, abstractmethod


class EventListener(metaclass=ABCMeta):
    @abstractmethod
    def on_event(self, event):
        raise NotImplementedError()


class AbstractScreen(metaclass=ABCMeta):
    @abstractmethod
    def draw_to_canvas(self, canvas):
        raise NotImplementedError()


class MenuButton(object):
    def __init__(self, text, on_click=None):
        self.text = text
        self.on_click = on_click
        self.hover = False
        self.rect = None
