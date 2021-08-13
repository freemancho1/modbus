from optparse import OptionParser


class SysOptions:

    def __init__(self):

        self._parser = OptionParser()

        self._parser.add_option('-H', '--host', dest='host', default='127.0.0.1',
                                help='디바이스 IP 주소를 기술한다. 기본값은 \'127.0.0.1\'이다.')
        self._parser.add_option('-P', '--port', dest='port', type=int, default=502,
                                help='디바이스 연결 PORT 번호를 기술한다. 기본값은 502이다.')
        self._parser.add_option('-D', '--device-info', dest='device_info_file_path', default='',
                                help='디바이스 정보파일을 기술한다.')

        (self._options, self._args) = self._parser.parse_args()

    def get_options(self):
        return self._options

    def get_agrs(self):
        return self._args

    def print_help(self):
        self._parser.print_help()