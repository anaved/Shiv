#!/usr/bin/env python
#
#       tab.py
#       

from django.conf import settings
from django.db.models.query import QuerySet
from django.template.loader import get_template

from shiv.container import Container
from shiv.nodes import Node
from shiv.paginator import Paginator


class TabMeta(type):
    def __init__(cls, name, bases, dict):
        for b in bases:
            if hasattr(b, '_registry'):
                b._registry[name] = cls
                cls.tab_id = dict['__module__'].rsplit('.', 1)[0] + name
                module = __import__(dict['__module__'].rsplit('.', 1)[0] + '.media', fromlist=[dict['__module__'].rsplit('.', 1)[0]])
                try:
                    cls._media = getattr(module, name + 'Media')()
                except AttributeError:
                    cls._media = getattr(module, 'DefaultMedia')()
                cls._media.css = [e.startswith('http') and e or cls._media.css_prefix + e for e in cls._media.css]
                cls._media.extra_css = dict['_element_class']._media.css
                cls._media.js = [e.startswith('http') and e or cls._media.js_prefix + e for e in cls._media.js]
                cls._media.extra_js = dict['_element_class']._media.js
                if settings.TEMPLATE_CACHING:
                    cls._media.template = get_template(cls._media.template)
                break
        return type.__init__(cls, name, bases, dict)
        
class Tab(Container):
    __metaclass__ = TabMeta
    _registry = {}
    title = "Tab"
    
    def __init__(self, request , is_default, tab_client=None):
        self.is_default = is_default
        self.user = request.user
        self.client = tab_client
        self.context = {'elements': [], 'is_default': is_default,
                            'id': self.tab_id, 'title': Node(self.title),
                            'images': self._media.images}
        self._prepare()        
        self.request = request

    def _prepare(self):
        self.ids = [self.client]
        
    def _get_elements(self, element_class, paginator):        
        return [ element_class(client=id, request=self.request,
                                ) for id in paginator.object_list]
        
    def show(self, template=None, is_json=False, start=1, count=10, next_key=None, prev_key=None):              
        if self.is_default:            
            element_class = self._element_class                  
            paginator = Paginator(self.ids, count, request=self.request)
            ppage = paginator.page(start)
            self.context['elements'] = [e.show(is_json=is_json)\
                                    for e in self._get_elements(element_class, ppage)]
            self.context['ppage'] = ppage                        
            
        context = {}        
        if (not is_json) and self.is_default:
            context['html'] = super(Tab, self).show(template=template,
                                request=self.request,
                                context=self.context,
                                is_json=is_json)
        context.update(self.context)
        if hasattr(self, 'client'):
            context['client'] = str(self.client)
        return context

