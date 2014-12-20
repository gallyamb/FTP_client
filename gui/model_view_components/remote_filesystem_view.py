from PyQt5 import QtWidgets
from .remote_filesystem_model import \
    RemoteFileSystemModel

__author__ = 'Галлям'


class RemoteFileSystemExplorer(QtWidgets.QTreeView):
    def __init__(self):
        super().__init__()
        self.reinitialise()

    def reinitialise(self):
        model = RemoteFileSystemModel()
        self.setModel(model)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # self.setDragDropMode(QtCore.QAbstractItemModel)
