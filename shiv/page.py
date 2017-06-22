#!/usr/bin/env python
#
#       page.py
#       
#       Copyright 2010 yousuf <yousuf@postocode53.com>
#
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
import inspect
import json
import logging
import operator
import os

from custom import data_methods as dm
from shiv.auth import login_required as lr
from shiv.container import Container
from shiv.utils.cssmin import cssmin
from shiv.utils.jsmin import jsmin


LOGGER = logging.getLogger('shiv')
        
class PageMeta(type):
    def __init__(cls, name, bases, dict):
        for b in bases:
            if hasattr(b, '_registry'):
                b._registry[name] = cls
                cls.page_id = name                
                # cls._media.template = get_template(cls._media.template)
                break
        return type.__init__(cls, name, bases, dict)
        
class Page(Container):
    __metaclass__ = PageMeta
    _registry = {}
    title = "Page"
    media = None
    
    def __init__(self, login_required=True, login_url=None, permission=None):
        self.module = self.__module__.split('.')[-2]
        
        if permission:
            self.view = permission_required(permission, login_url)(self.view)
        if login_required:
            self.view = lr(self.view, login_url)
        self.context = {}
#        self.css, self.js = self.get_css_js()
        self.all_widgets = []

    def unique_list(self, l):
        ulist = []
        [ulist.append(x) for x in l if x not in ulist]
        return ulist

    def _populate_widgets(self):
        from shiv.widget import Widget
        self.all_widgets = self.unique_list(map(operator.itemgetter(1),
                                        sorted(Widget._registry[self.url], key=operator.itemgetter(0))
                                        )
                                        )
        self.css, self.js = self.get_css_js()
        
    def __call__(self, request, *args, ** kwargs):
        meta_log = dict([(e, request.META.get(e, 'N/A')) for e in settings.META_LOGGER])        
        log_info = {
        'USER':request.user.username or str(request.user),
        'PATH':request.path,
        'URL':request.build_absolute_uri(),
        'PARAMS' :request.REQUEST.items(),
        'META':meta_log,
        'COOKIES': request.COOKIES
        }        
        LOGGER.info(json.dumps(log_info))
        user = request.user
        excludes = dm.get_excludes(user)        
        if self.module in excludes:
            return HttpResponseRedirect(reverse('master_prelogin_page', urlconf='master.urls'))
        check_loggedin = {
                     None:True,
                     False: isinstance(user, AnonymousUser),
                     True:not isinstance(user, AnonymousUser),
                      }
        self.widgets = filter(lambda x: x.__module__ + '.' + x.__name__ not in excludes and x.__module__ not in excludes, self.all_widgets)
        self.widgets = filter(lambda x: check_loggedin[getattr(x, '_for_loggedin')], self.widgets)
        self.boxes = filter(lambda x:  x.__module__ + '.' + (x.__name__ if inspect.isclass(x) else x.__class__.__name__) not in excludes and x.__module__ not in excludes, self.boxes)
        self.boxes = filter(lambda x: check_loggedin[getattr(x, '_for_loggedin')] , self.boxes)
        return self.view(request, *args, ** kwargs)
        
    def view(self, request, * args, ** kwargs):        
        if hasattr(self, 'request_validator'):            
            if not self.request_validator(request, args, kwargs):
                raise Http404
        return self.show(request, * args, ** kwargs)

    def show(self, request, * args, ** kwargs):
        if not hasattr(self, 'css'):self._populate_widgets();
        self.context['widgets'] = [e(request, * args, ** kwargs).show() for e in self.widgets]
        self.context['boxes'] = [inspect.isclass(e) and e(request, module=self.module, * args, ** kwargs).show() or e.show() for e in self.boxes]
        self.context['header'] = hasattr(self, 'header') and (inspect.isclass(self.header) and self.header(request, module=self.module).show() or self.header.show())
        self.context['footer'] = hasattr(self, 'footer') and self.footer(request, module=self.module).show() or ''
        self.context['css'] = self.css
        self.context['js'] = self.js
        # optimise this, can move in to request validator section, as we are making a validation already
        x = getattr(self, 'page_title', '')
        self.context['title'] = x(request, args, kwargs) if x.__class__.__name__ == 'function' else x
        self.context['header_meta'] = hasattr(self, 'header_meta') and self.header_meta(request, module=self.module).show() or ''
        self.context['module'] = self.module
        return HttpResponse(super(Page, self).show(self.template, request, None, None))

    def get_css_js(self):
        css = []
        js = []
        if type(self.media) == type(''):
            module, media = self.media.rsplit('.', 1)
            module = __import__(module, fromlist=[module])
            media = getattr(module, media)
            css = [e.startswith('http') and e or media.css_prefix + e for e in media.css]
            js = [e.startswith('http') and e or media.js_prefix + e for e in media.js]

        for e in self.__dict__.values():            
            if isinstance(e, list):
                for b in e:
                    if inspect.isclass(b) and (isinstance(b, Container) or issubclass(b, Container)):
                        css.extend(b.get_css())
                        js.extend(b.get_js())
                continue

            if inspect.isclass(e) and (isinstance(e, Container) or issubclass(e, Container)):
                css.extend(e.get_css())
                js.extend(e.get_js())

        # js minification function
        if settings.JS_MINIFY:
            js = minify_js(self.unique_list(js), "%s_%s_" % (self.module, self.page_id))

        # css minification function
        if settings.CSS_MINIFY:
            css = minify_css(self.unique_list(css), "%s_%s_" % (self.module, self.page_id))

        return [x[:-1] if x.endswith('/') else x for x in self.unique_list(css)], [x[:-1] if x.endswith('/') else x for x in self.unique_list(js)]
        
