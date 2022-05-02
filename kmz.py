
from zipfile import ZipFile
import os
import xml.sax, xml.sax.handler

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
            self.mapping[self.name_tag] = {}
        elif self.inPlacemark:
            if name in self.mapping[self.name_tag]:
                self.mapping[self.name_tag][name] += self.buffer
            else:
                self.mapping[self.name_tag][name] = self.buffer
        self.buffer = ""

def parseKml(mapping):
    header = []
    lst = []
    for key, element in mapping.items():
        if 'description' in element and "Flight" in element['description']:
            string = element['description']
            string = string.strip()
            string = string.replace("\n", "', '")
            if string[-1] == ":":
                string = string + " 0"
            string = string.replace(": ", "': '")    
            string = "{'" + string + "'}"
            features = eval(string)
            lst.append(list(features.values()))    
            header = list(features.keys())
    return lst, header
            
def handleKmz(path):
    path = os.path.join(path, "CombatFlite.kmz")
    kmz = ZipFile(path, 'r')
    kml = kmz.open('doc.kml', 'r')
    parser = xml.sax.make_parser()
    handler = PlacemarkHandler()
    parser.setContentHandler(handler)
    parser.parse(kml)
    kmz.close()
    return parseKml(handler.mapping)
