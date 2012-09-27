from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from utils import *

class __DataStoreObject(QObject):
    committed = pyqtSignal()

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.__init_database()
        self.query = QSqlQuery()
        self.__setup_database()
        self.__batch_exec = False

    def start_batch(self):
        self.__batch_exec = True

    def end_batch(self):
        self.__batch_exec = False

    def emit_committed(self):
        self.__batch_exec or self.committed.emit()

    def __init_database(self):
        self.database = QSqlDatabase.addDatabase('QSQLITE')
        self.database.setDatabaseName('database.db')
        self.database.open()

    def __setup_database(self):
        with open('database.sql', 'r') as file:
            for string in file.read().split(';')[0:-1]:
                self.query.exec_(string)

    def get(self, path):
        self.query.exec_('SELECT * FROM file_list WHERE path="%s"' % path)

        while self.query.next():
            return self.query

        return None

    def update_record(self, info):
        process_event()
        string = 'UPDATE file_list SET modified_at=%d, size=%d WHERE path="%s"' % (
            modified_at_of(info),
            info.size(),
            from_qvariant(info.absoluteFilePath()),
        )

        self.query.exec_(string)
        self.emit_committed()

    def move_record(self, src_path, dest_path):
        process_event()
        dest_info = QFileInfo(dest_path)
        string = 'UPDATE file_list SET name="%s", path="%s", modified_at="%d" WHERE path="%s"' % (
            from_qvariant(dest_info.fileName()),
            dest_path,
            modified_at_of(dest_info),
            src_path
        )

        self.query.exec_(string)
        self.emit_committed()

    def insert_record(self, info):
        process_event()
        if self.get(info.absoluteFilePath()):
            return self.update_record(info)

        string = 'INSERT INTO file_list (name, size, path, is_dir, modified_at)\
                  VALUES (:name, :size, :path, :is_dir, :modified_at)'

        self.query.prepare(string)
        self.query.bindValue(':name', info.fileName())
        self.query.bindValue(':size', info.size())
        self.query.bindValue(':path', info.absoluteFilePath())
        self.query.bindValue(':is_dir', 1 if info.isDir() else 0)
        self.query.bindValue(':modified_at', modified_at_of(info))
        self.query.exec_()
        self.emit_committed()

    def delete_record(self, path):
        process_event()
        string = 'UPDATE file_list SET modified_at=NULL WHERE path="%s"' % path

        self.query.exec_(string)
        self.emit_committed()

    def batch_insert(self, infos):
        self.start_batch()
        for info in infos:
            self.insert_record(info)
        self.end_batch()
        self.emit_committed()

    def batch_update(self, infos):
        self.start_batch()
        for info in infos:
            self.update_record(info)
        self.end_batch()
        self.emit_committed()

    def batch_delete(self, paths):
        self.start_batch()
        for path in paths:
            self.delete_record(path)
        self.end_batch()
        self.emit_committed()

DataStore = __DataStoreObject()

class __ConfigurationObject(QObject):
    have_updated = pyqtSignal()

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=None)
        self.query = QSqlQuery()

    def set_directory(self, directory):
        self.query.prepare('UPDATE configuration SET directory=:directory WHERE id=1')
        self.query.bindValue(':directory', directory)
        self.query.exec_()
        self.have_updated.emit()

    def get_directory(self):
        self.query.exec_('SELECT directory FROM configuration WHERE id=1')
        while self.query.next():
            return self.query.value(0)

Configuration = __ConfigurationObject()
