from queue import Queue
from threading import Thread
import logging

from PyQt5 import QtCore

from core.downloader import Downloader
from core.protocol_interpreter import ProtocolInterpreter
from gui.model_view_components.directory_listing_handler import\
    DirectoryListingHandler
from gui.model_view_components.remote_filesystem_model import FileItem


logging.basicConfig(filename='log.txt', level=logging.DEBUG, filemode='w')
logger = logging.getLogger(__name__)

ftp_std_port = 21


class Core(QtCore.QObject):
    new_log = QtCore.pyqtSignal(str)
    already_connected = QtCore.pyqtSignal()
    hostname_not_specified = QtCore.pyqtSignal()
    update_local_model = QtCore.pyqtSignal()
    ready_to_read_dirlist = QtCore.pyqtSignal()
    update_remote_model = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.pi = ProtocolInterpreter(None, None)
        self.connected = False
        self._username = ""
        self._password = ""
        self._log = []
        self.active_mode = False
        self.current_dtp = None

        self.queue = Queue()

        def queue_controller():
            while True:
                if self.current_dtp is None:
                    item = self.queue.get()
                    item[0](*item[1])

        Thread(target=queue_controller, daemon=True).start()

    @QtCore.pyqtSlot()
    def on_log_read(self):
        del self._log[:]

    def read_log(self):
        return '\r\n'.join(self._log)

    def start_connecting(self, hostname, port, username, password):
        logger.debug('Core starting')

        if hostname == "":
            self.hostname_not_specified.emit()
            return
        if self.connected:
            self.already_connected.emit()
            return
        if port == "":
            port = ftp_std_port
        if username == "":
            username = "anonymous"

        self.pi = ProtocolInterpreter(hostname, port)
        self._connect_signals_to_slots()
        self._username = username
        self._password = password
        self.pi.start()
        self.connected = True
        logger.debug('Core started')

    @QtCore.pyqtSlot()
    def set_type_binary(self):
        self.pi.set_binary_type()

    def start_file_downloading(self, source_path: str, path_to_save: str,
                               filename: str):
        if self.current_dtp:
            self.queue.put((self.start_file_downloading,
                            (source_path, path_to_save, filename)))
            return
        logger.debug('file %s downloading started. destination: %s' %
                     (filename, path_to_save))

        self.pi.change_dir(source_path)

        thread = QtCore.QThread()

        downloader = Downloader(path_to_save, filename)

        self.current_dtp = True
        self.pi.passive_mode.connect(downloader.data_transfer_process
                                     .start_transfer)

        downloader.complete.connect(self.update_local_model)
        downloader.complete.connect(self.set_dtp_to_none)
        downloader.complete.connect(thread.quit)
        # downloader.start()
        downloader.moveToThread(thread)

        thread.start()

        self.pi.initiate_passive_mode()
        self.pi.download_file(filename)


    def set_dtp_to_none(self):
        self.current_dtp = None

    @QtCore.pyqtSlot(FileItem)
    def get_directory_list(self, parent: FileItem):
        if self.current_dtp is not None:
            self.queue.put((self.get_directory_list, (parent,)))
            return
        logger.debug('directory listing getting')

        path = parent.file_path
        logger.debug('path: %s' % path + '/')
        self.pi.change_dir(path)

        dlh = DirectoryListingHandler(parent)
        self.current_dtp = dlh
        self.pi.passive_mode.connect(dlh.data_transfer_process.start_transfer)
        dlh.complete.connect(self.update_remote_model)

        dlh.complete.connect(self.set_dtp_to_none)

        self.pi.initiate_passive_mode()

        self.pi.get_dirlist_in_passive()

    def _connect_signals_to_slots(self):
        logger.debug('Slots connecting')
        self.pi.username_required.connect(self._send_username)
        self.pi.password_required.connect(self._send_password)
        self.pi.buffer_changed.connect(self.print_log)

        self.pi.user_authorised.connect(self.set_type_binary)
        self.pi.user_authorised.connect(self.ready_to_read_dirlist)
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
