class Device:
    id = ""
    master = ("", 0)

    def __init__(self, id, master):
        self.id = id
        self.master = master

    # def execute(self):
    #

