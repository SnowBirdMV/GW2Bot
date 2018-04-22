class Item:
    def __init__(self, id, name, amount, image):
        self.name = name
        self.id = id
        self.amount = amount
        self.price = None
        self.image = image

    def setID(self, newid):
        self.id = newid
    def getID(self):
        return self.id

    def setAmount(self, newid):
        self.id = newid

    def getAmount(self):
        return self.amount



