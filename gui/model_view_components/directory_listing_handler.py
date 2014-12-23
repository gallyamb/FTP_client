from PyQt5 import QtCore
from gui.model_view_components.remote_filesystem_model import FileItem, logger
from core.data_transfer_process import DataTransferProcess
from gui.model_view_components.data_container import DataContainer

__author__ = 'Галлям'


class DirectoryListingHandler(QtCore.QObject):
    complete = QtCore.pyqtSignal()

    def __init__(self, parent: FileItem, dt: DataTransferProcess):
        super().__init__()
        self.parent = parent
        self.data_transfer_process = dt
        self.data_transfer_process.complete[bytes].connect(self.process_dir_list)
        self.data_transfer_process.start()

    @QtCore.pyqtSlot(bytes)
    def process_dir_list(self, data: bytes):
        result = []
        for line in data.decode().split('\r\n'):
            if line == "":
                continue
            args = line.split(";")
            filename = args[-1]
            properties = {}
            for kv in [arg.split("=") for arg in args[:-1]]:
                properties[kv[0]] = kv[1]
            properties['name'] = filename
            dir_model_item = DataContainer(**properties)
            result.append(dir_model_item)
        self.handle_directory_list(result)

    @staticmethod
    def get_modified_date(item):
        year = int(item.modify[:4])
        month = int(item.modify[4:6])
        day = int(item.modify[6:8])
        date = QtCore.QDate(year, month, day)
        hour = int(item.modify[8:10])
        minute = int(item.modify[10:12])
        second = int(item.modify[-2:])
        time = QtCore.QTime(hour, minute, second)
        date_time = QtCore.QDateTime(date, time)
        return date_time

    @QtCore.pyqtSlot(list)
    def handle_directory_list(self, directory_items: list):
        logger.debug('directory listing handling')
        if self.parent is None:
            raise Exception('No fetched item to associate with')
        for item in directory_items:
            if item.type == 'pdir' or item.type == 'cdir':
                continue

            date_time = self.get_modified_date(item)
            is_dir = item.type == 'dir'
            file_path = self.parent.file_path + '/%s' % item.name[1:]

            item_to_add = FileItem(file_path,
                                   is_dir,
                                   self.parent,
                                   item.size if not is_dir else 0,
                                   date_time)
            self.parent.add_child(item_to_add)
        self.sort()
        self.complete.emit()

    def sort(self):
        self.parent.children \
            .sort(key=lambda file_item:
        (file_item.type, file_item.file_name, file_item.size))
        for index in range(self.parent.child_count()):
            self.parent.children[index].row = index

    def __hash__(self):
        return hash(self.parent)


