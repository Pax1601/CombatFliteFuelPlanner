
import re
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
