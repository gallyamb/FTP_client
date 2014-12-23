__author__ = 'Галлям'

import socket
import logging

from PyQt5 import QtCore

from switch_case import switch


logger = logging.getLogger(__name__)

standard_port = 54265


def get_port_as_tuple(port):
    first = port >> 8
    second = port % 256
    return first, second


class DataTransferProcess(QtCore.QThread):
    complete = QtCore.pyqtSignal([bytes], [bytes, str])
    error = QtCore.pyqtSignal(str)

    def __init__(self, ip: str=None, port: int=None):
        super().__init__()
        self.socket = socket.socket()
        self.is_passive = ip is not None or port is not None
        self.ip = ip
        self.port = port
        self.remote_socket = None
        logger.debug('IP: {0}'.format(self.ip))
        logger.debug('port: {0}'.format(self.port))

    @QtCore.pyqtSlot(tuple)
    def start_transfer(self, address: tuple):
        self.socket.connect(address)
        data = b''
        count = 2 ** 16
        tmp = self.socket.recv(count)
        while tmp:
            data += tmp
            tmp = self.socket.recv(count)
        self.complete[bytes].emit(data)

    def run(self):
        pass
        # if self.is_passive:
        #     logger.debug('in active mode')
        #     self.socket.bind((self.ip, self.port))
        #     self.socket.listen(1)
        #     sock, addr = self.socket.accept()
        #     self.remote_socket = sock
        # else:
        #     logger.debug('in passive mode')
        #     self.socket.connect((self.ip, self.port))
        #     self.remote_socket = self.socket
        # for case in switch(self.command):
        #     if case('MLSD'):
        #         self.download(False)
        #         break
        #     if case('RETR'):
        #         self.download(True)
        #         break
        #     if case('STOR'):
        #         self.upload
        #         break
        #     if case():
        #         break

    def upload(self):
        with open(self.filename, 'rb') as file:
            step = 2 ** 16
            pie = file.read(step)
            while pie:
                pie = file.read()
                self.socket.send(pie)

    def download(self, use_filename: bool):
        data = b''
        tmp = self.remote_socket.recv(2 ** 16)
        while tmp:
            data += tmp
            tmp = self.remote_socket.recv(2 ** 16)
        if use_filename:
            self.complete[bytes, str].emit(data, self.filename)
        else:
            self.complete[bytes].emit(data)
