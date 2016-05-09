import cache_parser
import card_generator
import argparse
import random

"""
This is the link between the image processing portion and
the card generation portion.

Uses the resulting labels and color info from the image processing
and sends that to the CardGenerator class so that a card can be generated.
"""

def generate_magic_card(labels, color_info, debug=False, flavor_database='real', filename='no'):
  if debug:
    print "Labels: %s\n" % labels
    print "Color info: %s\n" % color_info
  card = card_generator.CardGenerator(labels, color_info, debug, flavor_database)
  card.generate()
  print(card)

  print ('\n\nURL:')
  print get_url(card, filename.lower())

def get_url(card, filename):
  # This function was written in the last hour. plz no judging.
  color = card.color[0].lower()
  if card.color[2] == 'u':
    color = 'u'
  cardname = card.name.title()
  types = card.type
  subtypes = ''
  powertoughness = card.power_toughness
  if powertoughness:
    powertoughness = powertoughness.replace('(', '')
    powertoughness = powertoughness.replace(')', '')
    powertoughness = powertoughness.replace('/', '%2F')
  else:
    powertoughness = ''
  manacost = card.mana_cost
  manacost = manacost.replace('{', '')
  manacost = manacost.replace('}', '')
  flavor = card.flavor
  rules = card.rules

  cardtype = ''
  arr = ['Tribal', 'Artifact', 'Enchantment', 'Land', 'Creature', 'Instant', 'Sorcery', 'Planeswalker', 'Plane', 'Scheme', 'Emblem']
  for hi in arr:
    test = hi.lower()
    if test in types:
      cardtype += '1'
    else:
      cardtype += '0'
  arturl = random.choice(['http://wallpapercave.com/wp/W3gW73i.jpg', 'http://www.angelfire.com/moon2/xpascal/MoonHoax/AGC/BigOldComputer.jpg', 'http://i2.cdn.turner.com/money/dam/assets/150203180141-old-computers-780x439.jpg'])

  if 'sailboat' in filename:
    arturl = 'http://loewshotelsblog.com/wp-content/uploads/2015/09/Sailboat-sunset.jpg'

  if 'water' in filename:
    arturl = 'http://www.mycariboonow.com/wp-content/uploads/2015/06/Water-Advisory-Committee.jpg'


  format_string = (color, cardname, cardtype, subtypes, powertoughness, manacost, rules, flavor, arturl)
  url = "http://www.shenafu.com/magic/cc.php?save=true&frame=modern&border=&color=%s&cardname=%s" \
  "&supertype=00000&cardtype=%s&subtype=%s&powertoughness=%s&manacost=%s&rulestext=%s&" \
  "flavortext=%s&arturl=%s&artist=Taylor Wingard&creator=Chuck Roady" % format_string

  url = url.replace('\n', '')
  url = url.replace(' ', '%20')
  return url



if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-d', '--debug', action='store_true', default=False, help='will print debugging info')
  parser.add_argument('-f', '--file', default='cached.txt', help='file name for the cached file')
  parser.add_argument('-a', '--flavor', help='Which flavor to match to. This must be either "real", "all", or "generated"', default='real')

  args = parser.parse_args()
  labels, color_info = cache_parser.read_cache(args.file)
  generate_magic_card(labels, color_info, args.debug, args.flavor, args.file)
