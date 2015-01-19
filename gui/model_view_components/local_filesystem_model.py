import os

__author__ = 'Галлям'

from PyQt5 import QtWidgets, QtCore


class LocalFileSystemModel(QtWidgets.QDirModel):
    file_downloading = QtCore.pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot
                       | QtCore.QDir.Drives | QtCore.QDir.Files)
        self.setSorting(QtCore.QDir.DirsFirst | QtCore.QDir.IgnoreCase |
                        QtCore.QDir.Name)
        self.setReadOnly(False)

    def dropMimeData(self, mime_data: QtCore.QMimeData,
                     drop_actions: QtCore.Qt.DropActions,
                     row: int, column: int,
                     index: QtCore.QModelIndex):
        if not index.isValid() or not drop_actions & QtCore.Qt.CopyAction:
            return False
        urls = mime_data.urls()
        root = mime_data.property('root')
        print(root)
        for url in urls:
            source_path = os.path.dirname(url.path())
            filename = os.path.basename(url.path())
            print(source_path)
            print(filename)
            target_path = self.filePath(index)
            print(target_path)
            if root != '':
                target_path += source_path[source_path.index(root):]
                print(target_path)
            self.file_downloading.emit(source_path, target_path, filename)
        return True

    def supportedDropActions(self) -> QtCore.Qt.DropActions:
        return QtCore.Qt.CopyAction

    def supportedDragActions(self) -> QtCore.Qt.DropActions:
        return QtCore.Qt.CopyAction
