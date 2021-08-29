from datetime import datetime
from .common import CommonDriver

class ModbusDriver(CommonDriver):

    def __init__(self, dev_info, log):
        super().__init__(dev_info, log)


    def _prev_write_multiple_coils(self):

        # 전처리 #1
        # - CO의 'color'값을 그룹으로 변경하면,
        # - 정상적인 데이터 형태(하나만 True)인지 확인하고, 그 값을 DI의 'color'에 저장
        self._pwmc_01_chg_color()


    def _prev_write_multiple_registers(self):

        # 전처리 #1
        # - HR에 'set_time'값을 변경하면,
        # - IR의 'curr_time'값을 변경하고, 'chg_time'에 값 변경 시간(현재시간)을 저장
        self._pwmr_01_chg_curr_time()



    def _pwmc_01_chg_color(self):
        # 현재 트랜잭션의 주소가 CO 'color'의 주소와 비교하기 위해,
        # CO에서 이름이 'color'인 코일을 찾고,
        co_color = {}
        for data in self.di.data[self.const.DATA_CO]:
            if data['name'] == 'color':
                co_color = data
                break
        # 그 코일의 주소와 현재 트랜잭션의 주소를 비교해, 같으면,
        if self.ti.addr == co_color.get('addr', self.const.ERR_INT):
            # 트랜잭션의 데이터 길이와 코일의 기본값 길이가 같거나,
            # 트랜잭션의 입력값이 [1,0,0],[0,1,0],[0,0,1]인 경우를 비교([1,1,0]은 올 수 없음)
            # 길이나 값이 정상이면,
            if self.ti.cnt == len(co_color.get('default',[])) \
                and sum(self.ti.value) == 1:
                # DI의 'color'의 주소를 찾고
                color_di_addr = self.const.ERR_INT
                for data in self.di.data[self.const.DATA_DI]:
                    if data['name'] == co_color['name']:
                        color_di_addr = data.get('addr', self.const.ERR_INT)
                        break
                # DI 'color'의 주소가 정상이면, 해당 주소에 컬러값 설정하고,
                if color_di_addr != self.const.ERR_INT:
                    self.DataBank[self.ti.uid].set_bits(color_di_addr, self.ti.value)
                # DI 'color'의 주소가 정상이 아니면, 에러처리,
                else:
                    self.ti.es = self.const.EXP_DATA_ADDRESS
                    self.ti.em = f'fc={self.ti.fc}, addr={self.ti.addr}, ' \
                                 f'DI color addr error.'
            # 길이나 값에 오류가 있으면,
            else:
                self.ti.es = self.const.EXP_DATA_VALUE
                self.ti.em = f'CO color default values or TX input values error. ' \
                             f'color default={co_color.get("default",[])}, ' \
                             f'TX input={self.ti.value}'

    def _pwmr_01_chg_curr_time(self):
        # 현재 트랜잭션의 주소가 HR의 'set_time' 레지스터의 주소와 비교하기 위해,
        # HR에서 이름이 'set_time'인 레지스터를 찾고,
        hr_set_time = {}
        for data in self.di.data[self.const.DATA_HR]:
            if data['name'] == 'set_time':
                hr_set_time = data
                break
        # 그 레지스터의 주소와 현재 트랜잭션의 주소를 비교해, 같으면,
        if self.ti.addr == hr_set_time.get('addr', self.const.ERR_INT):
            # 그 레지스터의 'default'의 값 갯 수와 현재 트랜잭션의 입력값 갯 수를 비교함.
            # 그 레지스터에 'default'가 없으면 '[]'으로 비교(당연히 조건 만족하지 않음)
            # 레지스터 'default'값의 길이와 트랜잭션 입력값의 길이가 같을 때,
            if self.ti.cnt == len(hr_set_time.get('default', [])):
                # 그 레지스터의 min/max값과 현재 트랜잭션으로 들어온 값 비교(리스트)
                chk_data = True
                min_data, max_data = hr_set_time.get('min',[]), hr_set_time.get('max',[])
                # 그 레지스터의 값을 갖져와 길이를 비교
                if not (len(min_data) == len(self.ti.value) == len(max_data)):
                    chk_data = False
                else:
                    for min, val, max in zip(min_data, self.ti.value, max_data):
                        # 길이가 같으니 트랜잭션 입력값이 min/max 사이에 있나 비교
                        if not (min <= val <= max):
                            chk_data = False
                # 트랜잭션 입력값과 입력값의 길이가 모두 HR 레지스터를 만족하기 때문에
                # IR의 'curr_time'값 변경 작업을 수행함.
                if chk_data:
                    ir_set_time = {}
                    # IR에서 이름이 'curr_time'인 레지스터를 찾고,
                    for data in self.di.data[self.const.DATA_IR]:
                        if data['name'] == 'curr_time':
                            ir_set_time = data
                            break
                    # 찾은(혹은 못찾은) IR 레지스터에서 주소값을 가져옴(못찾은 경우 ERR_INT값)
                    curr_addr = ir_set_time.get('addr', self.const.ERR_INT)
                    # IR 레지스터에서 'curr_time'의 주소를 찾지 못하면, 에러처리
                    if curr_addr == self.const.ERR_INT:
                        self.ti.es = self.const.EXP_DATA_ADDRESS
                        self.ti.em = f'IR curr_time addr setting error.'
                    # IR 레지스터에서 'curr_time'의 주소를 찾으면,
                    # IR 레지스터의 값을 변경하고, 해당 타이머 재 설정(_time_manager실행)
                    else:
                        self.DataBank[self.ti.uid].set_words(curr_addr-self.di.w_addr,
                                                             self.ti.value)
                        self._time_manager(ir_set_time, self.ti.uid)
                        # IR 레지스터의 'curr_time'을 정상적으로 재 설정했으니,
                        # IR 레지스터의 'chg_time(curr_time 변경 시간)'을 현재시간으로 설정
                        # IR 레지스터에서 'chg_time'의 주소값 가져오기
                        chg_addr = self.const.ERR_INT
                        for data in self.di.data[self.const.DATA_IR]:
                            if data['name'] == 'chg_time':
                                chg_addr = data.get('addr', self.const.ERR_INT)
                        # IR 레지스터에 'chg_time'의 주소값이 없으면('chg_time'의 레지스터가 없으면)
                        if chg_addr == self.const.ERR_INT:
                            self.ti.es = self.const.EXP_DATA_ADDRESS
                            self.ti.em = f'IR chg_time addr setting error.'
                        # IR 레지스터에서 'chg_time'의 주소값을 정상적으로 가져오면,
                        else:
                            chg_time = datetime.now()
                            chg_time_words = [chg_time.hour, chg_time.minute, chg_time.second]
                            # 메모리상의 주소를 찾아 변경시간값 저장
                            self.DataBank[self.ti.uid].set_words(chg_addr-self.di.w_addr,
                                                                 chg_time_words)
                # 트랜잭션의 입력값이나 그 길이가 HR 레지스터를 만족하지 않아 에러처리
                else:
                    self.ti.es = self.const.EXP_DATA_VALUE
                    self.ti.em = f'IR/HR set_time min/max setting or input value error.' \
                                 f'min={min_data}, max={max_data}, in={self.ti.value}'
            # HR 'set_time' 레지스터 'default'값의 길이와 트랜잭션 입력값의 길이가 다를 때,
            else:
                self.ti.es = self.const.EXP_DATA_VALUE
                self.ti.em = f'HR curr_time default value length and ' \
                             f'TX data count not match. ' \
                             f'HR len={len(hr_set_time.get("default", []))}, ' \
                             f'TX cnt={self.ti.cnt}'
