"""
This is where everything happens.
Uses the labels and color info from an arbitrary
image to create a relevant magic card.
"""

import math
import collections

def closest_color(red, green, blue):
  """
  Determines whether the RBG value is closer to white, blue
  green, red, black or not really any of them.
  """
  my_ycc = _ycc(red, green, blue)
  choices = [('red', _ycc(255, 0, 0)), ('blue', _ycc(0, 0, 255)), ('green', _ycc(0, 0, 204)), ('black', _ycc(0, 0, 0)), ('white', _ycc(255, 255, 255))]
  results = []
  for choice in choices:
    y1, cb1, cr1 = my_ycc
    y2, cb2, cr2 = choice[1]
    diff = math.sqrt(1.4*math.pow(y1-y2, 2) + .8*math.pow(cb1-cb2, 2) + .8*math.pow(cr1-cr2, 2))
    results.append((choice[0], diff))

  sorted_results = sorted(results, key=lambda x: x[1])
  best_match = sorted_results[0]
  if best_match[1] < 100:
    # 100 is kind of arbitrary...but need a way to get rid colors that 
    # are just not close to any other color
    return best_match[0]
  return None


def _ycc(r, g, b): # in (0,255) range
  """
  Converts RBG into ycc color space which should be predict colors
  """
  y = .299*r + .587*g + .114*b
  cb = 128 -.168736*r -.331364*g + .5*b
  cr = 128 +.5*r - .418688*g - .081312*b
  return y, cb, cr

def get_card_database():
  database = collections.defaultdict(list)
  cards_sample = open('large_sample_readable.cards', 'r')
  content = cards_sample.read()
  # the cards are split by \n\n from mtgencode
  cards = content.split('\n\n')
  real_cards = []
  possible_colors = {'R' : 'Red', 'U' : 'Blue', 'G' : 'Green', 'B' : 'Black', 'W' : 'White'}
  for card in cards:
    if '~~~~~~~~' in card:
      # not a real card, some kind of marker.
      continue
    real_cards.append(card)
    lines = card.split('\n')
    first_line = lines[0] # first line has mana cost info
    mana_cost = first_line.split(' ')[-1]

    colors = []
    for color in possible_colors:
      if color in mana_cost:
        colors.append(possible_colors[color])

    colors_string = ','.join(colors)
    database[colors_string].append(card)

  return database


class CardGenerator:

  def __init__(self, labels, color_info):
    self.labels = labels
    self.color_info = color_info
    self.generated = False

  def generate_card_color(self):
    # uses color info to get an appropriate color
    votes = collections.defaultdict(int)
    for single_color_info in self.color_info:
      rbg_values = single_color_info['color']
      color_vote = closest_color(rbg_values['red'], rbg_values['green'], rbg_values['blue'])
      votes[color_vote] += 1 * single_color_info['pixelFraction'] * single_color_info['score']
    sorted_votes = sorted(votes.items(), key=lambda x: x[1])
    if len(sorted_votes) > 1:
      best_match = sorted_votes[-1]
      self.color = best_match[0].capitalize()
      # should check for second best match for multi color?
    else:
      self.color = None

  def generate_playable_card(self):
    # uses color, and labels to generate a name and all relevant abilities
    self.name = "Maw of Kozilek"
    database = get_card_database()

    import random
    card = random.choice(database[self.color])
    lines = card.split('\n')
    name_and_mana_cost = lines[0].split()
    self.name = ' '.join(name_and_mana_cost[:-1])
    self.mana_cost = name_and_mana_cost[-1]
    self.type = lines[1]
    if 'creature' in self.type:
      self.rules = '\n'.join(lines[2:-1])
      self.power_toughness = lines[-1]
    else:
      self.rules = '\n'.join(lines[2:])
      self.power_toughness = None

  def generate_card_flavor_text(self):
    # uses the card name, and maybe labels or color to generate flavor
    self.flavor = "Lol flavor TODO"

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
    self.generate_playable_card()
    self.generate_card_flavor_text()
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

