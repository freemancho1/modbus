import time
from datetime import datetime, timedelta
from random import randint


m_list = [[1, 10], [11, 20], [21, 30], [31, 40]]
a = 11

idx = [i for i in range(len(m_list)) if m_list[i][0] <= a <= m_list[i][1]]

print(f'idx={idx}, len(idx)={len(idx)}, len(m_list)={len(m_list)}')