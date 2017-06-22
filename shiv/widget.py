#!/usr/bin/env python
#
#       widget.py
#       

from django.conf import settings
from django.template.loader import get_template
import re

from shiv import data_methods as dm
from shiv.container import Container


# from shiv.mod_settings import URL_NAMES
url_names = settings.SHIV_URL_DICT.keys()

class WidgetMeta(type):
    def __init__(cls, name, bases, dict):
        for b in bases:
            if hasattr(b, '_registry'):
                pat = re.compile(dict['urlpat'])
                urls = [e for e in map(lambda x :"" if not x else x, b._registry.keys()) if re.search(pat, e)]
                for e in urls:b._registry[e].append((dict['index'], cls))
                cls.widget_id = name
                module = __import__(dict['__module__'].rsplit('.', 1)[0] + '.media', fromlist=[dict['__module__'].rsplit('.', 1)[0]])
                try:
                    cls._media = getattr(module, name + 'Media')()
                except AttributeError:
                    cls._media = getattr(module, 'DefaultMedia')()
                cls._media.css = [e.startswith('http') and e or cls._media.css_prefix + e for e in cls._media.css]
                cls._media.js = [e.startswith('http') and e or cls._media.js_prefix + e for e in cls._media.js]
                for elem in dict['_tab_class']:
                    cls._media.extra_css = cls._media.extra_css + elem._media.css + elem._media.extra_css
                    cls._media.extra_js = cls._media.extra_js + elem._media.js + elem._media.extra_js
                if settings.TEMPLATE_CACHING:
                    cls._media.template = get_template(cls._media.template)
                break
        return type.__init__(cls, name, bases, dict)

class Widget(Container):
    __metaclass__ = WidgetMeta
    _registry = dict([(e, []) for e in url_names])    
    title = "Widget"
    _for_loggedin = None

    def __init__(self, *args, **kwargs):
        request = args[0]
        excludes = dm.get_excludes(request.user)
        self.tabs = filter(lambda x: x.__module__ + '.' + x.__name__ not in excludes and x.__module__ not in excludes, self._tab_class)
        
        self.tabs = map(lambda x, i: x(
                            is_default=getattr(self, 'default_tab', i) == i,
                            tab_client=getattr(self, 'client', None),
                            request=request,
                            ), self.tabs, range(len(self.tabs))
                        )
         
        self.context = {'tabs': [], 'id': self.widget_id, 'title' : self.title, 'images': self._media.images}
        self.request = request

    def show(self, template=None, is_json=False, start=1, count=5):
        if len(self.context['tabs']) == 0 :
            self.context['tabs'] = [t.show(start=start, count=count, is_json=is_json) for t in self.tabs]
        return super(Widget, self).show(template, self.request, self.context, is_json)

    @classmethod
    def get_css(cls):
        return cls._media.css + cls._media.extra_css

    @classmethod
    def get_js(cls):
        return cls._media.js + cls._media.extra_js
