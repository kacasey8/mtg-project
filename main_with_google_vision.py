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
  parser.add_argument('-f', '--file', default="test_images/Sailboat-sunset.jpg", help='The image you\'d like to generate a magic card for.')
  parser.add_argument('-d', '--debug', action='store_true', help='will print debugging info')
  parser.add_argument('-c', '--cache', action='store_true', help='whether or not to cache the response')
  parser.add_argument('-l', '--location', help='Where the cached file will be saved')
  parser.add_argument('-a', '--flavor', help='Which flavor to match to. This must be either "real", "all", or "generated"', default='real')
  args = parser.parse_args()
  file_name = args.file

  response = google_vision.execute_google_vision(file_name, caching=args.cache, cache_filename=args.location)
  labels, color_info = cache_parser.use_cache(response)

  if args.debug:
    main.generate_magic_card(labels, color_info, debug=True, flavor_database=args.flavor)
  else:
    main.generate_magic_card(labels, color_info, debug=False, flavor_database=args.flavor)

