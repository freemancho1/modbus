from .class_test import CommonEngine

class AAEngine(CommonEngine):

    def __init__(self, params):
        super().__init__(params)

    def func_a(self):
        super().func_a()
        print('aaaaa')

    def func_b(self):
        print(f'AAEngine func_b: {self.params["attr1"]}')


class BBEngine(CommonEngine):

    def __init__(self, params):
        super().__init__(params)

    def func_a(self):
        super().func_a()
        print('bbbbbb')

    def func_b(self):
        print(f'BBEngine func_b: {self.params["attr1"]}')