#!/usr/bin/env python
#
#       solr.py
#
#       Copyright 2010 yousuf <yousuf@postocode53.com>
#

import ast
from django.conf import settings
import traceback
from urllib import urlencode
from urllib2 import urlopen
import urllib2


class SOLR(object):
    GET_PARAMS = {
    'version':2.2, 'q':'*:*',
    'qt':'standard', 'wt':'python', 'hl.simple.pre':'<b>', 'hl.simple.post':'</b>'
        }
    MAX_HL_LENGTH = 200

    def __init__(self, fl="*,score", hl="true", hl_fl="", hl_fragsize=70, hl_snippets=5, hl_mergeContiguous="true",
                 hl_fragmenter="regex", hl_usePhraseHighlighter="true", hl_regex_slop=0.2, hl_highlightMultiTerm="true",
                 start=0, rows=100, sort=None, solr_url=settings.SOLR_URL, solr_user=settings.SOLR_USER, solr_pass=settings.SOLR_PASS, fq=''):
        self.get_params = self.GET_PARAMS.copy()
        # self.get_params = self.GET_PARAMS.copy()
        self.get_params['fl'] = fl
        self.get_params['hl'] = hl
        self.get_params['hl.fl'] = hl_fl
        self.get_params['hl.fragsize'] = hl_fragsize
        self.get_params['hl.snippets'] = hl_snippets
        self.get_params['hl.mergeContiguous'] = hl_mergeContiguous
        self.get_params['hl.fragmenter'] = hl_fragmenter
        self.get_params['hl.usePhraseHighlighter'] = hl_usePhraseHighlighter
        self.get_params['hl.regex.slop'] = hl_regex_slop
        self.get_params['hl.highlightMultiTerm'] = hl_highlightMultiTerm
        self.get_params['start'] = start
        self.get_params['rows'] = rows
        self.get_params['fq'] = fq
        if sort:
            self.get_params['sort'] = sort

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, solr_url, solr_user, solr_pass)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)


    def search(self, search_url, query='', ** kwargs):
        if not query:
            return {'numFound':0, 'docs': [], }
        url = search_url
        for k, v in kwargs.items():
            query += ' ' + k + ':' + v
        self.get_params['q'] = query
        self.get_params['rows'] = 100
        data = urlencode(self.get_params)
        try:
            url = url + '?' + data
            settings.LOGGER.debug("Executing query at SOLR : %s" % (url,))
            u = urlopen(url)
        except:
            settings.LOGGER.error("Error occured at SOLR : %s" % (traceback.format_exc(),))
            return {'numFound':0, 'docs': [], }
        return self.parse_result(u.read(), url)

    def facet_search(self, search_url, query='', facet_field=[], facet_query=[], rows=0):
        if not query:query = '*:*'
            # return {'numFound':0, 'docs': [], }
        url = search_url
        self.get_params['q'] = query
        self.get_params['facet'] = 'on'
        self.get_params['facet.field'] = facet_field
        self.get_params['facet.query'] = facet_query
        self.get_params['facet.mincount'] = 0
        self.get_params['facet.limit'] = 10
        self.get_params['facet.sort'] = 'count'
        self.get_params['fq'] = ' OR '.join(facet_query)
        self.get_params['rows'] = rows
        data = urlencode(self.get_params, True)
        try:
            url = url + '?' + data
            settings.LOGGER.debug("Executing query at SOLR : %s" % (url,))
            u = urlopen(url)
        except:
            settings.LOGGER.error("Error occured at SOLR : %s" % (traceback.format_exc(),))
            return {'numFound':0, 'docs': [], }
        return self.parse_result(u.read(), url)


    def parse_result(self, data, url):
        data = ast.literal_eval(data)
        docs = data['response']['docs']
        if self.get_params['hl'] == 'false':
            return data['response']['numFound'], docs
        hls = data['highlighting']
        for e in docs:
            e['hl'] = '...'.join(hls[str(e['id'])].get(self.get_params['hl.fl'], ''))
        return {'numFound':data['response']['numFound'],
                'maxScore':data['response']['maxScore'],
                'docs': docs,
                'facets': data.get('facet_counts'),
                'url': url
                }
        




