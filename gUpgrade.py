class guildUpgrade:
    def __init__(self, id, name, ingredients, level, prerequisites, type, description, experience):
        self.id = id
        self.name = name
        self.ingredients = ingredients
        self.level = level
        self.prerequisites = prerequisites
        self.type = type
        self.description = description
        self.experience = experience
        self.totalPrice = None
        self.curentPrice = None

    def setID(self, newid):
        self.id = newid

    def addIngredient(self, ingredient, amount):
        if ingredient in self.ingredients:
            print(ingredient, " already in dictionary for id ", self.id)
        else:
            self.ingredients[ingredient] = amount

    def __str__(self):
        returnString = ""


