from .common import CommonDriver

class ModbusDriver(CommonDriver):

    def __init__(self, device_info, log):
        super().__init__(device_info, log)