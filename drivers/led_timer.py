from datetime import datetime
from .common import CommonDriver

class ModbusDriver(CommonDriver):

    def __init__(self, device_info, product_info, log):
        super().__init__(device_info, product_info, log)


    def prev_write_multiple_coils(self):

        color_reg = [data for data in self.co if data['name'] == 'color'][0]
        if self.address == color_reg['addr']:
            if self.count == 3 and sum(self.value) == 1:
                di_color = [data for data in self.di if data['name'] == color_reg['name']][0]
                self.DataBank[self.uid].set_bits(di_color['addr'], self.value)
            else:
                self.exp_status = self.const.EXP_DATA_VALUE
                self.log.error(f'{self.const.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}, '
                               f'values={self.value}')

    def prev_write_multiple_registers(self):

        set_time_reg = [data for data in self.hr if data['name'] == 'set_time'][0]
        if self.address == set_time_reg['addr']:
            if self.count == 3:
                min_data, max_data = set_time_reg['min'], set_time_reg['max']
                chk_data = True
                for min, val, max in zip(min_data, self.value, max_data):
                    if not (min <= val <= max): chk_data = False
                if chk_data:
                    ir_set_time_reg = [data for data in self.ir if data['name'] == 'curr_time'][0]
                    self.DataBank[self.uid].set_words(ir_set_time_reg['addr']-self.ws_addr,
                                                      self.value)
                    self._time_manager(ir_set_time_reg, self.uid)

                    curr_time = datetime.now()
                    curr_word = [curr_time.hour, curr_time.minute, curr_time.second]
                    ir_chg_time_reg = [data for data in self.ir
                                             if data['name'] == 'chg_time'][0]
                    self.DataBank[self.uid].set_words(
                        ir_chg_time_reg['addr']-self.ws_addr, curr_word)
                else:
                    self.exp_status = self.const.EXP_DATA_VALUE
                    self.log.error(f'{self.const.EXP_DETAILS[self.exp_status]}, '
                                   f'function code={self.fc}, address={self.address}, '
                                   f'values={self.value}')
            else:
                self.exp_status = self.const.EXP_DATA_VALUE
                self.log.error(f'{self.const.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}, '
                               f'values={self.value}, count={self.count}')