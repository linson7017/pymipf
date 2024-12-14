from collections import defaultdict
from mipf.core.mapper import *

class MapperManager:
    """
    Mapper manager.
    """

    def __init__(self):
        self.mappers = defaultdict(dict)
        self._next_id=0
        
    def set_mapper(self, node, mapper, mapper_type):
        self.mappers[node.id][mapper_type] = mapper
        mapper.set_node(node)


    def get_mapper(self, node, mapper_type):
        node_mapper = self.mappers.get(node.id)
        if node_mapper:
            return node_mapper.get(mapper_type)
        else:
            return None


mapper_manager = MapperManager()
