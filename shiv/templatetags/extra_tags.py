#!/usr/bin/env python
#
#       extra_tags.py
#       
from django import template
from django.utils.safestring import mark_safe


register = template.Library()

@register.simple_tag
def form_as_shiv(form, state):
    return form.as_shiv(state=state)

@register.filter
def render_node(node, arg=100):
  if 'text' in node:
    node['text'] = truncate_length(node['text'], arg)
  if node['type'] == 'has_data_id':
    t = "<%(tag_type)s class='has_data_id %(extra_class)s' data-id='%(data_id)s'>%(text)s</%(tag_type)s>" % node
  elif node['type'] == 'has_link':
    t = "<a href='%(link)s' class='has_link %(extra_class)s' target='%(target)s'>%(text)s</a>" % node
  elif node['type'] == 'has_image':
    t = "<a href='%(link)s' class='has_image %(extra_class)s' target='%(target)s'><img class='rollover' data-rollover='%(image_link_over)s' src='%(image_link)s' alt='%(text)s' /></a>"
  else:
    t = "<%(tag_type)s class='plain_text %(extra_class)s'>%(text)s</%(tag_type)s>" % node
  return mark_safe(t)

@register.filter
def truncate_length(string, arg):
    if len(string) > arg:
        return string[:arg - 3] + '...'
    return string

@register.filter
def result_count_text(ppage):        
        paginator = ppage.paginator
        total = paginator.count
        start_count = ((ppage.number - 1) * paginator.per_page)
        result_count = start_count + len(ppage.object_list)        
        result_count = result_count if result_count <= total else total 
        result_string = '%d to %d of %d' % (start_count + 1 , result_count, total) if  (total != 0)\
                        else "0"        
        return result_string    

@register.filter
def comma_seperated_list(alist):
    '''
    returns comman seperated values from a list, adds "and" between the last two elements.
    '''
    if len(alist)>1:        
        return ", ".join(alist[:-1])+' and '+alist[-1]
    if len(alist)==1:
        return alist[0]
    return ''
