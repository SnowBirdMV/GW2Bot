class TreasuryItem:
    def __init__(self, id, name, totalAmount, curentAmount, item):
        self.name = name
        self.id = id
        self.totalAmount = totalAmount
        self.curentAmount = curentAmount
        self.price = None
        self.item = item

    def setID(self, newid):
        self.id = newid
    def getID(self):
        return self.id

    def setAmount(self, newid):
        self.id = newid

    def getAmount(self):
        return self.amount



