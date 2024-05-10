from typing import Any

from samples.subdir.file import RandomClass2


class RandomClass1[str, int]:
    attr1: str
    attr2: str = "2"
    attr3 = [1,2,3,4]
    attr4 = RandomClass2()

    def __init_(self):
        self.instance_attribute: int = 1
        self.instance_attribute2: str | int | Any = 1