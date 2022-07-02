from kivy.clock import Clock
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.actionbar import ActionBar, ActionView, ActionButton, ActionPrevious
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button

from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

import libs.garden.graph

from dataTable import DataTable
import time

background_color = Color([0.95, 0.95, 0.95, 1.0])
text_color = [0.1, 0.1, 0.1, 1.0]

waypointsHeader = ['WP', 'Distance', 'Mach', 'Altitude', 'Bingo', 'Req.', 'Avail.']
flightsHeader = [('Export', 70), 'Flight name', 'Aircraft', 'Takeoff res. [k lbs]', 'Stack res. [k lbs]']

class FlightsScreen(Screen): 
        @property
        def flights(self):
            return self._flights

        @flights.setter
        def flights(self, flights):
            Clock.schedule_once(lambda dt, flights = flights: self._setFlights(flights))

class FlightSpecificScreen(FlightsScreen):
    instances = []
    def __init__(self, **kw):
        super().__init__(**kw)
        self.instances.append(self)
        self._selectedFlight = None
        self._dropdownButtons = []
        self._flights = {}
        self._flightDropdown = DropDown()
        self._flightButton = Button(text = 'No flights', 
                                    size_hint = (None, None),
                                    size = (150, 30),
                                    pos_hint = {'x': 0.02, 'top': 0.98},
                                    background_color = [0.2, 0.2, 0.2, 1.0],
                                    background_normal = '')
        self.add_widget(self._flightButton)
        self._flightButton.bind(on_release=self._flightDropdown.open)
        self._flightDropdown.bind(on_select=lambda instance, x: setattr(self._flightButton, 'text', x))

    def _setFlights(self, flights):
        self._flights = flights
        for btn in self._dropdownButtons:
            self._flightDropdown.remove_widget(btn)
        self._dropdownButtons.clear()

        if self._selectedFlight is None and len(self._flights) > 0:
            self._flightButton.text = "Select flight"

        for flight in flights:
            btn = Button(   text = flight, 
                            size_hint = (None, None), 
                            size = self._flightButton.size,
                            background_color = [0.2, 0.2, 0.2, 1.0],
                            background_normal = '')
            for instance in self.instances:
                btn.bind(on_release=lambda btn, instance = instance: instance._selectFlight(btn.text))
            self._flightDropdown.add_widget(btn)
            self._dropdownButtons.append(btn)
        
        if self._selectedFlight is not None:
            if self._selectedFlight in self._flights:
                self._selectFlight(self._selectedFlight)
            else:
                if len(self._flights) > 0:
                    self._selectFlight(list(self._flights.keys())[0])
                else:
                    self._selectFlight(None)
        
    def _selectFlight(self, flight):
        if flight is not None:
            self._flightDropdown.select(flight)
        else:
            self._flightDropdown.select("No flights")
        self._selectedFlight = flight
            
class FlightSelectionScreen(FlightsScreen):
    def __init__(self, **kwargs):
        self._flights = {}
        super().__init__(**kwargs)
        self._table = DataTable(
            pos_hint = {'x': 0.02, 'top': 0.98}, 
            size_hint = (0.96, 0.96),
            header = flightsHeader
        )
        self.add_widget(self._table)

    def _setFlights(self, flights):
        for flight in flights:
            if flight not in self._flights: 
                self._flights[flight] = (CheckBox(active = True), flight, "N/A", TextInput(text = "5.5"), TextInput(text = "0.8"))

        for flight in list(self._flights.keys()):
            if flight not in flights:
                del self._flights[flight]
        
        self._table.rows = [flightData for flightData in self.flights.values()]
        
