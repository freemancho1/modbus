# 프로그램 상수
MBAP_HEAD_SIZE = 7
MIN_DATA_LEN = 2
MAX_DATA_LEN = 256
MAX_FUNC_CODE = 0x7F    # 127

MIN_BIT_CNT = 0x0001
MAX_BIT_CNT = 0x07D0    # 2000
MAX_BIT_0F_CNT = 0x07B0 # 1968 (2000에서 4Byte(32) 제거)
MIN_WORD_CNT = 0x0001
MAX_WORD_CNT = 0x007D   # 125
MAX_WORD_10_CNT = 0x007B # 123 (125에서 2개 제거)

# 모드버스 형식
MODBUS_TCP = 1
MODBUS_RTU = 2

# 모드버스 기능 코드
READ_COILS = 0x01
READ_DISCRETE_INPUTS = 0x02
READ_HOLDING_REGISTERS = 0x03
READ_INPUT_REGISTERS = 0x04
WRITE_SINGLE_COIL = 0x05
WRITE_SINGLE_REGISTER = 0x06
WRITE_MULTIPLE_COILS = 0x0F
WRITE_MULTIPLE_REGISTERS = 0x10
MODBUS_ENCAPSULATED_INTERFACE = 0x2B

# 모드버스 에러 코드
EXP_NONE = 0x00
EXP_ILLEGAL_FUNCTION = 0x01
EXP_DATA_ADDRESS = 0x02
EXP_DATA_VALUE = 0x03
EXP_SLAVE_DEVICE_FAILURE = 0x04
EXP_ACKNOWLEDGE = 0x05
EXP_SLAVE_DEVICE_BUSY = 0x06
EXP_NEGATIVE_ACKNOWLEDGE = 0x07
EXP_MEMORY_PARITY_ERROR = 0x08
EXP_GATEWAY_PATH_UNAVAILABLE = 0x0A
EXP_GATEWAY_TARGET_DEVICE_FAILED_TO_RESPOND = 0x0B

# 간단한 에러 메세지
EXP_TXT = {
    EXP_NONE: '에러 없음',
    EXP_ILLEGAL_FUNCTION: '승인되지 않는 기능',
    EXP_DATA_ADDRESS: '승인되지 않는 데이터 주소',
    EXP_DATA_VALUE: '승인되지 않는 데이터 값',
    EXP_SLAVE_DEVICE_FAILURE: '디바이스 장치 오류',
    EXP_ACKNOWLEDGE: '처리중 메시지(오류 아님)',
    EXP_SLAVE_DEVICE_BUSY: '디바이스 장치 사용 중',
    EXP_NEGATIVE_ACKNOWLEDGE: '디바이스 프로그래밍 불가 오류',
    EXP_MEMORY_PARITY_ERROR: '메모리 패리티 오류',
    EXP_GATEWAY_PATH_UNAVAILABLE: '게이트웨이 경로를 사용할 수 없음',
    EXP_GATEWAY_TARGET_DEVICE_FAILED_TO_RESPOND: '게이트웨이 대상 장치의 응답 오류'
}
# 에러 메세지
EXP_DETAILS = {
    EXP_NONE: '최근(마지막) 요청에서 에러가 발생하지 않았습니다.',
    EXP_ILLEGAL_FUNCTION: '수신된 기능코드가 디바이스에서 인식(또는 허용)하지 않습니다.',
    EXP_DATA_ADDRESS: '요청한 일부 또는 모든 주소 중 디바이스에 없는 주소가 존재합니다.',
    EXP_DATA_VALUE: '디바이스에서 허용하지 않는 값입니다.',
    EXP_SLAVE_DEVICE_FAILURE: '디바이스가 요청된 작업을 처리하는 동안 복구할 수 없는 오류가 발생했습니다.',
    EXP_ACKNOWLEDGE: '디바이스가 요청 받은 작업을 처리하는데 오랜 시간이 걸릴 때, '
                     '마스터에서 시간초과 오류가 발생하는 것을 방지하기 위해 보내는 메시지입니다(오류 아님). '
                     '마스테는 처리 완료 여부를 결정하기 위해 \'Poll Program Complete\'메시지를 보낼 수 있습니다.',
    EXP_SLAVE_DEVICE_BUSY: '디바이스가 이전 요청을 처리하고 있습니다.(마스터는 나중에 다시 요청해야 합니다.)',
    EXP_NEGATIVE_ACKNOWLEDGE: '디바이스는 프로그래밍 기능을 수행할 수 없습니다. '
                              '마스터는 디바이스에 진단 또는 오류 정보를 요청해야 합니다.',
    EXP_MEMORY_PARITY_ERROR: '디바이스가 메모리에서 패리티 오류를 감지했습니다. 마스터는 재요청을 시도할 수 있습니다.',
    EXP_GATEWAY_PATH_UNAVAILABLE: '모드버스 통신용으로 구성된 게이트웨이가 잘못 구성되었습니다.',
    EXP_GATEWAY_TARGET_DEVICE_FAILED_TO_RESPOND: '게이트웨이에 연결된 디바이스가 마스터의 요청에 응답하지 않을 때 전송됩니다.'
}

# 모드버스 에러 코드
MB_NO_ERR = 0
MB_RESOLVE_ERR = 1
MB_CONNECT_ERR = 2
MB_SEND_ERR = 3
MB_RECV_ERR = 4
MB_TIMEOUT_ERR = 5
MB_FRAME_ERR = 6
MB_EXCEPT_ERR = 7
MB_CRC_ERR = 8
MB_SOCK_CLOSE_ERR = 9

# 모드버스 에러 메세지
MB_ERR_TXT = {
    MB_NO_ERR: '오류 없음',
    MB_RESOLVE_ERR: '이름 확인 오류',
    MB_CONNECT_ERR: '통신 오류',
    MB_SEND_ERR: '소켓 전송 오류',
    MB_RECV_ERR: '소켓 수신 오류',
    MB_TIMEOUT_ERR: '수신시간 초과 오류',
    MB_FRAME_ERR: '데이터 형식 오류',
    MB_EXCEPT_ERR: '모드버스 예외 발생',
    MB_CRC_ERR: '수신 데이터의 CRC 데이터 오류',
    MB_SOCK_CLOSE_ERR: '소켓 닫힘 오류'
}