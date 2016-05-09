# Robo Rosewater Project
Generating magic cards from random images.

Currently I can get labels from images (e.g. an image has a sailboat and a sun) and color information in the form of the top 10 RBG values of the image from the google vision api. I translate these RBG values into HSL (hue, lightness, and saturation) and then figure out if the RBG is closest to either red, green or blue, black or white. I then choose a color that the card should be, unfortunately only single color for now, and no devoid. I can also generate unique new cards using mtg-rnn after training on all the legacy cards. I then link the image to a generated card through exact text matching between labels and the card names and also enforcing the color of the card matches. For flavor text I trained mtg-rnn but only on flavor text of all legacy cards. I then link the labels to a flavor text by using gensim which uses a bag of words model to compute similarity.

## Usage
- To use the project use main.py or main_with_google_vision.py. Use the -d (debug) flag to print out more information about what is going on. You can also specify with the -a option whether to pull from "real" flavor texts, "generated" flavor texts or all.

### main.py
- main.py takes a file that the google vision api returned, you can use any file from the cache_from_gv directory, and you specify this file with the -f option.
- An example command would be `python main.py -f cache_from_gv/bench.txt`.
- Another example command of with the -a option would be `python main.py -f cache_from_gv/water.txt -a generated` which outputs

Color: Blue  
Name: trid~mover reflection  
Rules: @ can't be blocked.  
Flavor: exception shapes up in the great scenebind.  
Mana cost: {2}{U}  
Type: creature enchantment ~ xemunta  
Power/Toughness: (2/2)  

### main_with_google_vision.py
- main_with_google_vision.py takes an image file, goes to the google vision api and then uses main.py with the result. The image file is specified with -f.
- Other options include -c which is whether or not we should cache the result, and if we are caching it -l determines the location of where we should cache to.
- An example command would be `python main_with_google_vision.py -f test_images/green_plant.jpg -d -c -l cache_from_gv/plant.txt -a both` which outputs (along with various debug info)

Color: Green  
Name: torplanting road  
Rules: uncast target spell. put a 2/2 green elemental creature token onto the battlefield.  
Flavor: smart artificers clean up after themselves.  
Mana cost: {3}{G}{G}  
Type: instant  

## Using Other Projects
- Both are under MIT license
- mtgencode is from https://github.com/billzorn/mtgencode. I've modified it slightly to allow it to handle flavor text and to work with the JSON that I am using from https://deckbrew.com/api/. This repo lets us convert a magic card into '|' separated data and also convert it back. This is pretty useful in conjuction with mtg-rnn.
- mtg-rnn is https://github.com/billzorn/mtg-rnn. mtg-rnn uses a character based neural network which means it guesses what character to add based on what it outputed previously. It adds characters in magic like style by training on a set of magic cards...and it learns english by itself with enough training. By using the encoded version to train, the neural network doesn't have to learn as much about syntax since the magic cards are encoded. (e.g. @ refers to the card's name in question, the neural network can just write "When @ enteres the battlefield..." as oppose to trying to properly generate those effects itself.)
- Gensim is under the GNU LGPL license and is https://radimrehurek.com/gensim/tut3.html. Gensim provides word2vec functionality, so that I can translate flavor text into a bag of words, and then try to find flavor text that is most similar to the labels. It uses Latent Semantic Analysis to map how close words are to each other, and then chose the overall closest bag of words to the bag of labels.

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
- legacy_flavor.txt is a placeholder for all legacy flavor texts currently in use by mtg.
- large_sample_flavor.cards are 12,522 flavor texts that were generated from mtg-rnn that was trained on legacy flavors for a few days
- large_sample_flavor_readable.cards are the same 12,522 but after running mtgencode/decode.py

### Testing
- test_images/* are the test images I'm using. The idea is that each of them has a different dominant color: the bench is black, the car and plains are red, the plant is green, the sailboat is white and the water is blue
- cache_from_gv/* Holds the google response as json for each image. This allows other people to test without needing to have the google vision api set up.
