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

from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp

import libs.garden.graph

from dataTable import DataTable
import time

background_color = Color([0.95, 0.95, 0.95, 1.0])
text_color = [0.1, 0.1, 0.1, 1.0]

waypointsHeader = ['WP', 'Distance', 'Mach', 'Altitude', 'Bingo', 'Req.', 'Avail.']
flightsHeader = [('Compute', 70), 'Flight name', 'Aircraft', 'Takeoff res. [k lbs]', 'Stack res. [k lbs]']

class FlightSelectionScreen(Screen):
    def __init__(self, **kwargs):
        self._flights = {}
        self._selectedFlight = None
        super().__init__(**kwargs)
        self._table = DataTable(
            pos_hint = {'x': 0.02, 'top': 0.98}, 
            size_hint = (0.96, 0.96),
            header = flightsHeader
        )
        self.add_widget(self._table)

    @property
    def flights(self):
        return self._flights

    @flights.setter
    def flights(self, flights):
        Clock.schedule_once(lambda dt, flights = flights: self._setFlights(flights))

    def _setFlights(self, flights):
        if len(flights) == 0: return

        if self._selectedFlight not in flights:
            self._selectedFlight = None

        for flight in flights:
            if self._selectedFlight is None:
                self._selectedFlight = flight

            if flight not in self._flights: 
                self._flights[flight] = (CheckBox(active = True), flight, "N/A", TextInput(text = "5.5"), TextInput(text = "0.8"))
        
        self._table.rows = [flightData for flightData in self.flights.values()]
        
class LoadoutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        img = Image(source='hornet.png',
                    pos_hint = {'x': 0.02, 'top': 0.98}, 
                    size_hint = (0.96, 0.48))
        self.add_widget(img)

class WaypointsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._table = DataTable(
            pos_hint = {'x': 0.02, 'top': 0.98}, 
            size_hint = (0.96, 0.96),
            header = waypointsHeader
        )
        self.add_widget(self._table)

class FuelProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = libs.garden.graph.Graph(
            xlabel = "Waypoint #",
            ylabel = "Fuel [lbs x 1000]",
            pos_hint = {'x': 0.02, 'top': 0.98}, 
            size_hint = (0.96, 0.96),
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

class GUI(App):
    '''
    def update(self, flights, missionData, fuels):
        if len(flights) == 0: return
        if self.flightButton.text == "Waiting for flights...":
            self.flightButton.text = "Select"

        self.flightMenu.items = [{"text": item, "viewclass": "OneLineListItem", "on_release": lambda x = item, flights = flights, missionData = missionData, fuels = fuels: self.selectFlight(x, flights, missionData, fuels)} for item in list(flights.keys()) if item in missionData]

        if self.activeFlightName is None or self.activeFlightName not in flights: return
        activeFlight = flights[self.activeFlightName]
        if len(activeFlight) == 0 or not activeFlight[0] or len(fuels['Bingo']) == 0: return

        for row in activeFlight:
            for key in row:
                row[key] = f"[color=#000000]{row[key]}[/color]" 

        for i, row in enumerate(activeFlight):
            row['WP'] = f"[color=#000000][b]{str(i)}[/b][/color]" 
            row['Bingo'] = f"[color=#000000][b]{fuels['Bingo'][i]:0.1f}k[/b][/color]"
            row['Req.'] = f"[color=#AA0000][b]{fuels['Required'][i]:0.1f}k[/b][/color]"
            if (fuels['Available'][i] >= fuels['Required'][i]):
                row['Avail.'] = f"[color=#00AA00][b]{fuels['Available'][i]:0.1f}k[/b][/color]"
            else:
                row['Avail.'] = f"[color=#00AA00][s][b]{fuels['Available'][i]:0.1f}k[/b][/s][/color]"
            
        self.table.rows = [[f"{row[key]}" for key in headers] for row in activeFlight]

        if self.bingoPlot is not None:
            self.graph.remove_plot(self.bingoPlot)
        self.bingoPlot = libs.garden.graph.SmoothLinePlot(color = [0, 0, 0, 1])
        self.bingoPlot.points = [(idx, fuel) for idx, fuel in enumerate(fuels['Bingo'])]
        self.graph.add_plot(self.bingoPlot)

        if self.availablePlot is not None:
            self.graph.remove_plot(self.availablePlot)
        self.availablePlot = libs.garden.graph.SmoothLinePlot(color = [0, 0.7, 0, 1])
        self.availablePlot.points = [(idx, fuel) for idx, fuel in enumerate(fuels['Available'])]
        self.graph.add_plot(self.availablePlot)

        if self.requiredPlot is not None:
            self.graph.remove_plot(self.requiredPlot)
        self.requiredPlot = libs.garden.graph.SmoothLinePlot(color = [0.7, 0, 0, 1])
        self.requiredPlot.points = [(idx, fuel) for idx, fuel in enumerate(fuels['Required'])]
        self.graph.add_plot(self.requiredPlot)

        self.graph.xmax = len(fuels['Bingo'])-1

        for acLabel in self.acLabels:
            self.rootLayout.remove_widget(acLabel)

        self.acLabels.clear()

        for station in range(1, 10):
            if str(station) in missionData[self.activeFlightName]['Stores']:
                store = missionData[self.activeFlightName]['Stores'][str(station)]
            else:
                store = 'empty'
            self.acLabels.append(Label(text = f"{station}: {store}", 
                            size_hint = (None, None),
                            size = (500, 20),
                            pos_hint = {'x': 0.04, 'top': 0.75 - (station - 1) * 20 / self.rootLayout.height},
                            color = [0, 0, 0, 1],
                            font_size = 14, 
                            halign = 'left'))

        self.acLabels.append(Label(text = f"Total fuel: {fuels['Available'][0]:.1f}k lbs", 
                            size_hint = (None, None),
                            size = (300, 20),
                            pos_hint = {'x': 0.04, 'y': 0.495},
                            color = [0, 0, 0, 1],
                            font_size = 14, 
                        halign = 'left',
                        bold = True))
        
        self.acLabels.append(Label(text = f"Total weight: {missionData[self.activeFlightName]['Weight'] * 1000:.0f} lbs", 
                             size_hint = (None, None),
                             size = (300, 20),
                             pos_hint = {'x': 0.25, 'y': 0.495},
                             color = [0, 0, 0, 1],
                             font_size = 14, 
                             halign = 'left',
                             bold = True))

        if 'DragIndex' in missionData[self.activeFlightName]:
            self.acLabels.append(Label(text = f"Base drag index: {missionData[self.activeFlightName]['DragIndex']:.0f}", 
                                size_hint = (None, None),
                                size = (300, 20),
                                pos_hint = {'x': 0.04, 'y': 0.465},
                                color = [0, 0, 0, 1],
                                font_size = 14, 
                                halign = 'left',
                                bold = True))

        for acLabel in self.acLabels:
            acLabel.text_size = acLabel.size
            self.rootLayout.add_widget(acLabel)
    '''
    def __init__(self, **kwargs):
        self._initialized = False
        super().__init__(**kwargs)
        Window.size = (600, 400)
        self.icon = "icon/icon.ico"
        self.title = "767 Squadron F/A-18 Hornet Fuel Planner: Mission file never updated"
        
    def build(self):
        self._rootLayout = BoxLayout(orientation = "vertical")

        self._actionBar = ActionBar()
        self._actionView = ActionView(orientation = 'horizontal')

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
