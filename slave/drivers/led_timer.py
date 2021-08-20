from .common import CommonDevice

class ModbusDriver(CommonDevice):

    def __init__(self, args, log):
        print('LED TIMER')
        super().__init__(args, log)