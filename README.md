# Robo Rosewater Project
Generating magic cards from random images.

## Project Structure
### Image Processing
- google_vision.py reads an image and gets information about it and stores the result to 'cached.txt' so we don't have to keep executing google_vision.py
- cached.txt holds the result of the google_vision.py function. Currently it holds the result of processing the 'Sailboat-sunset.jpg'
- Sailboat-sunset.jpg is a test file for image processing
- parser.py reads the results from cached.txt into a slightly more managable format
- dominant_color.py could be useful for figuring out the dominant color(s). It generates RBG values similar to what the google_vision api does

### Card Generation
- main.py triggers the parser to get the cached image processing results, then feeds that to the card generator
- card_generator.py generates everything about the card from the image info.

