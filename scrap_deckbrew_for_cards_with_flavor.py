import requests
import json

page_number = 0
modern_cards = []
standard_cards = []
legacy_cards = []
while True:
  url = 'https://api.deckbrew.com/mtg/cards?page=%s' % str(page_number)
  response = requests.get(url)
  response_cards = json.loads(response.text)
  if len(response_cards) == 0:
    break
  for card in response_cards:
    if 'modern' in card['formats']:
      modern_cards.append(card)
    if 'standard' in card['formats']:
      standard_cards.append(card)
    if 'legacy' in card['formats']:
      legacy_cards.append(card)
  page_number += 1

f_modern = open('modern_cards.json', 'w')
f_modern.write(json.dumps(modern_cards))
f_standard = open('standard_cards.json', 'w')
f_standard.write(json.dumps(standard_cards))
f_legacy = open('legacy_cards.json', 'w')
f_legacy.write(json.dumps(legacy_cards))