class LoadoutScreen(FlightSpecificScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        img = Image(source='hornet.png',
                    pos_hint = {'x': 0.02, 'top': 0.98}, 
                    size_hint = (0.96, 0.48))
        self.add_widget(img)

        self._storesLayout = GridLayout(pos_hint = {'x': 0.02, 'top': 0.58}, 
                                        size_hint = (0.47, 0.56),
                                        rows = 10,
                                        cols = 1)
        self.add_widget(self._storesLayout)

        self._dataLayout = GridLayout(  pos_hint = {'x': 0.52, 'top': 0.58}, 
                                        size_hint = (0.47, 0.56),
                                        rows = 10,
                                        cols = 1)
        self.add_widget(self._dataLayout)

        self.bind(pos = self._update, size = self._update)
        self._update()

    def _selectFlight(self, flight):
        super()._selectFlight(flight)

        for child in list(self._storesLayout.children):
            self._storesLayout.remove_widget(child)

        for child in list(self._dataLayout.children):
            self._dataLayout.remove_widget(child)

        if flight is not None:
            if 'Stores' in self._flights[flight] and 'Fuels' in self._flights[flight]:
                stores = self._flights[flight]['Stores']
                fuels = self._flights[flight]['Fuels']

                for station in range(1, 10):
                    if str(station) in stores:
                        store = stores[str(station)]
                    else:
                        store = 'Empty'
                    label = Label(  text = f"{station}: {store}", 
                                    color = [0, 0, 0, 1],
                                    font_size = 14, 
                                    halign = 'left')
                    self._storesLayout.add_widget(label)
                
                strings = [ f"Total fuel: {fuels['Available'][0]:.1f}k lbs",
                            f"Total weight: {self._flights[flight]['Weight'] * 1000:.0f} lbs",
                            f"Base drag index: {self._flights[flight]['DragIndex']:.0f}"
                            ]
                for string in strings:
                    label = Label(  text = string, 
                                    color = [0, 0, 0, 1],
                                    font_size = 14, 
                                    halign = 'left',
                                    bold = True)
                    self._dataLayout.add_widget(label)
                
                while len(self._dataLayout.children) < len(self._storesLayout.children):
                    self._dataLayout.add_widget(Label())

                Clock.schedule_once(self._update, 0)

    def _update(self, *args):
        for child in self._storesLayout.children:
            child.text_size = child.size
        
        for child in self._dataLayout.children:
            child.text_size = child.size

class WaypointsScreen(FlightSpecificScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._table = DataTable(
            pos_hint = {'x': 0.02, 'top': 0.88}, 
            size_hint = (0.96, 0.86),
            header = waypointsHeader
        )
        self.add_widget(self._table)

    def _selectFlight(self, flight):
        super()._selectFlight(flight)
        self._table.rows = []
        if flight is not None:
            if 'Fuels' in self._flights[flight]:
                fuels = self._flights[flight]['Fuels']
                waypoints = self._flights[flight]['Waypoints']
                data = []

                for i, row in enumerate(waypoints):
                    data.append({})
                    for key in ['Distance', 'Mach', 'Altitude']:
                        data[i][key] = f"[color=#000000]{row[key]}[/color]" 
                    data[i]['WP'] = f"[color=#000000][b]{str(i)}[/b][/color]" 
                    data[i]['Bingo'] = f"[color=#000000][b]{fuels['Bingo'][i]:0.1f}k[/b][/color]"
                    data[i]['Req.'] = f"[color=#AA0000][b]{fuels['Required'][i]:0.1f}k[/b][/color]"
                    if (fuels['Available'][i] >= fuels['Required'][i]):
                        data[i]['Avail.'] = f"[color=#00AA00][b]{fuels['Available'][i]:0.1f}k[/b][/color]"
                    else:
                        data[i]['Avail.'] = f"[color=#00AA00][s][b]{fuels['Available'][i]:0.1f}k[/b][/s][/color]"
                    
                self._table.rows = [[f"{row[key]}" for key in waypointsHeader] for row in data]

class FuelProfileScreen(FlightSpecificScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = libs.garden.graph.Graph(
            xlabel = "Waypoint #",
            ylabel = "Fuel [lbs x 1000]",
            pos_hint = {'x': 0.02, 'top': 0.88}, 
            size_hint = (0.96, 0.86),
            label_options = {'color': [0, 0, 0, 1]},
            border_color =  [0, 0, 0, 1], 
            tick_color =    [0.5, 0.5, 0.5, 1], 
            y_grid_label=True, 
            x_grid_label=True,
            xmin = 0,
            xmax = 4,
            ymin = 0,
            ymax = 20,
            x_ticks_major = 1,
            y_ticks_major = 5,
            y_ticks_minor = 1,
            x_grid = True,
            y_grid = True
        )
        self.bingoPlot = None    
        self.availablePlot = None    
        self.requiredPlot = None    
        self.add_widget(self.graph)

    def _selectFlight(self, flight):
        super()._selectFlight(flight)

        if self.bingoPlot is not None:
            self.graph.remove_plot(self.bingoPlot)
        if self.availablePlot is not None:
            self.graph.remove_plot(self.availablePlot)
        if self.requiredPlot is not None:
                self.graph.remove_plot(self.requiredPlot)

        if flight is not None:
            if 'Fuels' in self._flights[flight]:
                fuels = self._flights[flight]['Fuels']
                
                self.bingoPlot = libs.garden.graph.SmoothLinePlot(color = [0, 0, 0, 1])
                self.bingoPlot.points = [(idx, fuel) for idx, fuel in enumerate(fuels['Bingo'])]
                self.graph.add_plot(self.bingoPlot)

                self.availablePlot = libs.garden.graph.SmoothLinePlot(color = [0, 0.7, 0, 1])
                self.availablePlot.points = [(idx, fuel) for idx, fuel in enumerate(fuels['Available'])]
                self.graph.add_plot(self.availablePlot)

                self.requiredPlot = libs.garden.graph.SmoothLinePlot(color = [0.7, 0, 0, 1])
                self.requiredPlot.points = [(idx, fuel) for idx, fuel in enumerate(fuels['Required'])]
                self.graph.add_plot(self.requiredPlot)

                self.graph.xmax = len(fuels['Bingo'])-1

class GUI(App):
    def __init__(self, **kwargs):
        self._initialized = False
        super().__init__(**kwargs)
        Window.size = (600, 400)
        self.icon = "icon/icon.ico"
        self.title = "767 Squadron F/A-18 Hornet Fuel Planner: Mission file never updated"
        
    def build(self):
        self._rootLayout = BoxLayout(orientation = "vertical")

        self._actionBar = ActionBar()
        self._actionView = ActionView(orientation = "horizontal")

        self._actionBar.add_widget(self._actionView)

        self._flightSelectionScreen = FlightSelectionScreen(name="Mission setup")
        self._loadoutScreen = LoadoutScreen(name="Loadout")
        self._waypointsScreen = WaypointsScreen(name="Waypoints")
        self._fuelProfileScreen = FuelProfileScreen(name="Fuel profile")

        self._screenManager = ScreenManager(transition=SlideTransition(duration = .2))
        self._screenManager.add_widget(self._flightSelectionScreen)
        self._screenManager.add_widget(self._loadoutScreen)
        self._screenManager.add_widget(self._waypointsScreen)
        self._screenManager.add_widget(self._fuelProfileScreen)

        self._actionView.add_widget(ActionPrevious(title = "", app_icon = "icon/icon.ico"))
        self._actionView.add_widget(ActionButton(text = "Mission setup", on_release = lambda *args: self._setScreen("Mission setup")))
        self._actionView.add_widget(ActionButton(text = "Loadout", on_release = lambda *args: self._setScreen("Loadout")))
        self._actionView.add_widget(ActionButton(text = "Waypoints", on_release = lambda *args: self._setScreen("Waypoints")))
        self._actionView.add_widget(ActionButton(text = "Fuel profile", on_release = lambda *args: self._setScreen("Fuel profile")))
        self._actionView.add_widget(ActionButton(text = "Export", on_release = lambda *args: self._planner.exportResults()))

        self._rootLayout.add_widget(self._actionBar)
        self._rootLayout.add_widget(self._screenManager)

        self._rootLayout.canvas.before.add(background_color)
        self._rectangle = Rectangle()
        self._rootLayout.canvas.before.add(self._rectangle)
        self._update()
        self._rootLayout.bind(size = self._update, pos = self._update)
        
        self._initialized = True
        return self._rootLayout

    @property
    def flightSelectionScreen(self):
        return self._flightSelectionScreen

    @property
    def loadoutScreen(self):
        return self._loadoutScreen

    @property
    def waypointsScreen(self):
        return self._waypointsScreen

    @property
    def fuelProfileScreen(self):
        return self._fuelProfileScreen

    @property
    def initialized(self):
        return self._initialized

    def setUpdateTime(self, updateTime):
        if updateTime:
            if time is None:
                self.title = "767 Squadron F/A-18 Hornet Fuel Planner: Mission file never updated"
            else:
                self.title = f"767 Squadron F/A-18 Hornet Fuel Planner: Mission file updated {(time.time() - updateTime):0.0f} seconds ago"

    def setPlanner(self, planner):
        self._planner = planner

    def _update(self, *args):
        self._rectangle.pos = self._rootLayout.pos
        self._rectangle.size = self._rootLayout.size

    def _setScreen(self, screen):
        self._screenManager.current = screen
