import weakref


class Content(object):
    def __getattr__(self, name):
        # Return empty string if <name> was not a valid attribute
        return ''


class WeakrefWrapper:
    def __init__(self, content_obj):
        self.content_obj = weakref.proxy(content_obj)

    def __getattr__(self, name):
        try:
            return getattr(self.content_obj, name)
        except weakref.ReferenceError:
            return ''


class Entry(Content):
    def __init__(self, json_obj, language):
        fields = json_obj['fields']
        for field_name, field_val in fields.items():
            if type(field_val[language]) is dict:
                continue
            setattr(self, field_name, field_val[language])
        setattr(self, 'content_type',
                json_obj['sys']['contentType']['sys']['id'])
        setattr(self, 'id', json_obj['sys']['id'])


class Asset(Content):
    def __init__(self, json_obj, language):
        self.url = json_obj['fields']['file'][language]['url']
        self.id = json_obj['sys']['id']

    def __getattr__(self, name):
        # Return empty string if <name> was not a valid attribute
        return ''
