from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextFieldRect
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.image import Image
import libs.garden.graph
from dataTable import DataTable
from kivy.core.window import Window
import time
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp

headers = ['WP', 'Distance', 'Mach', 'Altitude', 'Bingo', 'Req.', 'Avail.']

KV = '''
BoxLayout:
    orientation: "vertical"

    MDTabs:
        id: content_tabs
        on_tab_switch: app.on_tab_switch(*args)
'''

class FlightSelectionTab(FloatLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._flights = {}
        self._flightsTable = MDDataTable(
            use_pagination=False,
            check=True,
            column_data=[
                ("[size=14]Flight name[/size]", dp(60),),
                ("[size=14]Aircraft[/size]", dp(60)),
                ("[size=14]Members[/size]", dp(30))
            ],
            elevation=2,
            size_hint = (0.96, 0.96),
            pos_hint = {'x': 0.02, 'top': 0.98}
        )
        self._flightsTable.bind(on_row_press=self.on_row_press)
        self._flightsTable.bind(on_check_press=self.on_check_press)
        self.add_widget(self._flightsTable)

    def on_row_press(self, instance_table, instance_row):
        print(instance_table, instance_row)

    def on_check_press(self, instance_table, current_row):
        print(instance_table, current_row)

    @property
    def flights(self):
        return self._flights

    @flights.setter
    def flights(self, flights):
        Clock.schedule_once(lambda dt, flights = flights: self._setFlights(flights))

    def _setFlights(self, flights):
        if len(flights) == 0: return

        for flight in flights:
            if flight not in self._flights:
                self._flights[flight] = (flight, "", "")
        
        self._flightsTable.row_data = [flightData for flightData in self.flights.values()]
        self._flightsTable.header.height = 25
        foo = 1

        
class LoadoutTab(FloatLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        img = Image(source='hornet.png',
                    pos_hint = {'x': 0.02, 'top': 0.98}, 
                    size_hint = (0.96, 0.48))
        self.add_widget(img)

class WaypointsTab(FloatLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table = DataTable(
            pos_hint = {'x': 0.02, 'top': 0.98}, 
            size_hint = (0.96, 0.96),
            header = headers
        )
        self.add_widget(self.table)

class FuelProfileTab(FloatLayout, MDTabsBase):
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

class GUI(MDApp):
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

    def build(self):
        self.icon = 'icon/icon.ico'
        Window.size = (650, 400)
        return Builder.load_string(KV)

    @property
    def flightSelectionTab(self):
        return self._flightSelectionTab

    @property
    def loadoutTab(self):
        return self._loadoutTab

    @property
    def waypointsTab(self):
        return self._waypointsTab

    @property
    def fuelProfileTab(self):
        return self._fuelProfileTab

    @property
    def initialized(self):
        return self._initialized

    def on_start(self):
        self._flightSelectionTab = FlightSelectionTab(text="Setup flight")
        self._loadoutTab = LoadoutTab(text="Loadout")
        self._waypointsTab = WaypointsTab(text="Waypoints")
        self._fuelProfileTab = FuelProfileTab(text="Fuel profile")

        self.root.ids.content_tabs.add_widget(self._flightSelectionTab)
        self.root.ids.content_tabs.add_widget(self._loadoutTab)
        self.root.ids.content_tabs.add_widget(self._waypointsTab)
        self.root.ids.content_tabs.add_widget(self._fuelProfileTab)
        
        self._initialized = True

    def on_tab_switch(self, *args):
        pass

    def selectFlight(self, x, flights, missionData, fuels):
        setattr(self, "activeFlightName", x)
        if hasattr(self, "planner"):
            Clock.schedule_once(lambda dt: self.planner.readKmz(True), 0)
        #Clock.schedule_once(lambda dt, flights = flights, missionData = missionData, fuels = fuels: MDApp.get_running_app().update(flights, missionData, fuels), 0)
        self.flightMenu.dismiss()
        self.flightButton.text = x

    def setUpdateTime(self, updateTime):
        if updateTime:
            if time is None:
                self.title = "767 Squadron F/A-18 Hornet Fuel Planner: Mission file never updated"
            else:
                self.title = f"767 Squadron F/A-18 Hornet Fuel Planner: Mission file updated {(time.time() - updateTime):0.0f} seconds ago"

    def setPlanner(self, planner):
        self.planner = planner
