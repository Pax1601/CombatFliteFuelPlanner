from zipfile import ZipFile
import os
import xml.sax, xml.sax.handler
import hashlib
from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextFieldRect
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.image import Image
import libs.garden.graph
import re
import geopy.distance
import shutil
import xml.etree.ElementTree as ET
from kivy.core.window import Window
import json
import time
from dataTable import DataTable
from kivy.config import Config

from hornetDragIndexData import dragIndexesTable, inboardStores1, inboardStores2, outboardStores1, outboardStores2, fuselageStores1, fuselageStores2

plane = "FA-18C"
fileName = plane + ".json"
f = open(fileName)
fuelData = json.load(f)
f.close()

headers = ['WP', 'Distance', 'Mach', 'Altitude', 'Bingo', 'Req.', 'Avail.']

class GUI(MDApp):
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

    def sizeUpdate(self, *args):
        pass
        #for graphLabel in self.graphLabels:
        #    self.rootLayout.remove_widget(graphLabel)
#
        #self.graphLabels.clear()
#
        #self.graphLabels.append(Label(text = "Bingo",     x = self.rootLayout.width * 0.97 - 85, y = self.graph.top - 40,   halign = 'right', color = [0, 0, 0, 1] , size_hint = (None, None), size = (80, 20)))
        #self.graphLabels.append(Label(text = "Available", x = self.graphLabels[-1].x, y = self.graphLabels[-1].y - 20,      halign = 'right', color = [0, 0.7, 0, 1], size_hint = (None, None), size = (80, 20)))
        #self.graphLabels.append(Label(text = "Required",  x = self.graphLabels[-1].x, y = self.graphLabels[-1].y - 20,      halign = 'right', color = [0.7, 0, 0, 1], size_hint = (None, None), size = (80, 20)))
        #
        #for graphLabel in self.graphLabels:
        #    graphLabel.text_size = graphLabel.size
        #    self.rootLayout.add_widget(graphLabel)
        
    def build(self):
        Window.size = (750, 800)
        self.icon = 'icon/icon.ico'
        self.rootLayout = MDFloatLayout()

        self.flightMenu = MDDropdownMenu(width_mult=4)
        self.rootLayout.add_widget(Label( text = "Selected flight: ", 
                                            size_hint = (0.15, 0.04),
                                            pos_hint = {'x': 0.02, 'top': 0.98},
                                            font_size = 14,
                                            color = [0, 0, 0, 1]))
        self.flightButton = MDRaisedButton(text = "Waiting for flights...", 
                            on_release = lambda *args: self.flightMenu.open(),
                            size_hint = (0.2, 0.04),
                            pos_hint = {'x': 0.2, 'top': 0.98})
        self.flightMenu.caller = self.flightButton
        self.rootLayout.add_widget(self.flightButton)
        self.activeFlightName = None

        self.rootLayout.add_widget(Label( text = "Stack reserve [k lbs]: ", 
                                            size_hint = (0.15, 0.04),
                                            pos_hint = {'x': 0.51, 'top': 0.98},
                                            font_size = 14,
                                            color = [0, 0, 0, 1]))
        self.reserveTextField = MDTextFieldRect(text = "5.5",
                                                size_hint = (0.15, 0.04),
                                                pos_hint = {'x': 0.7, 'top': 0.98},
                                                font_size = 14,
                                                multiline = False)
        self.reserveTextField.bind(on_text_validate = lambda *args: self.planner.readKmz(True))
        self.rootLayout.add_widget(self.reserveTextField)
    
        self.table = DataTable(
            pos_hint = {'x': 0.5, 'top': 0.92}, 
            size_hint = (0.48, 0.46),
            header = headers
        )
        self.rootLayout.add_widget(self.table)

        img = Image(source='hornet.png',
                    pos_hint = {'x': 0.02, 'y': 0.725}, 
                    size_hint = (0.46, 0.2))
        self.rootLayout.add_widget(img)

        self.graph = libs.garden.graph.Graph(
            xlabel = "Waypoint #",
            ylabel = "Fuel [lbs x 1000]",
            pos_hint = {'x': 0.0125, 'y': 0.0}, 
            size_hint = (0.97, 0.43),
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
        self.rootLayout.add_widget(self.graph)

        self.acLabels = []
        self.graphLabels = []

        self.rootLayout.bind(size = self.sizeUpdate, pos = self.sizeUpdate)
        self.graph.bind(size = self.sizeUpdate, pos = self.sizeUpdate)
        Clock.schedule_once(self.sizeUpdate, 0)
        return self.rootLayout

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

class PlacemarkHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.inName = False # handle XML parser events
        self.inPlacemark = False
        self.mapping = {}
        self.buffer = ""
        self.name_tag = ""
       
    def startElement(self, name, attributes):
        if name == "Placemark": # on start Placemark tag
            self.inPlacemark = True
            self.buffer = ""
        if self.inPlacemark:
            if name == "name": # on start title tag
                self.inName = True # save name text to follow
           
    def characters(self, data):
        if self.inPlacemark: # on text within tag
            self.buffer += data # save text if in title
           
    def endElement(self, name):
        self.buffer = self.buffer.strip('\n\t')
       
        if name == "Placemark":
            self.inPlacemark = False
            self.name_tag = "" #clear current name
       
        elif name == "name" and self.inPlacemark:
            self.inName = False # on end title tag           
            self.name_tag = self.buffer.strip()
            
            if self.name_tag in self.mapping:
                pattern = re.compile(f"^({self.name_tag}_[0-9]+)+$")
                reps = [name for name in self.mapping if pattern.match(name)]
                self.name_tag = f"{self.name_tag}_{len(reps) + 1}"
            self.mapping[self.name_tag] = {}
        elif self.inPlacemark:
            if name in self.mapping[self.name_tag]:
                self.mapping[self.name_tag][name] += self.buffer
            else:
                self.mapping[self.name_tag][name] = self.buffer
        self.buffer = ""

class FuelPlanner():
    def __init__(self, path) -> None:
        self.path = path
        self.kmzHash = None
        self.cfHash = None
        self.lastUpdateTime = None
        Clock.schedule_interval(self.updateTime, 1.0)
        
    def updateTime(self, dt):
        MDApp.get_running_app().setUpdateTime(self.lastUpdateTime)

    def readKmz(self, force = False): 
        if (MDApp.get_running_app()):
            MDApp.get_running_app().setPlanner(self)
            read = False
            while not read:
                try:
                    kmzFilename = os.path.join(self.path, "CombatFlite.kmz")
                    cfFilename = os.path.join(self.path, "Autosave.cf")
                    kmzHash = hashlib.md5(open(kmzFilename, 'rb').read()).hexdigest()
                    cfHash = hashlib.md5(open(cfFilename, 'rb').read()).hexdigest()

                    missionFileChanged = False
                    if cfHash != self.cfHash:
                        self.cfHash = cfHash
                        self.lastUpdateTime = time.time()
                        missionFileChanged = True

                    if missionFileChanged or kmzHash != self.kmzHash or force:
                        self.kmzHash = kmzHash

                        kmz = ZipFile(kmzFilename, 'r')
                        kml = kmz.open('doc.kml', 'r')
                        self.parser = xml.sax.make_parser()
                        self.handler = PlacemarkHandler()
                        self.parser.setContentHandler(self.handler)
                        self.parser.parse(kml)
                        kmz.close()
                        flights = self._parseKml()

                        tmpName = cfFilename[:-3] + "_tmp.cf"
                        writeName = cfFilename[:-3] + "_fuel.cf"
                        shutil.copyfile(cfFilename, tmpName)
                        cf = ZipFile(tmpName, 'r')
                        missionFile = cf.open('mission.xml', 'r')
                        fileString = missionFile.read().decode('utf-8')
                        self.root = ET.fromstring(fileString)
                        missionData = self._parseMission()
                        cf.close()

                        app = MDApp.get_running_app()
                        if hasattr(app, 'activeFlightName') and app.activeFlightName and app.activeFlightName in missionData \
                           and app.activeFlightName in flights and len(flights[app.activeFlightName]) > 0 and len(flights[app.activeFlightName][0]) > 0:
                            fuels, baseDragIndex = self._computeFuel(flights[app.activeFlightName], missionData[app.activeFlightName])
                            missionData[app.activeFlightName]['DragIndex'] = baseDragIndex
                            self._editMission(app.activeFlightName, fuels, flights[app.activeFlightName])
                            xmlstr = ET.tostring(self.root , encoding='utf-8', method='xml')
                            cf = ZipFile(writeName, 'w')
                            writeFile = cf.open('mission.xml', 'w')
                            writeFile.write(xmlstr)
                            writeFile.close()
                        else:
                            fuels = {'Bingo': [], 'Used': [], 'Available': [], 'Required': []}
                            missionFile.close()
                        cf.close()
                        Clock.schedule_once(lambda dt, flights = flights, missionData = missionData, fuels = fuels: MDApp.get_running_app().update(flights, missionData, fuels), 0)
                    read = True
                except (FileNotFoundError, PermissionError) as e:
                    read = False
        
    def _parseKml(self ):
        mapping = self.handler.mapping
        dataTable = []
        flights = {}
        for key, element in mapping.items():
            if 'coordinates' in element and 'extrude' in element and 'description' not in element:
                coords = element['coordinates'].strip().split(' ')
                flights[key] = coords

        for key, element in mapping.items():
            if 'description' in element and "Flight" in element['description']:
                string = element['description']
                string = string.strip()
                string = string.replace("\n", "', '")
                string = string.replace("Min fuel to complete", "Fuel")
                string = string.replace("AMSL", "")
                if string[-1] == ":":
                    string = string + " 0"
                string = string.replace(": ", "': '")    
                string = "{'" + string + "'}"
                features = eval(string)
                dataTable.append(list(features.values()))    
                for flight, waypoints in flights.items():
                    if flight in features["Flight"]:
                        for idx, waypoint in enumerate(waypoints):
                            if waypoint == element['coordinates'].strip():
                                coords = waypoint.split(',')
                                features['Latitude'] = coords[1]
                                features['Longitude'] = coords[0]
                                flights[flight][idx] = features
        return flights

    def _parseMission(self):
        missionData = {}
        for child in self.root:
            if child.tag == 'Routes':
                for route in child:
                    name = route.find("Name").text
                    fuel = float(route.find("FlightMembers").find("FlightMember").find("Aircraft").find("InitFuel").text)
                    weight = float(route.find("FlightMembers").find("FlightMember").find("Aircraft").find("InitWeight").text)
                    storesTag = route.find("FlightMembers").find("FlightMember").find("Aircraft").find("Stores")
                    stores = {}
                    for store in storesTag:
                        stores[store.find('Pylon').text] = store.find('StoreName').text
                    missionData[name] = {'Fuel': fuel * 2.20462 / 1000, 'Stores': stores, 'Weight': weight * 2.20462 / 1000}
        return missionData

    def _editMission(self, flightName, fuels, activeFlight):
        coordinates = [(row['Latitude'], row['Longitude']) for row in activeFlight]
        for child in self.root:
            if child.tag == 'Routes':
                for route in child:
                    name = route.find("Name").text
                    if name == flightName:
                        for idx, waypoint in enumerate(route.find("Waypoints")):
                            name = waypoint.find('Name')
                            lat = waypoint.find('Lat')
                            lon = waypoint.find('Lon')
                            if idx < len(fuels['Bingo']):
                                name.text = f"{name.text.split(' BINGO: ')[0]} BINGO: {fuels['Bingo'][idx]:.2f}"
                                lat.text = coordinates[idx][0]
                                lon.text = coordinates[idx][1]
                
    def _computeFuel(self, activeFlight, missionData):
        coordinates = [(float(row['Latitude']), float(row['Longitude'])) for row in activeFlight if row]
        home = coordinates[-1]
        distances = [geopy.distance.geodesic(coordinate, home).nm for coordinate in coordinates]
        legFuels = [(distance * 10) / 1000 for distance in distances]

        weight = missionData['Weight'] 

        bagsCount = 0
        for store in missionData['Stores'].values():
            if "FPU-8A" in store:
                bagsCount += 1
        totalFuel = missionData['Fuel'] + bagsCount * 330 * 6.71 / 1000.0
        try:
            reserve = float(MDApp.get_running_app().reserveTextField.text)
            MDApp.get_running_app().reserveTextField.error = False
        except:
            reserve = 5.5
            MDApp.get_running_app().reserveTextField.text = "5.5"
            MDApp.get_running_app().reserveTextField.error = True

        fuels = {}
        fuels['Used'] = [0]
        fuels['Available'] = [totalFuel]
        fuels['Required'] = []
        fuels['Bingo'] = [] 
        baseDragIndex = 0

        for legFuel in legFuels:
            fuels['Bingo'].append( legFuel + reserve)

        for i in range(len(activeFlight) - 1):
            startCoordinates = (float(activeFlight[i]['Latitude']), float(activeFlight[i]['Longitude']))
            endCoordinates = (float(activeFlight[i + 1]['Latitude']), float(activeFlight[i + 1]['Longitude']))
            legDistance = geopy.distance.geodesic(startCoordinates, endCoordinates).nm
            altitude = float(activeFlight[i + 1]['Altitude'].replace("ft", "").replace( "AGL", "").strip())
            mach = float(activeFlight[i + 1]["Mach"])
            
            baseDragIndex, dragIndex = self._computeDragIndex(missionData, altitude, mach)
           
            # Average initial and final fuel consumption #TODO iteration may be needed
            SFi = self._interpolateFuelData(altitude, weight * 1000, dragIndex, mach)
            _weight = weight - legDistance / SFi / 1000
            SFf = self._interpolateFuelData(altitude, _weight * 1000, dragIndex, mach)
            SF = (SFi + SFf) / 2

            fuelBurn = legDistance / SF / 1000
            weight = weight - fuelBurn
            totalFuel = totalFuel - fuelBurn
            fuels['Used'].append(fuelBurn)
            fuels['Available'].append(totalFuel)
        
        t = list(fuels['Used'])
        k = []
        t.reverse()
        required = reserve
        k.append(required)
        for legRequired in t[:-1]:
            required += legRequired
            k.append(required)

        k.reverse()
        fuels['Required'] = k
            
        return fuels, baseDragIndex

    def _computeDragIndex(self, missionData, altitude, mach):
        basicStoreDragIndexs = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        stores = {}
        for station, store in missionData['Stores'].items():
            store.replace("GBU-38", "Mk-82")
            store.replace("GBU-32", "Mk-83")
            store.replace("GBU-35", "Mk-83")
            store.replace("GBU-31", "Mk-84")

            station = int(station)
            for tableStore in dragIndexesTable:
                if tableStore[0][0] in store:
                    if station not in stores:
                        stores[station] = [tableStore[0][0]]
                    else:
                        stores[station].append(tableStore[0][0])
                    if len(tableStore[0]) == 1:
                        storeDragIndex = tableStore[1][0]
                    else:
                        modifier = False
                        for index, tableStation in enumerate(tableStore[0]):
                            if tableStation == station:
                                storeDragIndex = tableStore[1][index]
                                modifier = True
                        if not modifier:
                            storeDragIndex = tableStore[1][0]
                    
                    storeStringIndex = store.index(tableStore[0][0])
                    for multiplier in range(1, 10):
                        if storeStringIndex >+ 5 and f" {multiplier}" in store[storeStringIndex - 5: storeStringIndex]:
                            storeDragIndex *= multiplier

                    basicStoreDragIndexs[station - 1] += storeDragIndex

            # Pylon
            if station in [2, 3, 7, 8]:
                basicStoreDragIndexs[station - 1] += 7.5
        
        interferenceCodeNumber = 0
        if 2 in stores and 3 in stores:
            interferenceCodeNumber += self._findIntereferenceCodeNumber(inboard = stores[3], outboard = stores[2] , fuselage = None)

        if 7 in stores and 8 in stores:
            interferenceCodeNumber += self._findIntereferenceCodeNumber(inboard = stores[7], outboard = stores[8] , fuselage = None)

        if 4 in stores and 3 in stores:
            interferenceCodeNumber += self._findIntereferenceCodeNumber(inboard = stores[3], outboard = None , fuselage = stores[4])

        if 7 in stores and 6 in stores:
            interferenceCodeNumber += self._findIntereferenceCodeNumber(inboard = stores[7], outboard = None , fuselage = stores[6])

        interferenceDragIndex = self._computeInterferenceDrag(interferenceCodeNumber, mach, altitude)

        baseDragIndex = 0
        for dragIndex in basicStoreDragIndexs:
            baseDragIndex += dragIndex
        return baseDragIndex, interferenceDragIndex + baseDragIndex

    def _computeInterferenceDrag(self, interferenceCodeNumber, mach, altitude):
        dashCruiseMach = [0.6, 0.8, 0.9]
        dashCruiseAltitude = [0.0, 15000.0, 30000.0]
        dashCruiseLimit = self._linearInterpolate(dashCruiseAltitude, dashCruiseMach, altitude)

        if mach >= dashCruiseLimit:
            slopes = [20 / 24, 26 / 24, 40 / 24, 70 / 24]
        else:
            slopes = [12 / 24, 16 / 24, 22 / 24, 52 / 24]

        machs = [0.6, 0.7, 0.8, 0.85]
        slope = self._linearInterpolate(machs, slopes, mach)
        return interferenceCodeNumber * slope

    def _findIntereferenceCodeNumber(self, inboard, outboard = None, fuselage = None):
        if outboard is not None:
            interferenceRowStore = None
            interferenceColumnIndex = None

            for row, store in enumerate(outboardStores1):
                if False not in [substore in store for substore in outboard]:
                    interferenceRowStore = store
                    break

            for column, store in enumerate(inboardStores1):
                if False not in [substore in store for substore in inboard]:
                    interferenceColumnIndex = column
                    break

            if interferenceColumnIndex is not None and interferenceRowStore is not None:
                return outboardStores1[interferenceRowStore][interferenceColumnIndex]

            for row, store in enumerate(outboardStores2):
                if False not in [substore in store for substore in outboard]:
                    interferenceRowStore = store
                    break
                    
            for column, store in enumerate(inboardStores2):
                if False not in [substore in store for substore in inboard]:
                    interferenceColumnIndex = column
                    break
            
            if interferenceColumnIndex is not None and interferenceRowStore is not None:
                return outboardStores2[interferenceRowStore][interferenceColumnIndex]

        if fuselage is not None:
            interferenceRowStore = None
            interferenceColumnIndex = None

            for row, store in enumerate(fuselageStores1):
                if False not in [substore in store for substore in fuselage]:
                    interferenceRowStore = store
                    break

            for column, store in enumerate(inboardStores1):
                if False not in [substore in store for substore in inboard]:
                    interferenceColumnIndex = column
                    break

            if interferenceColumnIndex is not None and interferenceRowStore is not None:
                return fuselageStores1[interferenceRowStore][interferenceColumnIndex]

            for row, store in enumerate(fuselageStores2):
                if False not in [substore in store for substore in fuselage]:
                    interferenceRowStore = store
                    break
                    
            for column, store in enumerate(inboardStores2):
                if False not in [substore in store for substore in inboard]:
                    interferenceColumnIndex = column
                    break
            
            if interferenceColumnIndex is not None and interferenceRowStore is not None:
                return fuselageStores2[interferenceRowStore][interferenceColumnIndex]
        return 0

    def _linearInterpolate(self, x, y, xm):
        if xm < x[0]:
            return y[0]
        elif xm >= x[-1]:
            return y[-1]
        else:
            for i in range(len(x) - 1):
                xp = x[i]
                xs = x[i + 1]
                yp = y[i]
                ys = y[i + 1]
                if xp <= xm < xs:
                    return yp + (xm - xp) / (xs - xp) * (ys - yp)

    def _interpolateFuelData(self, altitude, weight, dragIndex, mach):
        altitudes = []
        altitudeSFs = []
        for _altitude in fuelData:
            weights = []
            weightSFs = []
            for _weight in fuelData[_altitude]:
                dragIndexs = []
                dragIndexSFs = []
                for _dragIndex in fuelData[_altitude][_weight]:
                    machs = [value[0] for value in fuelData[_altitude][_weight][_dragIndex]]
                    SFs = [value[1] for value in fuelData[_altitude][_weight][_dragIndex]]
                    dragIndexs.append(float(_dragIndex))
                    dragIndexSFs.append(self._linearInterpolate(machs, SFs, mach))
                weights.append(float(_weight))
                weightSFs.append(self._linearInterpolate(dragIndexs, dragIndexSFs, dragIndex))
            altitudes.append(float(_altitude))
            altitudeSFs.append(self._linearInterpolate(weights, weightSFs, weight))
        
        return self._linearInterpolate(altitudes, altitudeSFs, altitude)
            
                    