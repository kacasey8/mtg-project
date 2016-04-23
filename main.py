import cache_parser
import card_generator
import argparse

"""
This is the link between the image processing portion and
the card generation portion.

Uses the resulting labels and color info from the image processing
and sends that to the CardGenerator class so that a card can be generated.
"""

def generate_magic_card(labels, color_info, debug=False, flavor_database='real'):
  if debug:
    print "Labels: %s\n" % labels
    print "Color info: %s\n" % color_info
  card = card_generator.CardGenerator(labels, color_info, debug, flavor_database)
  card.generate()
  print(card)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-d', '--debug', action='store_true', default=False, help='will print debugging info')
  parser.add_argument('-f', '--file', default='cached.txt', help='file name for the cached file')
  parser.add_argument('-a', '--flavor', help='Which flavor to match to. This must be either "real", "all", or "generated"', default='real')

  args = parser.parse_args()
  labels, color_info = cache_parser.read_cache(args.file)
  generate_magic_card(labels, color_info, args.debug, args.flavor)
