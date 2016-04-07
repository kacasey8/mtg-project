import requests
import json

def find_all_cards_in_format(mtg_format_name):
  cards = []
  page_number = 0
  while True:
    url = 'https://api.deckbrew.com/mtg/cards?page=%s&format=%s' % (str(page_number), mtg_format_name) 
    response = requests.get(url)
    response_cards = json.loads(response.text)
    if len(response_cards) == 0:
      break
    for card in response_cards:
      cards.append(card)
    page_number += 1
  return cards

if True:
  # change this to False to not get the standard cards.
  # this should take under 15 seconds
  standard_cards = find_all_cards_in_format('standard')
  f_standard = open('standard_cards.json', 'w')
  f_standard.write(json.dumps(standard_cards))


if False:
  # change this to True to get all the modern cards.
  # doing this should take around 1 minute
  modern_cards = find_all_cards_in_format('modern')
  f_modern = open('modern_cards.json', 'w')
  f_modern.write(json.dumps(modern_cards))

if False:
  # change this to True to get all the legacy cards.
  # doing this should take around 3 minutes
  legacy_cards = find_all_cards_in_format('legacy')
  f_legacy = open('legacy_cards.json', 'w')
  f_legacy.write(json.dumps(legacy_cards))