class DefaultPage(Page):
    template = "master/PageHome.html"
    media = 'master.media.PageHomeMedia'

    def show(self, request, * args, ** kwargs):        
        self.context['menu'] = inspect.isclass(self.menu) and  hasattr(self, 'menu') and self.menu(request, module=self.module).show() or ''
        self.context['subheader'] = inspect.isclass(self.subheader) and  hasattr(self, 'subheader') and self.subheader(request, module=self.module).show() or  ''
        return super(DefaultPage, self).show(request, * args, ** kwargs)


def minify_js(js, page_id):
        xs = []
        jsdata = ''
        exists = False
        if os.path.exists(settings.MEDIA_ROOT + '/js/minified/' + page_id + str(settings.JS_VERSION) + '.js'):
            exists = True
        for e in js:
            if e.startswith('http'):
                xs.append(e)
                continue
            if exists:continue
            try:
                f = open(settings.PROJECT_PATH + e)                                    
                jsdata += '\n//' + e + '\n' + f.read() + '\n'
                f.close()
            except:pass
        if not exists:
            of = open(settings.MEDIA_ROOT + '/js/minified/' + page_id + str(settings.JS_VERSION) + '.js', 'w')
            if settings.DEBUG:
                of.write(jsmin(jsdata))
            else:
                of.write(jsmin(jsdata))
            of.close()
        js = xs + ['/static/js/minified/' + page_id + str(settings.JS_VERSION) + '.js']
        return js
    
def minify_css(css, page_id):        
        xs = []
        cssdata = ''
        exists = False
        if os.path.exists(settings.MEDIA_ROOT + '/css/minified/' + page_id + str(settings.CSS_VERSION) + '.css'):
            exists = True
        for e in css:
            if e.startswith('http'):
                xs.append(e)                
                continue
            if exists:continue
            try:
                f = open(settings.PROJECT_PATH + e)                                
                cssdata += '\n/*' + e + '*/\n' + f.read()
            except:pass
        if not exists:
            of = open(settings.MEDIA_ROOT + '/css/minified/' + page_id + str(settings.CSS_VERSION) + '.css', 'w')
            of.write(cssmin("".join(cssdata)))
            of.close()
        css = xs + ['/static/css/minified/' + page_id + str(settings.CSS_VERSION) + '.css']
        return css


def redirect_to_internal(url, index=1):
    # NOTE check university name removal part
    url_list = url.split('/')
    url_list.pop(index)
    url_list.pop(index)
    url = "/".join(url_list)
    return HttpResponseRedirect(url)
