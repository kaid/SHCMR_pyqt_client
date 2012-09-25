from PyQt4.QtCore import QObject, pyqtSignal, QEventLoop
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from PyQt4.QtGui import QApplication
from utils import *

_sql_file          = open('database.sql', 'r')
_setup_sql_strings = _sql_file.read().split(';')[0:-1]
_sql_file.close()

class __DataStoreObject(QObject):
    committed = pyqtSignal()

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.__init_database()
        self.query = QSqlQuery()
        self.__setup_database()

    def __init_database(self):
        self.database = QSqlDatabase.addDatabase('QSQLITE')
        self.database.setDatabaseName('database.db')
        self.database.open()

    def __setup_database(self):
        for string in _setup_sql_strings:
            self.query.exec_(string)

    def get(self, path):
        self.query.exec_('SELECT * FROM file_list WHERE path="%s"' % path)

        while self.query.next():
            return self.query

        return None

    def update_record(self, info):
        string = 'UPDATE file_list SET modified_at=%d, size=%d WHERE path="%s"' % (
            modified_at_of(info),
            info.size(),
            info.absoluteFilePath(), 
        )

        self.query.exec_(string)

    def insert_record(self, info):
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

    def delete_record(self, path):
        string = 'UPDATE file_list SET modified_at=NULL WHERE path="%s"' % path
        self.query.exec_(string)

    def batch_insert(self, infos):
        for info in infos:
            QApplication.processEvents(QEventLoop.AllEvents)
            self.insert_record(info)

        self.committed.emit()

    def batch_update(self, infos):
        for info in infos:
            QApplication.processEvents(QEventLoop.AllEvents)
            self.update_record(info)

        self.committed.emit()

    def batch_delete(self, paths):
        for path in paths:
            QApplication.processEvents(QEventLoop.AllEvents)
            self.delete_record(path)

        self.committed.emit()

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
