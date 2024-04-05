import samples.file as test


class RandomClass2:
    attr1: dict[str, int]
    attr2: test.RandomClass1 = None
    attr3: str | int | float = None
    attr4 = 1
    attr5 = [1,2,3,4]
    attr6 = test.RandomClass1()


class RandomClass3(test.RandomClass1):
    attr1: str
    attr2: str = "2"
    def __init__(self, a: int):
        self.a: int = a

    def func(self):
        pass

    def func2(self):
        pass

class RandomClass4(test.RandomClass1):
    attr1: str
    attr2: str = "2"
    attr3: str = "3"

    def func(self):
        pass

    def func2(self):
        pass
