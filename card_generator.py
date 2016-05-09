"""
This is where everything happens.
Uses the labels and color info from an arbitrary
image to create a relevant magic card.
"""

import collections
import random
import colorsys

def closest_color(red, green, blue):
  """
  Determines whether the RBG value is closer to white, blue
  green, red, black or not really any of them.
  Theory taken from
  http://stackoverflow.com/questions/8457601/how-can-i-classify-some-color-to-color-ranges
  Testing on http://hslpicker.com/#7cb184 to figure out better boundaries
  """
  hue, lightness, saturation = colorsys.rgb_to_hls(red*1.0/255, green*1.0/255, blue*1.0/255)
  if lightness > 0.8:
    # fairly white, check to see if saturation is strong
    # enough to bring out a color.
    if saturation < 0.9:
      return 'White'

  if lightness < 0.2:
    # if lightness is low, there still might be enough saturation
    # to see the color
    if saturation + 5*lightness < 1.5:
      # at .5 saturation and .2 lightness you can still see the underlying color
      # similarly for 1.0 saturation and .11 lightness
      # anything lower will just look black
      return 'Black'

  if saturation < 0.25:
    if saturation > .2:
      # saturation is low, but is ok.
      if lightness > .7 or lightness < .3:
        # lightness too extreme -> washed out color that won't come through
        return 'Devoid'
      # if lightness is normal then color can come through
    elif saturation > 1.:
      # saturation is very low, but might be possible to see color
      if lightness > .6 or lightness < .4:
        # low saturation and not perfect lightness means color won't come through
        return 'Devoid'
      # if lightness is close to median then color can come through
    else:
      # saturation is too low. Color will look very washed out.
      return 'Devoid'

  hue_360_scale = hue * 360

  # the first 'Devoid' here is Orange-Yellow. The second is Purple.
  mappings = [('Red', 40), ('Devoid', 80), ('Green', 170), ('Blue', 230), ('Devoid', 290), ('Red', 360)]
  for color_name, maximum_hue in mappings:
    if hue_360_scale <= maximum_hue:
      return color_name
  return 'Devoid'

def get_card_database():
  """
  Loads in a bunch of cards we have pre generated.
  We'll sort the cards into what color they are, and then
  attempt to grab one of these cards as a base for the card we are generating.

  This assumes the database of cards is saved at 'large_sample_readable.cards'
  """
  filename = 'large_final_sample_readable.cards'
  database = collections.defaultdict(list)
  cards_sample = open(filename, 'r')
  content = cards_sample.read()
  # the cards are split by \n\n from mtgencode
  cards = content.split('\n\n')
  possible_colors = {'R' : 'Red', 'U' : 'Blue', 'G' : 'Green', 'B' : 'Black', 'W' : 'White'}
  for card in cards:
    if '~~~~~~~~' in card:
      # not a real card, some kind of marker.
      continue
    lines = card.split('\n')
    first_line = lines[0] # first line has mana cost info
    mana_cost = first_line.split(' ')[-1]

    colors = []
    # stable order with the sort
    keys = sorted(possible_colors.keys())
    for color in keys:
      if color in mana_cost:
        colors.append(possible_colors[color])

    colors_string = ','.join(colors)
    database[colors_string].append(card)

  return database

def get_flavor_database(filename):
  """
  Loads in a bunch of flavor texts we have pre generated.
  We'll attempt to grab one of these that is related to the image
  we are generating from.

  This assumes the database of flavor is saved at 'legacy_flavor.txt'
  """
  database = []
  flavor = open(filename, 'r')
  content = flavor.read()
  # the flavor is split by \n\n from mtgencode
  flavors = content.split('\n\n')
  for flavor in flavors:
    if '~~~~~~~~' in flavor:
      # not a real card, some kind of marker.
      continue
    flavor = flavor.replace('|', '')
    flavor = flavor.replace('`', '')
    database.append(flavor)

  return database


