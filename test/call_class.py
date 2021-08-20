import os, sys
# sys.path.append(os.path.abspath(__file__+'/../..'))
# sys.path.append(os.path.abspath(
#     os.path.join(os.path.expanduser('~'), 'projects/modbus')))

import importlib
# from .class_test.aaEngine import AAEngine

params = {"attr1": "attr1"}

# ae = AAEngine(params)
# ae = importlib.import_module('test.class_test.aaEngine.AAEngine')
# _ae = __import__('class_test.aaEngine', fromlist=['class_test.aaEngine'])
ae = __import__('class_test.aaEngine', fromlist=['class_test.aaEngine'])
ae = ae.AAEngine(params)
print(ae)
ae.func_a()

print('----------')
ae = __import__('class_test.aaEngine', fromlist=['class_test.aaEngine'])
ae = ae.BBEngine(params)
print(ae)
ae.func_a()

