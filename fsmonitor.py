from PyQt4.QtCore import QObject
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from utils import *
from env import *

class FileChangeHandler(PatternMatchingEventHandler):
    def on_created(self, event):
        DataStore.insert_record(QFileInfo(event.src_path))

    def on_deleted(self, event):
        DataStore.delete_record(event.src_path)

    def on_modified(self, event):
        DataStore.update_record(QFileInfo(event.src_path))

    def on_moved(self, event):
        DataStore.move_record(event.src_path, event.dest_path)

class FSMonitor(QObject):
    def __init__(self, parent=None):
        super(FSMonitor, self).__init__(parent)
        self.worker = Worker()
        self.observer = Observer()

    def watch(self, directory):
        self.observer.schedule(FileChangeHandler(ignore_patterns=[from_qvariant(directory)]),
                               path=from_qvariant(directory),
                               recursive=True)

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()
