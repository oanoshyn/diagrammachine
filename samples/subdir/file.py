from samples.file import RandomClass1


class RandomClass2(RandomClass1):
    attr1: str
    attr2: str = "2"

    def func(self):
        pass

    def func2(self):
        pass


class RandomClass3(RandomClass1):
    attr1: str
    attr2: str = "2"

    def func(self):
        pass

    def func2(self):
        pass