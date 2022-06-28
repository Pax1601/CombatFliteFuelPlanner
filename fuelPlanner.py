from zipfile import ZipFile
import os
import xml.sax, xml.sax.handler
import hashlib

import geopy.distance
import shutil
import xml.etree.ElementTree as ET
import json
import time
from kivy.app import App
from kivy.clock import Clock

from placemarkHandler import PlacemarkHandler
from hornetDragIndexData import dragIndexesTable, inboardStores1, inboardStores2, outboardStores1, outboardStores2, fuselageStores1, fuselageStores2

plane = "FA-18C"
fileName = plane + ".json"
f = open(fileName)
fuelData = json.load(f)
f.close()

class FuelPlanner():
    def __init__(self, path) -> None:
        self._path = path
        self._kmzHash = None
        self._cfHash = None
        self._lastUpdateTime = None
        self._kmzFilename = os.path.join(self._path, "CombatFlite.kmz")
        self._cfFilename = os.path.join(self._path, "Autosave.cf")
        self._tmpName = self._cfFilename[:-3] + "_tmp.cf"
        self._writeName = self._cfFilename[:-3] + "_fuel.cf"
        Clock.schedule_interval(self._updateTime, 1.0)
        
    def readKmz(self, force = False):
        app = App.get_running_app() 
        if app and app.initialized:
            app.setPlanner(self)
            read = False
            while not read:
                try:
                    kmzHash = hashlib.md5(open(self._kmzFilename, 'rb').read()).hexdigest()
                    cfHash = hashlib.md5(open(self._cfFilename, 'rb').read()).hexdigest()

                    # The mission file has changed. Update the time of last load
                    if cfHash != self._cfHash:
                        self._lastUpdateTime = time.time()

                    # Run the fuel analysis
                    if cfHash != self._cfHash or kmzHash != self._kmzHash or force:
                        self._kmzHash = kmzHash
                        self._cfHash = cfHash

                        # Read the kmz file and extract the available flights
                        kmz = ZipFile(self._kmzFilename, 'r')
                        kml = kmz.open('doc.kml', 'r')
                        self._parser = xml.sax.make_parser()
                        self._handler = PlacemarkHandler()
                        self._parser.setContentHandler(self._handler)
                        self._parser.parse(kml)
                        kmz.close()
                        waypoints = self._parseKml()

                        # Read the cf file and extract the mission data
                        shutil.copyfile(self._cfFilename, self._tmpName)
                        cf = ZipFile(self._tmpName, 'r')
                        missionFile = cf.open('mission.xml', 'r')
                        fileString = missionFile.read().decode('utf-8')
                        self._root = ET.fromstring(fileString)
                        self._missionData = self._parseMission()
                        cf.close()

                        for flight in self._missionData:
                            if flight in waypoints:
                                self._missionData[flight]['Waypoints'] = waypoints[flight]

                        # Set the available flights on the GUI
                        app.flightSelectionScreen.flights   = self._missionData
                        
                        # Compute the fuel
                        Clock.schedule_once(lambda *args: self._analyzeFlights(), 0.1)

                        read = True
                        
                except (FileNotFoundError, PermissionError) as e:
                    read = False

    def exportResults(self):
        for flight in self._missionData.keys():
            self._editMission(flight)
            xmlstr = ET.tostring(self._root , encoding='utf-8', method='xml')
            cf = ZipFile(self._writeName, 'w')
            writeFile = cf.open('mission.xml', 'w')
            writeFile.write(xmlstr)
            writeFile.close()
            cf.close()

    def _analyzeFlights(self):
        for flight in self._missionData.keys():
            fuels, baseDragIndex = self._computeFuel(flight)
            if fuels is not None and baseDragIndex is not None:
                self._missionData[flight]['DragIndex'] = baseDragIndex
                self._missionData[flight]['Fuels'] = fuels  

        app = App.get_running_app() 
        if app and app.initialized:
            app.loadoutScreen.flights           = self._missionData
            app.waypointsScreen.flights         = self._missionData
            app.fuelProfileScreen.flights       = self._missionData

    def _updateTime(self, dt):
        App.get_running_app().setUpdateTime(self._lastUpdateTime)

    def _parseKml(self ):
        mapping = self._handler.mapping
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
        for child in self._root:
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

    def _editMission(self, flight):
        if flight in self._missionData and 'Fuels' in self._missionData[flight]:
            fuels = self._missionData[flight]['Fuels']
            waypoints = self._missionData[flight]['Waypoints']
            coordinates = [(row['Latitude'], row['Longitude']) for row in waypoints]
            for child in self._root:
                if child.tag == 'Routes':
                    for route in child:
                        name = route.find("Name").text
                        if name == flight:
                            for idx, waypoint in enumerate(route.find("Waypoints")):
                                name = waypoint.find('Name')
                                lat = waypoint.find('Lat')
                                lon = waypoint.find('Lon')
                                if idx < len(fuels['Bingo']):
                                    name.text = f"{name.text.split('/B')[0]}/B{fuels['Bingo'][idx]:.1f}-R{fuels['Required'][idx]:.1f}"
                                    lat.text = coordinates[idx][0]
                                    lon.text = coordinates[idx][1]
                
    def _computeFuel(self, flight):
        app = App.get_running_app() 
        if flight in self._missionData:
            waypoints = self._missionData[flight]['Waypoints']
            missionData = self._missionData[flight]

            coordinates = [(float(row['Latitude']), float(row['Longitude'])) for row in waypoints if row]
            home = coordinates[-1]
            distances = [geopy.distance.geodesic(coordinate, home).nm for coordinate in coordinates]
                                    # Specific fuel consumption on the deck clean
            legFuels = [(distance / 0.065) / 1000 for distance in distances]

            weight = missionData['Weight'] 

            bagsCount = 0
            for store in  missionData['Stores'].values():
                if "FPU-8A" in store:
                    bagsCount += 1
            totalFuel =  missionData['Fuel'] + bagsCount * 330 * 6.71 / 1000.0

            reserve = 5.5
            try:
                reserve = float(app.flightSelectionScreen.flights[flight][3].text)
            except:
                app.flightSelectionScreen.flights[flight][3].text = "5.5"

            fuels = {}
            fuels['Used'] = [0]
            fuels['Available'] = [totalFuel]
            fuels['Required'] = []
            fuels['Bingo'] = [] 
            baseDragIndex = 0

            for legFuel in legFuels:
                fuels['Bingo'].append( legFuel + reserve)

            for i in range(len(waypoints) - 1):
                startCoordinates = (float(waypoints[i]['Latitude']), float(waypoints[i]['Longitude']))
                endCoordinates = (float(waypoints[i + 1]['Latitude']), float(waypoints[i + 1]['Longitude']))
                legDistance = geopy.distance.geodesic(startCoordinates, endCoordinates).nm
                altitude = float(waypoints[i + 1]['Altitude'].replace("ft", "").replace( "AGL", "").strip())
                mach = float(waypoints[i + 1]["Mach"])
                
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
        return None, None

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
            
                    