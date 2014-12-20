
__author__ = 'Галлям'

from enum import Enum
import logging

from PyQt5 import QtCore

from . import protocol_interpreter
from . import data_transfer_process
from gui.model_view_components.data_container import DataContainer


logging.basicConfig(filename='log.txt', level=logging.DEBUG, filemode='w')
logger = logging.getLogger('core')

ftp_std_port = 21


class Core(QtCore.QThread):
    new_log = QtCore.pyqtSignal(str)
    already_connected = QtCore.pyqtSignal()
    hostname_not_specified = QtCore.pyqtSignal()
    new_directory_list = QtCore.pyqtSignal(list)
    update_local_model = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.pi = protocol_interpreter.ProtocolInterpreter(None, None)
        self.connected = False
        self._log = []
        self._username = None
        self._password = None
        self.last_command = None
        self.upload_file_path = None
        self.active_mode = False
        self.dts = []
        self.dt_complete_handlers = {
            "RETR": self.handle_file_download,
            "MLSD": self.handle_mlsd,
            "STOR": None,
            "LIST": None
        }

    @QtCore.pyqtSlot(str, str)
    def upload_file(self, source_path, destination):
        self.upload_file_path = source_path
        self.last_command = 'STOR'
        self.pi.initiate_passive_mode()
        self.pi.push(b'STOR ' + destination.encode() + b'\r\n')


    @QtCore.pyqtSlot()
    def on_log_read(self):
        del self._log[:]

    def read_log(self):
        return '\r\n'.join(self._log)

    def start_connecting(self, hostanme, port, username, password):
        logger.debug('Core starting')

        if hostanme == "":
            self.hostname_not_specified.emit()
            return
        if self.connected:
            self.already_connected.emit()
            return
        if port == "":
            port = ftp_std_port
        if username == "":
            username = "anonymous"

        self.pi = protocol_interpreter.ProtocolInterpreter(hostanme, port)
        self._connect_signals_to_slots()
        self._username = username
        self._password = password
        self.pi.start()
        self.connected = True
        logger.debug('Core started')

    @QtCore.pyqtSlot()
    def set_type_binary(self):
        self.pi.set_binary_type()

    def start_file_downloading(self, path: str, path_to_save: str):
        self.last_command = 'RETR'
        self.pi.initiate_passive_mode()
        self.pi.push(b'RETR ' + path.encode() + b'\r\n')
        self.save = path_to_save + '/' + path.split('/')[-1]

    def get_directory_list(self, path: str=""):
        logger.debug('directory listing getting')
        logger.debug('path: %s' % path)
        self.pi.push(b'CWD ' + path.encode() + b'\r\n')
        self.last_command = "MLSD"
        self.pi.initiate_passive_mode()
        self.pi.get_dirlist_in_passive()

    @QtCore.pyqtSlot(bytes)
    def handle_mlsd(self, data: bytes):
        result = []
        for line in data.decode().split('\n'):
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
        logger.debug('new directory listing received')
        self.new_directory_list.emit(result)

    @QtCore.pyqtSlot(bytes, str)
    def handle_file_download(self, data: bytes, filename: str):
        with open(self.save, 'wb') as file:
            file.write(data)
        self.update_local_model.emit()

    def initiate_data_transfer_process(self, address: tuple, in_passive: bool):
        dt = data_transfer_process.\
            DataTransferProcess(address[0], address[1],
                                self.last_command,
                                self.upload_file_path,
                                in_passive_mode=in_passive)
        dt.complete[bytes].connect(self.handle_mlsd)
        dt.complete[bytes, str].connect(self.handle_file_download)
        self.last_command = None
        dt.start()
        self.dts.append(dt)

    def start_data_transfer(self, address: tuple):
        self.initiate_data_transfer_process(address, False)

    def _connect_signals_to_slots(self):
        logger.debug('Slots connecting')
        self.pi.username_required.connect(self._send_username)
        self.pi.password_required.connect(self._send_password)
        self.pi.buffer_changed.connect(self.print_log)

        self.pi.user_authorised.connect(self.get_directory_list)
        self.pi.user_authorised.connect(self.set_type_binary)
        self.pi.passive_mode.connect(self.start_data_transfer)
        logger.debug('Slots connected')

    @QtCore.pyqtSlot(bool)
    def set_connected(self, is_connected):
        self.connected = is_connected

    @QtCore.pyqtSlot()
    def _send_username(self):
        logger.debug('Username sent')
        self.pi.send_username(self._username)

    @QtCore.pyqtSlot()
    def _send_password(self):
        logger.debug('Password sent')
        self.pi.send_password(self._password)

    @QtCore.pyqtSlot(list)
    def print_log(self, log: list):
        self._log.extend(log)
        self.new_log.emit(self.read_log())
