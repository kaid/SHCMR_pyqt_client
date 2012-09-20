import time
from PyQt4.QtCore import Qt, QThread, pyqtSignal, QFileSystemWatcher, QObject, QDir, QDirIterator, QFileInfo, QTimer

def convert_byte_size(byte_size):
    for unit in ['bytes','KB','MB','GB','TB']:
        if byte_size < 1024.0:
            return "%3.1f%s" % (byte_size, unit)
        byte_size /= 1024.0

def format_time(seconds):
    return time.strftime('%H小时%M分%S秒', time.gmtime(seconds))

def convert_time(qdatetime):
    qdatetime.setTimeSpec(Qt.LocalTime)
    return qdatetime.toTime_t()

class Worker(QThread):
    done = pyqtSignal()

    def begin(self, job, *args):
        self.__job = job
        self.__args = args
        self.start()

    def __del__(self):
        self.wait()

    def run(self):
        self.__job(*self.__args)
        self.done.emit()

class DirFileInfoList(QObject):
    def __init__(self, directory, parent=None):
        super(DirFileInfoList, self).__init__(parent)
        self.iterator = QDirIterator(directory,
                                     QDir.AllEntries | QDir.NoDotAndDotDot,
                                     QDirIterator.Subdirectories)
        self.__iterate_files()

    def __iterate_files(self):
        self.file_infos = []
        while self.iterator.hasNext():
            info = QFileInfo(self.iterator.next())
            self.file_infos.append(info)

    def get_meta_dict(self):
        meta_dict = {}
        for info in self.file_infos:
            meta_dict[info.absoluteFilePath()] = -1 if info.isDir() else convert_time(info.lastModified() or info.create())
        return meta_dict

class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

class FSMonitor(QObject):
    scanned = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(FSMonitor, self).__init__(parent)
        self.worker = Worker()
        self.timer = QTimer(self)
        self.__init_watcher()
        # self.watching_list = []

    def watch(self, directory):
        # if self.__dict__.get('directory', False):
        #     self.watcher.removePaths(self.watching_list)
        self.directory = directory
        # self.watching_list = list(map(lambda info: info.absoluteFilePath(),
        #                               DirFileInfoList(directory).file_infos))
        # self.watcher.addPath(directory)#self.watching_list)

    def __init_watcher(self):
        # self.watcher = watcher = QFileSystemWatcher()
        # watcher.directoryChanged.connect(self.scan_changes)
        # watcher.directoryChanged.connect(self.__update_watching_list)
        # watcher.fileChanged.connect(self.__update_watching_list)
        self.timer.timeout.connect(self.scan_changes)
        self.timer.start(30000)

    def scan_changes(self):
        self.worker.begin(self.__file_iteration, self.directory)

    def __file_iteration(self, directory):
        print('lalalalala')
        self.meta_dict = DirFileInfoList(directory).get_meta_dict()
        self.scanned.emit(self.meta_dict)
