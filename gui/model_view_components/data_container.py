__author__ = 'Галлям'


class DataContainer:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)