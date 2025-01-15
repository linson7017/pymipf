from abc import ABC, abstractmethod

 
class LocalStroageHandler():
    def __init__(self,cls):
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
    