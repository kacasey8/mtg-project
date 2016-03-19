import os
import json

"""
Reads the result from cached and parses it into useful formats.
Mainly to prevent unnecessary calls to the google vision API because
there is a limit of free queries.

See https://cloud.google.com/vision/reference/rest/v1/images/annotate
to get more info about the response.
"""

def read_cache(file_name='cached.txt'):
  if os.path.isfile(file_name):
    f = open(file_name, 'r')
    contents = f.read()
    cached_responses = json.loads(contents)
    cached_response = cached_responses['responses'][0]

    # This is a list of dictionaries containing color information
    # It looks something like this -
    # [{u'color': {u'blue': 83, u'green': 220, u'red': 253}, u'pixelFraction': 0.015963303, u'score': 0.092865042}, {u'color': {u'blue': 206, u'green': 241, u'red': 249}, u'pixelFraction': 0.11480122, u'score': 0.086540572}]
    # it's length 10 and each entry has color which has RBG values, a score representing how dominant the color is,
    # and how many pixels are occupied by said color.
    color_info = cached_response['imagePropertiesAnnotation']['dominantColors']['colors']

    # This is another list of dictionaries
    # it looks like this
    # [{u'score': 0.937013, u'mid': u'/m/0jp31', u'description': u'sail'}, {u'score': 0.93413693, u'mid': u'/m/07yv9', u'description': u'vehicle'}]
    # it's also length 10 and each entry has a score which is how confident google is, and a description which is the label
    label_info = cached_response['labelAnnotations']

    # discard score info, just get what labels we need
    labels = [x['description'] for x in label_info]

    # We will likely need multiple colors to identify what
    # color the card should be, but this is the most dominant.
    most_dominant_color_RBG = color_info[0]['color']
    #print "labels for image %s:" % labels
    #print "Most dominant color in RBG %s:" % most_dominant_color_RBG
    return (labels, color_info)

  else:
    print("Oops, cached.txt doesn't exist. Perhaps you need to run google_vision.py")
