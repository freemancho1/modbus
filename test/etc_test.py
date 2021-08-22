import time
from datetime import datetime, timedelta
from random import randint

curr = datetime.now()
l_curr = f'{curr:%H.%M.%S}'
l_currr = [curr.hour, curr.minute, curr.second]
print(type(l_curr), l_curr, l_currr)