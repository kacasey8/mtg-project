"""
This is where everything happens.
Uses the labels and color info from an arbitrary
image to create a relevant magic card.
"""

class CardGenerator:

  def __init__(self, labels, color_info):
    self.labels = labels
    self.color_info = color_info
    self.generated = False

  def generate_card_color(self):
    # uses color info to get an appropriate color
    self.color = "Red"

  def generate_card_name(self):
    # uses color, and labels to generate a name
    self.name = "Maw of Kozilek"

  def generate_card_flavor_text(self):
    # uses the card name, and maybe labels or color to generate flavor
    self.flavor = "The Eldrazi make worse than ruins--they make a world where not even ruins stand."

  def generate_card_abilities(self):
    # uses color and name to generate all relevant abilities
    # of the card
    # this will generate rules_text, mana_cost, type info,
    # and power/toughness if relevant.

    self.rules = 'Devoid'
    self.mana_cost = '3R'
    self.type = 'Creature - Eldrazi Drone'
    self.power_toughness = '2/5'

  def generate(self):
    self.generate_card_color()
    self.generate_card_name()
    self.generate_card_flavor_text()
    self.generate_card_abilities()
    self.generated = True

  def __str__(self):
    if not self.generated:
      return "call generate first!"
    attributes = ["Color: %s" % self.color, "Name: %s" % self.name]
    attributes += ["Rules: %s" % self.rules, "Flavor: %s" % self.flavor]
    attributes += ["Mana cost: %s" % self.mana_cost, "Type: %s" % self.type]
    if self.power_toughness:
      attributes += ['Power/Toughness: %s' % self.power_toughness]
    return "\n".join(attributes)
