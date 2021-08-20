from .common import CommonDevice

class ModbusDriver(CommonDevice):

    def __init__(self, args, log):
        print('Thermometer')
        super().__init__(args, log)