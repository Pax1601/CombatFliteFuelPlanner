from tkinter import *
from  tkinter import ttk
from table import Table
import os
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from kmz import handleKmz
from threading import Thread

kmzModified = True
ws = None
lst = []
table = None
class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified':
            global kmzModified
            kmzModified = True

def GUITask():
    global table
    ws = Tk()
    ws.title('Combat Flite Fuel Planner')
    ws.geometry('500x500')
    ws['bg'] = '#AC99F2'
    table = Table(ws)
    ws.mainloop()
   
if __name__ == "__main__":
    # Set the format for logging info
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
  
    # Set format for displaying path
    path = os.path.expanduser("~\\Documents\\CombatFlite")
  
    # Initialize logging event handler
    event_handler = Handler()
  
    # Initialize Observer
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    # Start the GUI
    Thread(target=GUITask, daemon=True).start()
  
    # Start the observer
    observer.start()
    try:
        while True:
            # Set the thread sleep time
            time.sleep(1)
            if kmzModified:
                lst, header = handleKmz(path)
                table.update(lst, header)
                kmzModified = False
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

