class Geometry:
    def __init__(self):
        self.origin = [0,0,0]
        self.spacing = [0,0,0]
        self.matrix = None

    def index_to_world(self,index):
        pass

    def world_to_index(self,pos):
        pass

    def get_matrix(self):
        return self.matrix