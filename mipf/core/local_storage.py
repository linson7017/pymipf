from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type


T = TypeVar('T') 
class LocalStroageHandler(Generic[T]):
    def __init__(self,cls: Type[T]):
        super().__init__()
        self.rls = {}
        self.cls = cls
        
    def get_local_storage(self,renderer,*args, **kwargs):
        rid = id(renderer)
        ls = self.rls.get(rid)
        if not ls:
            ls = self.cls(*args, **kwargs)
            self.rls[rid] = ls
        return ls
    