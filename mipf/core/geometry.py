class Geometry:
    def __init__(self):
        self.origin = [0, 0, 0]
        self.spacing = [1, 1, 1]
        self.matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        self.bounds = [0, 0, 0, 0, 0, 0]

    def index_to_world(self, index):
        pass

    def world_to_index(self, pos):
        pass

    def get_matrix(self):
        return self.matrix

    def get_bounds(self):
        return self.bounds
