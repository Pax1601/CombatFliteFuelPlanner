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
    row_height = NumericProperty(30)
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
        self._headerElements = []
        for el in self.header:
            if isinstance(el, tuple):
                label = TableLabel( text = el[0], 
                                    color = [1.0, 1.0, 1.0, 1.0], 
                                    font_size = 14,  
                                    background_color = [0.2, 0.2, 0.2, 1.0], 
                                    size_hint_x = None, 
                                    width = el[1] )
            else:
                label = TableLabel( text = el, 
                                    color = [1.0, 1.0, 1.0, 1.0], 
                                    font_size = 14,  
                                    background_color = [0.2, 0.2, 0.2, 1.0] )
            self._headerElements.append(label)
            self.content.add_widget(label)

    def setContent(self):
        for i, row in enumerate(self.rows):
            for col, el in enumerate(row):
                if isinstance(el, str):
                    label = TableLabel( text = el, 
                                        color = [0.0, 0.0, 0.0, 1.0], 
                                        font_size = 14, 
                                        markup = True, 
                                        background_color = [0.93, 0.93, 0.93, 1.0] if i % 2 else [1.0, 1.0, 1.0, 1.0])
                    if isinstance(self.header[col], tuple):
                        label.size_hint_x = None
                        label.width = self.header[col][1]
                    self.content.add_widget(label)
                else:
                    if isinstance(self.header[col], tuple):
                        el.size_hint_x = None
                        el.width = self.header[col][1]
                    self.content.add_widget(el)

    