import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fuelPlanner import FuelPlanner, GUI
from threading import Thread

class Handler(FileSystemEventHandler):
    def __init__(self, path) -> None:
        super().__init__()
        self.fuelPlanner = FuelPlanner(path)
        self.fuelPlanner.readKmz()

    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified':
            self.fuelPlanner.readKmz()

def observerTask():
    path = os.path.expanduser("~\\Documents\\CombatFlite")
    # Initialize logging event handler
    event_handler = Handler(path)
  
    # Initialize Observer
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    # Start the observer
    observer.start()
    try:
        while True:
            # Set the thread sleep time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    Thread(target=observerTask, daemon=True).start()
    GUI().run()

    
