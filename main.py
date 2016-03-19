import parser
import card_generator

"""
This is the link between the image processing portion and
the card generation portion.

Uses the resulting labels and color info from the image processing
and sends that to the CardGenerator class so that a card can be generated.
"""


def generate_magic_card(labels, color_info):
  card = card_generator.CardGenerator(labels, color_info)
  card.generate()
  print card

def generate_magic_card_from_filename(file_name):
  # this should call google_vision.py eventually
  # and pass the results to the other generate_magic_card
  return None


labels, color_info = parser.read_cache()

generate_magic_card(labels, color_info)
