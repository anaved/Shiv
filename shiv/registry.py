from django.conf import settings
from django.core.urlresolvers import get_resolver, reverse, resolve
import sys

from shiv.page import Page


def flatten_list(l):
    res = []
    for e in l:
        if isinstance(e, list):
            res.extend(e)
        else:
            res.append(e)
    return res
    
def get_url_dict():
    resolver = get_resolver(None)
    patterns = map(lambda x: hasattr(x, 'url_patterns') and x.url_patterns or x, resolver.url_patterns)
    patterns = flatten_list(patterns)
    result = dict([(e.name, e.callback) for e in patterns if isinstance(e.callback, Page)])
    return result

def register_widgets():
    settings.SHIV_URL_DICT .update(get_url_dict())
    apps = [e for e in settings.INSTALLED_APPS if not e == 'shiv']
    for e in apps:
        try:
            sys.modules[e + '.widget'] = __import__(e + '.widget', fromlist=['widget'])
        except:pass
    for name, callback in settings.SHIV_URL_DICT.items():
        callback.url = name
        callback._populate_widgets()

def register_pages():
    settings.SHIV_URL_DICT = get_url_dict()
    for name, callback in settings.SHIV_URL_DICT.items():
        callback.url = name
