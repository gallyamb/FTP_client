from PyQt5 import QtCore
from core.data_transfer_process import DataTransferProcess

__author__ = 'root'


class Downloader(QtCore.QObject):
    complete = QtCore.pyqtSignal()

    def __init__(self, path_to_save: str, filename: str,
                 dt: DataTransferProcess=None):
        super().__init__()
        self.path_to_save = path_to_save
        self.filename = filename

        self.data_transfer_process = DataTransferProcess() if dt is None else dt
        self.data_transfer_process.ready.connect(self.start_downloading)

    def start_downloading(self):
        with open(self.path_to_save + '/' + self.filename, 'wb') as file:
            for data in self.data_transfer_process.download():
                file.write(data)
        self.complete.emit()