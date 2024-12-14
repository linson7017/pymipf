class DataManager:
    """
    Data manager.
    """

    def __init__(self):
        self.dataset = {}

    def add_data(self, data, uid):
        self.dataset[uid] = data

    def remove_data(self, uid):
        self.dataset.pop(uid)
        
    def get_data(self, uid):
        return self.dataset.get(uid)


data_manager = DataManager()
