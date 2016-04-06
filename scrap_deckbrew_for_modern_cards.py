import requests
import json

page_number = 0
modern_cards = []
standard_cards = []
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
  page_number += 1

f = open('modern_cards.json', 'w')
f.write(json.dumps(modern_cards))
f = open('standard_cards.json', 'w')
f.write(json.dumps(standard_cards))