class CardGenerator:

  def __init__(self, labels, color_info, debug=False, flavor_database='real'):
    self.labels = labels
    self.color_info = color_info
    self.generated = False
    self.debug = debug
    self.flavor_database = flavor_database

  def generate_card_color(self):
    # uses color info to get an appropriate color
    votes = collections.defaultdict(int)
    for single_color_info in self.color_info:
      rbg_values = single_color_info['color']
      color_vote = closest_color(rbg_values['red'], rbg_values['green'], rbg_values['blue'])
      if color_vote == 'Devoid':
        continue
        # just ignore devoid for now, we'd rather see colors get chosen.
      votes[color_vote] += 1 * single_color_info['pixelFraction'] * single_color_info['score']

    sorted_votes = sorted(votes.items(), key=lambda x: x[1])
    if self.debug:
      print "Votes for color choice: %s\n" % sorted_votes
    if len(sorted_votes) > 1:
      best_match = sorted_votes[-1]
      self.color = best_match[0].capitalize()
      if self.debug:
        print "Color chosen: %s\n" % self.color
      # should check for second best match for multi color?
    else:
      self.color = 'Black'

  def generate_playable_card(self):
    # uses color, and labels to generate a name and all relevant abilities
    database = get_card_database()

    choices = database[self.color]
    names = []
    found_indicies = []
    for index, card in enumerate(choices):
      lines = card.split('\n')
      name_and_mana_cost = lines[0].split()
      name = ' '.join(name_and_mana_cost[:-1])
      names.append(name)

      for label in self.labels:
        if label in name:
          # good enough of a match for me...
          found_indicies.append(index)
          if self.debug:
            print "Matching %s label with %s" % (label, name)

    if len(found_indicies) != 0:
      index = random.choice(found_indicies)
      card = choices[index]
    else:
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
    # uses the labels of the image to find a relevant flavor text
    # Uses word2vec to try to find flavor similar to the labels

    flavor_database = []
    if self.flavor_database in ('real', 'all'):
      if self.debug:
        print("getting real flavors\n")
      flavor_database += get_flavor_database('legacy_flavor.txt')
    if self.flavor_database in ('all', 'generated'):
      if self.debug:
        print("getting generated flavors\n")
      flavor_database += get_flavor_database('large_sample_flavor_readable.cards')

    try:
      from gensim import corpora, models, similarities
      stoplist = set('for a of the and to in'.split())
      texts = [[word for word in flavor.lower().split() if word not in stoplist]
                for flavor in flavor_database]

      dictionary = corpora.Dictionary(texts)
      corpus = [dictionary.doc2bow(text) for text in texts]

      lsi = models.LsiModel(corpus, id2word=dictionary)
      doc = ' '.join(self.labels)
      vec_bow = dictionary.doc2bow(doc.lower().split())
      vec_lsi = lsi[vec_bow]
      index = similarities.MatrixSimilarity(lsi[corpus])
      sims = index[vec_lsi]
      sims = sorted(enumerate(sims), key=lambda item: -item[1])

      # kind of arbitrary, choice a random from the top 10 to spice it up.
      best_matches = sims[:10]
      if self.debug:
        best_flavors = map(lambda x: flavor_database[x[0]], best_matches)
        print "Flavor choices %s" % best_flavors
      best_match = random.choice(best_matches)
      index, score = best_match
      self.flavor = flavor_database[index]
    except ImportError:
      print("Tried to import gensim for flavor text matching, just using random instead")
      self.flavor = random.choice(flavor_database)

  def generate(self):
    # Triggers generation of the card.
    self.generate_card_color()
    self.generate_playable_card()
    self.generate_card_flavor_text()
    self.generated = True

  def __str__(self):
    # For printing cards. Better readability, but doesn't look that great
    if not self.generated:
      return "call generate first!"
    attributes = ["Color: %s" % self.color, "Name: %s" % self.name]
    attributes += ["Rules: %s" % self.rules, "Flavor: %s" % self.flavor]
    attributes += ["Mana cost: %s" % self.mana_cost, "Type: %s" % self.type]
    if self.power_toughness:
      attributes += ['Power/Toughness: %s' % self.power_toughness]
    return "\n".join(attributes)

