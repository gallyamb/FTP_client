__author__ = 'Галлям'

import socket
import logging

from PyQt5 import QtCore

from switch_case import switch


logger = logging.getLogger('dt')

standard_port = 54265


def get_port_as_tuple(port):
    first = port >> 8
    second = port % 256
    return first, second


class DataTransferProcess(QtCore.QThread):
    complete = QtCore.pyqtSignal([bytes], [bytes, str])
    error = QtCore.pyqtSignal(str)

    def __init__(self, ip: str, port: int,
                 command: str,
                 filename: str="new_file", in_passive_mode: bool=False):
        super().__init__()
        self.filename = filename
        self.socket = socket.socket()
        self.is_active = in_passive_mode
        self.ip = ip
        self.port = port
        if command is None:
            raise ValueError('"command" can not be None')
        self.command = command
        self.remote_socket = None
        logger.debug('IP: {0}'.format(self.ip))
        logger.debug('port: {0}'.format(self.port))

    def run(self):
        if self.is_active:
            logger.debug('in active mode')
            self.socket.bind((self.ip, self.port))
            self.socket.listen(1)
            sock, addr = self.socket.accept()
            self.remote_socket = sock
        else:
            logger.debug('in passive mode')
            self.socket.connect((self.ip, self.port))
            self.remote_socket = self.socket
        for case in switch(self.command):
            if case('MLSD'):
                self.download(False)
                break
            if case('RETR'):
                self.download(True)
                break
            if case('STOR'):
                self.upload
                break
            if case():
                break

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
