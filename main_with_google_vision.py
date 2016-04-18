import google_vision
import argparse
import cache_parser
import main

"""
This is a driver script to activate main. It uses google_vision.py
to get all the relevant info a file that is passed in and then execute
main.py
"""


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file', help='The image you\'d like to generate a magic card for.')
  parser.add_argument('-d', '--debug', action='store_true', help='will print debugging info')
  args = parser.parse_args()
  file_name = args.file
  if file_name == None:
    file_name = "Sailboat-sunset.jpg"

  response = google_vision.execute_google_vision(file_name, caching=False)

  labels, color_info = cache_parser.use_cache(response)

  if args.debug:
    main.generate_magic_card(labels, color_info, debug=True)
  else:
    main.generate_magic_card(labels, color_info, debug=False)

