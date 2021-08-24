import time
from datetime import datetime, timedelta
from random import randint

class MyClass:

    aa = 10
    bb = 20

    def __init__(self):
        self.aa = 110
        self.bb = 120


my_class = MyClass
print(my_class.bb)
