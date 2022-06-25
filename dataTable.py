from kivy.uix.scrollview import ScrollView
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line

class TableLabel(Label):
    background_color = ListProperty([0, 0, 0, 0])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            colorString = str(self.background_color).replace("[", "").replace("]", "")
            eval(f"Color({colorString})")
            self.rectangle = Rectangle(pos=self.pos, size=self.size)
            Color(0.8, 0.8, 0.8)
            x = self.rectangle.pos[0]
            y = self.rectangle.pos[1]
            right = x + self.rectangle.size[0]
            top = y + self.rectangle.size[1]
            self.line = Line(points=[x, y, x, top, right, top, right, y, x, y], width=1)
        self.bind(pos = self._update, size = self._update)
        self._update()
    
    def _update(self, *args):
        self.rectangle.pos = self.pos
        self.rectangle.size = self.size
        x = self.rectangle.pos[0]
        y = self.rectangle.pos[1]
        right = x + self.rectangle.size[0]
        top = y + self.rectangle.size[1]
        self.line.points= [x, y, x, top, right, top, right, y, x, y]
    
class DataTable(ScrollView):
    header = ListProperty([])
    rows = ListProperty([]) 
    row_height = NumericProperty(18)
    def __init__(self, **kwargs):        
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1)
            self.rectangle = Rectangle(pos=self.pos, size=self.size)
            Color(0.8, 0.8, 0.8)
            x = self.rectangle.pos[0]
            y = self.rectangle.pos[1]
            right = x + self.rectangle.size[0]
            top = y + self.rectangle.size[1]
            self.line = Line(points=[x, y, x, top, right, top, right, y, x, y], width=1)

        self.content = GridLayout(  cols = len(self.header), 
                                    rows = len(self.header),
                                    size_hint = (None, None))
        self.add_widget(self.content)
        self.bind(size = self._update, pos = self._update, header = self._update, rows = self._update)
        self._update()

    def _update(self, *args):
        for child in list(self.content.children):
            self.content.remove_widget(child)
        self.content.cols = len(self.header)
        self.content.rows = len(self.rows) + 1
        self.content.width = self.width
        self.content.height = (self.content.rows) * self.row_height
        self.setHeader()
        self.setContent()
        self.rectangle.pos = self.pos
        self.rectangle.size = self.size
        x = self.rectangle.pos[0]
        y = self.rectangle.pos[1]
        right = x + self.rectangle.size[0]
        top = y + self.rectangle.size[1]
        self.line.points= [x, y, x, top, right, top, right, y, x, y]

    def setHeader(self):
        for el in self.header:
            label = TableLabel(text = el, color = [0, 0, 0, 1], font_size = 12, bold = True,  background_color = [0.9, 0.9, 0.9, 1.0] )
            self.content.add_widget(label)

    def setContent(self):
        for i, row in enumerate(self.rows):
            for el in row:
                label = TableLabel(text = el, font_size = 12, markup = True, background_color = [0.93, 0.93, 0.93, 1.0] if i % 2 else [1.0, 1.0, 1.0, 1.0])
                self.content.add_widget(label)

    