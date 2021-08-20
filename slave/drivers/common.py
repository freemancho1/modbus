import time
import threading

from slave import slave_constants as CONST
from slave.slave_utils import DataMgt, DataBank

class CommonDevice:

    def __init__(self, args, log):
        self.args = args
        self.log = log
        self.DataBank = [DataBank() for _ in range(1)]

        gd_process = GenerationData(self.gen_data)
        gd_process.daemon = True
        gd_process.start()

    def chk_mbap_header(self, mbap_header):
        self.log.debug(f'++{mbap_header}')

    def gen_data(self):
        self.log.debug('-----------------------------')


class GenerationData(threading.Thread):

    def __init__(self, run_func):
        super().__init__()
        self.Run = run_func

    def run(self, *args):
        while True:
            self.Run()
            time.sleep(30)


