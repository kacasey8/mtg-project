import google_vision
import argparse

"""
This is a driver script to activate main. It uses google_vision.py
to get all the relevant info a file that is passed in and then execute
main.py
"""

def generate_magic_card_from_filename(file_name):
  # this should call google_vision.py eventually
  # and pass the results to the other generate_magic_card
  return None


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file', help='The image you\'d like to generate a magic card for.')
  parser.add_argument('-v', '--verbose', action='store_true', help='will print debugging info')
  args = parser.parse_args()
  file_name = args.file
  if file_name == None:
    file_name = "Sailboat-sunset.jpg"