# Robo Rosewater Project
Generating magic cards from random images.

Currently I can get labels from images (e.g. an image has a sailboat and a sun) from the google vision api and I can also generate unique new cards using mtg-rnn after training on all the legacy cards. I'm currently linking the two through exact text matching between labels and the card names that are generated, and also enforcing the color of the card matches. To get flavor text I'm currently just choosing between all the flavor texts on legacy mtg cards and using gensim (https://radimrehurek.com/gensim/index.html) to find the best match.

## Using Other Projects
- Both are under MIT license
- mtgencode is from https://github.com/billzorn/mtgencode. I've modified it slightly to allow it to handle flavor text and to work with the JSON that I am using from https://deckbrew.com/api/. This repo lets us convert a magic card into '|' separated data and also convert it back. This is pretty useful in conjuction with mtg-rnn.
- mtg-rnn is https://github.com/billzorn/mtg-rnn. mtg-rnn uses a character based neural network which means it guesses what character to add based on what it outputed previously. It adds characters in magic like style by training on a set of magic cards...and it learns english by itself with enough training. By using the encoded version to train, the neural network doesn't have to learn as much about syntax since the magic cards are encoded. (e.g. @ refers to the card's name in question, the neural network can just write "When @ enteres the battlefield..." as oppose to trying to properly generate those effects itself.)

## Project Structure
### Image Processing
- google_vision.py reads an image and gets information about it and stores the result to 'cached.txt' so we don't have to keep executing google_vision.py
- cached.txt holds the result of the google_vision.py function. Currently it holds the result of processing the 'Sailboat-sunset.jpg'
- Sailboat-sunset.jpg is a test file for image processing
- cache_parser.py reads the results from cached.txt into a slightly more managable format

### Card Generation
- main.py triggers the parser to get the cached image processing results, then feeds that to the card generator
- main_with_google_vision.py triggers google_vision.py to get image processing results and then feeds that into main.py
- card_generator.py generates everything about the card from the image info.

### Scraping
- scrap_deckbrew_for_card_with_flavor.py scraps https://deckbrew.com/api/. This script is useful because the api only returns 100 cards at a time. I'm using all the legacy cards as a training set for the neural network.
- legacy_cards.json is a json file for all legacy cards

### Data files
- large_final_sample.cards are 31,858 cards generated from mtg-rnn that was trained from all cards in legacy for a few days
- large_final_sample_readable.cards are those same 31,858 but after running mtgencode/decode.py on it
- legacy_flavor.txt is a placeholder for all legacy flavor textx currently in use. Later we will use generated flavor text instead.
