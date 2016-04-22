import argparse
import base64
import httplib2
import json

import logging
logging.basicConfig()

from apiclient.discovery import build
from oauth2client.client import GoogleCredentials

"""
This executes an api call to Google Vision.
It comes back with a response that has some label annotations
and dominant colors in RBG values. It then saves the result of the
call to 'cached.txt' so that you don't need to keep querying Google
There's some limit of free calls to the API, you would need my or a google API key,
and you would need to download most of the things imported above to use
this file. I put an OFFLINE var that will stop the call unless you change it to
False.
"""

OFFLINE = False

def execute_google_vision(photo_file, caching=True):
  '''Run a label request on a single image'''

  API_DISCOVERY_FILE = 'https://vision.googleapis.com/$discovery/rest?version=v1'
  http = httplib2.Http()

  credentials = GoogleCredentials.get_application_default().create_scoped(
      ['https://www.googleapis.com/auth/cloud-platform'])
  credentials.authorize(http)

  service = build('vision', 'v1', http, discoveryServiceUrl=API_DISCOVERY_FILE)

  with open(photo_file, 'rb') as image:
    image_content = base64.b64encode(image.read())
    service_request = service.images().annotate(
      body={
        'requests': [{
          'image': {
            'content': image_content
           },
          'features': [
            {
              "type":"IMAGE_PROPERTIES",
              "maxResults":10
            },
            {
              "type":"LABEL_DETECTION",
              "maxResults":10
            }
          ]
         }]
      })
    response = service_request.execute()
    if caching:
      with open('cached.txt', 'w') as outfile:
        json.dump(response, outfile)
    else:
      return response

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file', help='The image you\'d like to label.')
  args = parser.parse_args()
  file_name = args.file
  if file_name == None:
    file_name = "Sailboat-sunset.jpg"

  if OFFLINE:
    print("Use the results in cached.txt for testing.")
  else:
    execute_google_vision(file_name)
