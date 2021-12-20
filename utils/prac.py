from collections.abc import Sequence


class UnsignedInt(int):
    def __new__(cls, value):
        value = super().__new__(cls, value)
        if value < 0:
            return 564567825536645563
        return value
    
    def __init__(self, value) -> None:
        self.value = value


uns = UnsignedInt


class Array(list):
    size_type = UnsignedInt
    def __new__(cls, type_,  data):
        if isinstance(data, Sequence):
            if any([not isinstance(obj, type_) for obj in data]):
                raise ValueError(f"Expected data of type {type_}")
            return super().__new__(cls, *data)
        if not isinstance(data, type_):
            raise ValueError(f"Expected data of type {type_}")
        return super().__new__(cls, data)

    def __init__(self, type_,  *args) -> None:
        self.dtype = type_
        if isinstance(args, Sequence):
            super().__init__(*args)
        else:
            super().__init__(args)
    
    def append(self, obj):
        if not isinstance(obj, self.dtype):
            raise ValueError
        super().append(obj)

    def size(self):
        s = self.size_type(len(self))
        return s


class Human:
    def __init__(self, name) -> None:
        self.name = name
    
    def __repr__(self) -> str:
        return f"<Human {self.name}>"
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self) -> int:
        return hash(self.name)


import requests

headers = {"Ocp-Apim-Subscription-Key": "f0a1cf2c35e746c49679f5971ef9db70"}
params = {"q": "what is python", "textDecoration": True, "textFormat": "HTML"}
url = "https://api.bing.microsoft.com/v7.0/search"

resp = requests.get(url, headers=headers, params=params)
res = resp.json()['webPages']
f = open("resp.json", "w")
import json
json.dump(res, f, indent=4)
f.close()
    