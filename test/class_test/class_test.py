class CommonEngine:

    def __init__(self, params):
        self.params = params


    def func_a(self):
        print(f'common func_a: {self.params["attr1"]}')
        self.func_b()

    def func_b(self):
        pass
