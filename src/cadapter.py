# -*- coding: utf-8 -*-

import inspect, content_model
from load_env_variables import CONTENTFUL_DELIVERY_API, CONTENTFUL_PREVIEW_API, CONTENTFUL_SPACE_ID, CONTENTFUL_MANAGEMENT_API
import json, requests, sys, datetime
from urllib2 import Request, urlopen
reload(sys)
sys.setdefaultencoding('utf-8')


class Language(object):
    def __init__(self, name, code, default, optional):
        self.name = name
        self.code = code
        self.default = default
        self.optional = optional


class CAdapter:
    def __init__(self):
        # Raw json data from contentful
        self.json_obj = None
        self.preview_json_obj = None
        # Next contentful request address
        self.last_update_time = datetime.datetime.now()

        # List of supported languages in data
        self.languages = []
        # Default language
        self.user_language = ''
        self.default_language = ''
        # Entry objects converted from contentful json data
        self.entries = {}
        self.preview_entries = {}
        # Assets converted from contentful json data
        self.assets = {}
        self.preview_assets = {}

        # Contentful entries with links to unpublished content
        self.broken_links = []

        # Synchronize with contentful
        self.use_preview = False
        self.synchronize_with_contentful()

    def check_timed_update(self):
        current_time = datetime.datetime.now()
        if current_time > self.last_update_time + datetime.timedelta(
                minutes=30):
            self.synchronize_with_contentful()
            self.last_update_time = current_time

    def synchronize_with_contentful(self,
                                    space_id=None,
                                    content_api_key=None,
                                    management_api_key=None,
                                    preview=False):
        space_id = CONTENTFUL_SPACE_ID if not space_id else space_id
        management_api_key = CONTENTFUL_MANAGEMENT_API if not management_api_key else management_api_key
        if preview:
            content_api_key = CONTENTFUL_PREVIEW_API if not content_api_key else content_api_key
        else:
            content_api_key = CONTENTFUL_DELIVERY_API if not content_api_key else content_api_key

        languages, default_language = self.get_contentful_locales(
            space_id, management_api_key)
        json_obj = self.get_contentful_data(space_id, 'entries',
                                            content_api_key, preview)
        json_obj += self.get_contentful_data(space_id, 'assets',
                                             content_api_key, preview)
        if len(self.languages) == 0:
            self.languages = languages
        if self.default_language == '':
            self.default_language = default_language
        if self.user_language == '':
            self.user_language = default_language

        entries, assets = self.convert_contentful_to_objects(json_obj)

        if preview:
            self.preview_entries = entries
            self.preview_assets = assets
            self.preview_json_obj = json_obj
        else:
            self.entries = entries
            self.assets = assets
            self.json_obj = json_obj

    def get_contentful_locales(self, space_id, api_key):
        default_language = ''
        languages = []
        request = 'https://api.contentful.com/spaces/{}/locales?access_token={}'.format(
            space_id, api_key)
        response = requests.get(request).json()
        for item in response['items']:
            language = Language(item['name'], item['code'], item['default'],
                                item['optional'])
            languages.append(language)
            if language.default:
                default_language = language.code
        return languages, default_language

    def get_contentful_data(self,
                            space_id,
                            request_type,
                            api_key,
                            preview=False):
        if preview:
            base_request = 'https://preview.contentful.com/spaces/'
        else:
            base_request = 'https://cdn.contentful.com/spaces/'
        request = base_request + '{}/{}?access_token={}&locale=*'.format(
            space_id, request_type, api_key)
        response = requests.get(request)
        content = response.json()
        json_obj = content['items']
        skip = len(json_obj)
        while skip < int(content['total']):
            request = base_request + '{}/{}?access_token={}&skip={}&locale=*'.format(
                space_id, request_type, api_key, skip)
            response = requests.get(request)
            json_obj += response.json()['items']
            skip += len(json_obj)
        return json_obj

    def convert_contentful_to_objects(self,
                                      json_obj,
                                      entries=None,
                                      assets=None):
        if entries is None:
            entries = {}
            for language in self.languages:
                entries[language.code] = {}
        if assets is None:
            assets = {}
            for language in self.languages:
                assets[language.code] = {}
        linked_content = []
        for obj in json_obj:
            for language in [l.code for l in self.languages]:
                if obj['sys']['type'] == 'Entry':
                    entry = self.create_entry_object(obj, language)
                    linked_content += [
                        (entry.id, field_name, link)
                        for field_name, link in obj['fields'].items()
                        if type(link[language]) is dict or list
                    ]
                    entries[language][entry.id] = entry

                elif obj['sys']['type'] == 'Asset':
                    try:
                        asset = self.create_asset_object(obj, language)
                        assets[language][asset.id] = asset
                    except:
                        # Malformed asset data, skip it
                        continue
        linked_content += self.broken_links
        self.broken_links = []
        self.resolve_links(linked_content, entries, assets)
        return entries, assets

    def create_asset_object(self, obj, language):
        if language not in obj['fields']['file']:
            language = self.default_language
        return content_model.Asset(obj, language)

    def create_entry_object(self, obj, language):
        obj = self.fill_empty_locale_content(obj, language)
        entry = content_model.Entry(obj, language)
        return entry

    def fill_empty_locale_content(self, obj, language):
        for field, lang_dict in obj['fields'].items():
            if not language in lang_dict:
                obj['fields'][field][language] = obj['fields'][field][
                    self.default_language]
        return obj

    def resolve_links(self, linked_content, entries, assets):
        for entry_id, field_name, link in linked_content:
            for language in link.keys():
                if isinstance(link[language], dict):
                    link_id = link[language]['sys']['id']
                    link_type = link[language]['sys']['linkType']
                    #Try to create a weakref_wrapper from entries
                    weakref_wrapper = self.create_weakrefwrapper_object(
                        link_id, language, assets)
                    if weakref_wrapper is None:
                        # Entry was not in entries, try asset
                        weakref_wrapper = self.create_weakrefwrapper_object(
                            link_id, language, entries)

                    if weakref_wrapper is not None:
                        setattr(entries[language][entry_id], field_name,
                                weakref_wrapper)
                    else:
                        self.broken_links.append((entry_id, field_name, link))
                elif isinstance(link[language], list):
                    newList = []
                    for elem in link[language]:
                        elem_id = elem['sys']['id']
                        elem_type = elem['sys']['type']
                        #Try to create a weakref_wrapper from entries
                        weakref_wrapper = self.create_weakrefwrapper_object(
                            elem_id, language, entries)
                        if weakref_wrapper is None:
                            # Entry was not in entries, try asset
                            weakref_wrapper = self.create_weakrefwrapper_object(
                                elem_id, language, assets)

                        if weakref_wrapper is not None:
                            newList.append(weakref_wrapper)
                        else:
                            self.broken_links.append(
                                (entry_id, field_name, link))
                    setattr(entries[language][entry_id], field_name, newList)

    def create_weakrefwrapper_object(self, content_id, language, resource):
        if content_id in resource[language]:
            return content_model.WeakrefWrapper(resource[language][content_id])
        else:
            return None

    def resolve_entry_link(self, link_id, entry_id, field_name, language,
                           entries):
        if link_id in entries[language]:
            weakref_wrapper = content_model.WeakrefWrapper(entries[language][
                link_id])
            setattr(entries[language][entry_id], field_name, weakref_wrapper)
        else:
            # The linked entry was not present in data, add to broken links for future resolution
            self.broken_links.append((entry_id, field_name, link))

    def get_entries(self, **kwargs):
        order = kwargs.pop('order', None)
        language = self.user_language
        if self.use_preview:
            res = self.preview_entries[language].values()
        else:
            res = self.entries[language].values()
        for name, val in kwargs.items():
            res = [c for c in res if getattr(c, name) == val]
        if order:
            reverse = False
            if order[0] is '-':
                # Reverse the order
                order = order[1:]
                reverse = True
            res.sort(key=lambda e: getattr(e, order), reverse=reverse)
        if len(res) == 0:
            # No content matched the query, return a dummy Content object
            res.append(content_model.Content())
        return res

    def get_entry(self, **kwargs):
        return self.get_entries(**kwargs)[0]
