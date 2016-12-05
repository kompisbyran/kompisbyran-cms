import os
# -*- coding: utf-8 -*-

import sys
import threading
import time
import json, requests, datetime
from urllib2 import Request, urlopen
from load_env_variables import CONTENTFUL_DELIVERY_API, CONTENTFUL_PREVIEW_API, CONTENTFUL_SPACE_ID, CONTENTFUL_MANAGEMENT_API
from werkzeug import secure_filename

from load_env_variables import HOSTNAME

reload(sys)
sys.setdefaultencoding('utf-8')
ACCEPTED_IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'bmp', 'raw']


def handle_mail(body, image):
    static_path = '/static/mail_images/'
    filename = secure_filename(image.filename)
    if filename.split(".").pop() not in ACCEPTED_IMAGE_FORMATS:
        return

    handle_image(image, './src' + static_path + filename)
    upload_new_post(body, (HOSTNAME + static_path + filename, filename))
    RemoveImage('./src' + static_path + filename).start()


def upload_new_post(text, image_data):
    id = make_image_available(image_data)
    upload_meetup_entry(text, id)


def handle_image(image, path):
    image.save(path)


def make_image_available(image):
    id = upload_image(image)
    process_image(id)
    return id


def upload_image(image):
    data = get_image_data(image)
    headers = {
        'Authorization': 'Bearer ' + CONTENTFUL_MANAGEMENT_API,
        'Content-Type': 'application/vnd.contentful.management.v1+json'
    }
    request = Request(
        'https://api.contentful.com/spaces/' + CONTENTFUL_SPACE_ID + '/assets',
        data=json.dumps(data),
        headers=headers)
    response_body = urlopen(request).read()
    return json.loads(response_body)['sys']['id']


def get_image_data(image):
    url = image[0]
    filename = image[1]
    file_extension = filename.rsplit('.', 1)[-1]
    data = {
        "fields": {
            "title": {
                "sv": filename
            },
            "file": {
                "sv": {
                    "contentType": "image/" + file_extension,
                    "fileName": filename,
                    "upload": url
                }
            }
        }
    }
    return data


def process_image(id):
    headers = {
        'Authorization': 'Bearer ' + CONTENTFUL_MANAGEMENT_API,
        'X-Contentful-Version': '1'
    }
    request = Request(
        'https://api.contentful.com/spaces/' + CONTENTFUL_SPACE_ID + '/assets/'
        + id + '/files/sv/process',
        headers=headers)
    request.get_method = lambda: 'PUT'
    response_body = urlopen(request).read()


def upload_meetup_entry(meetup_text, image_id):
    data = get_meetup_data(meetup_text, image_id)
    headers = {
        'Authorization': 'Bearer ' + CONTENTFUL_MANAGEMENT_API,
        'Content-Type': 'application/vnd.contentful.management.v1+json',
        'X-Contentful-Content-Type': 'meetup'
    }
    request = Request(
        'https://api.contentful.com/spaces/' + CONTENTFUL_SPACE_ID + '/entries',
        data=json.dumps(data),
        headers=headers)

    response_body = urlopen(request).read()


def get_meetup_data(meetup_text, image_id):
    date = datetime.datetime.now().isoformat().split('.', 1)[0]
    return {
        "fields": {
            "date": {
                "sv": date
            },
            "meetup": {
                "sv": meetup_text
            },
            "picture": {
                "sv": {
                    "sys": {
                        "type": "Link",
                        "linkType": "Asset",
                        "id": image_id
                    }
                }
            }
        }
    }


class RemoveImage(threading.Thread):

    def __init__(self, path):
        threading.Thread.__init__(self)
        self.path = path

    def run(self):
        time.sleep(30)
        os.remove(self.path)
