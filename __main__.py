#!/usr/bin/env python
import sys
from PyQt4.QtGui import QApplication, QIcon
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from models import Configuration
from views import MyWindow, FileTransferStatusBar, TrayIcon

if __name__ == '__main__':
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("database.db")
    db.open()
    q = QSqlQuery()
    q.exec_('CREATE TABLE IF NOT EXISTS file_list (\
               id          INTEGER PRIMARY KEY AUTOINCREMENT,\
               status      BOOL DEFAULT 1 CHECK (status = 0 OR status = 1),\
               name        VARCHAR(255) NOT NULL,\
               size        INTEGER,\
               path        VARCHAR(255) UNIQUE,\
               is_dir      BOOL DEFAULT 0 CHECK (status = 0 OR status = 1),\
               modified_at DATETIME\
             )')

    q.exec_('CREATE TABLE IF NOT EXISTS configuration (\
               id        INTEGER PRIMARY KEY AUTOINCREMENT,\
               directory VARCHAR(255)\
             )')
    # q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(1, 1, \'东方风神录.rar\',   348127232)')
    # q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(2, 1, \'旅途之中.mp3\',     4194304)')
    # q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(3, 1, \'zurich.mp4\',      9101244)')
    # q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(4, 1, \'armageddon.jpg\',  401244)')
    # q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(5, 0, \'larmageddon.jpg\', 401240)')
    q.exec_('INSERT INTO configuration (id) VALUES(1)')
    q.exec_('commit')

    config = Configuration()
    window = MyWindow(config)
    window.resize(800, 400)
    window.show()
    tray = TrayIcon(app, config, parent=app)
    tray.show()
    app.exec_()
    tray = None
    sys.exit()

