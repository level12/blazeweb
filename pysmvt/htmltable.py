"""
    Example:
    
    t = Table()
    t.name = Link('Name', 'contentbase:AttributeCategoriesUpdate', 'id')
    t.display = Col('Display')
    t.inactive = YesNo('Active', reverse=True)
    t.created = DateTime('Created')
    t.last_edited = DateTime('Last Updated')
    t.render(dic_or_list)
"""
from pysmvt.utils import OrderedProperties, isurl
from pysmvt.routing import url_for
from webhelpers.html import HTML, literal
from webhelpers.html.tags import link_to
from webhelpers.containers import NotGiven

class StringIndentHelper(object):

    def __init__(self):
        self.output = []
        self.level = 0
        self.indent_with = '    '
    
    def dec(self, value):
        self.level -= 1
        return self.render(value)
            
    def inc(self, value):
        self.render(value)
        self.level += 1
    
    def __call__(self, value, **kwargs):
        self.render(value)
    
    def render(self, value, **kwargs):
        self.output.append('%s%s' % (self.indent(**kwargs), value) )
    
    def indent(self, level = None):
        if level == None:
            return self.indent_with * self.level
        else:
            return self.indent_with * self.level
    
    def get(self):
        retval = '\n'.join(self.output)
        self.output = []
        return retval

class HtmlAttributeHolder(object):
    def __init__(self, **kwargs):
        #: a dictionary that represents html attributes
        self.attributes = kwargs
        
    def setAttributes(self, **kwargs ):
        self.attributes.update(kwargs)
        
    def setAttribute(self, key, value):
        self.attributes[key] = value
    
    def getAttributes(self):
        return self.attributes
    
    def getAttribute(self, attr):
        return self.attributes[attr]

class Table(OrderedProperties):
    def __init__(self, **kwargs):
        # avoid accesiblity errors when running validation
        if not kwargs.has_key('summary'):
            kwargs['summary'] = ''
        if not kwargs.has_key('cellpadding'):
            kwargs['cellpadding'] = 0
        if not kwargs.has_key('cellspacing'):
            kwargs['cellspacing'] = 0
        self.attrs = kwargs
        # this has to go after all our initilization b/c otherwise the attributes
        # get put into _data
        OrderedProperties.__init__(self)

    def render(self, iterable):
        ind = StringIndentHelper()
        if len(iterable) > 0:
            # start table
            ind.inc(HTML.table(_closed=False, **self.attrs))
            ind.inc('<thead>')
            ind.inc('<tr>')
            # loop through columns for header
            for name, col in self._data.items():
                ind(col.render_th())
            ind.dec('</tr>')
            ind.dec('</thead>')
            ind.inc('<tbody>')
            # loop through rows
            for value in iterable:
                ind.inc('<tr>')
                # loop through columns for data
                for name, col in self._data.items():                    
                    ind(col.render_td(value, name))
                ind.dec('</tr>')
            ind.dec('</tbody>')
            ind.dec('</table>')
            return ind.get()
        else:
            return ''
        

class Col(object):
    def __init__(self, header, **kwargs):
        # attributes for column's <td> tags
        self.attrs_td = dict([(k[:-3],v) for k,v in kwargs.items() if k.endswith('_td')])
        #: attributes for column's <th> tag
        self.attrs_th = dict([(k[:-3],v) for k,v in kwargs.items() if k.endswith('_th')])
        #: string that will display in <th> or callable to get said string
        self.header = header
        #: data for the row we are currently processing
        self.crow = None
        
    def render_th(self):
        return HTML.th(self.header, **self.attrs_th)
        
    def render_td(self, row, key):
        self.crow = row
        contents = self.process(key)
        return HTML.td(contents, **self.attrs_td)
    
    def extract(self, name):
        """ extract a value from the current row """
        # dictionary style
        try:
            return self.crow[name]
        except TypeError:
            pass
        
        # attribute style
        try:
            return getattr(self.crow, name)
        except AttributeError, e:
            if ("object has no attribute '%s'" % name) not in str(e):
                raise
        
        # can't figure out how to get value
        raise TypeError('could not retrieve value from row, unrecognized row type')
        
    def process(self, key):
        return self.extract(key)

class Link(Col):
    def __init__(self, header, urlfrom='url', **kwargs):
        Col.__init__(self, header, **kwargs)
        self.urlfrom = urlfrom
        self._link_attrs = {}
        
    def process(self, key):
        url = self.extract(self.urlfrom)
        if url is not None and isurl(url):
            return link_to(self.extract(key), url, **self._link_attrs)
        return self.extract(key)
    
    def attrs(self, **kwargs):
        self._link_attrs = kwargs
        # this is made to be tacked onto the initial instantiation, so
        # make sure we return the instance
        return self

class Links(Col):
    def __init__(self, header, *args, **kwargs):
        Col.__init__(self, header, **kwargs)
        self.aobjs = args
        
    def process(self, key):
        return literal(''.join([a.process(key, self.extract) for a in self.aobjs]))

class A(object):
    """ a container class used by Links """
    def __init__(self, endpoint, *args, **kwargs):
        self.endpoint = endpoint
        if kwargs.has_key('label'):
            self.label = kwargs['label']
            del kwargs['label']
        else:
            self.label = NotGiven
        self.url_arg_keys = args
        self.attrs = kwargs
    
    def process(self, name, extract):
        url_args = dict([(key, extract(key)) for key in self.url_arg_keys])
        url = url_for(self.endpoint, **url_args)
        if self.label is NotGiven:
            label = extract(name)
        else:
            label = self.label
        return link_to(label, url, **self.attrs )

class YesNo(Col):
    def __init__(self, header, reverse=False, yes='yes', no='no', **kwargs):
        Col.__init__(self, header, **kwargs)
        self.reversed = reverse
        self.yes = yes
        self.no = no
        
    def process(self, key):
        value = self.extract(key)
        if self.reversed:
            value = not value
        if value:
            return self.yes
        else:
            return self.no
        
class TrueFalse(YesNo):
    def __init__(self, header, reverse=False, true='true', false='false', **kwargs):
        YesNo.__init__(self, header, reverse, true, false, **kwargs)

class DateTime(Col):
    def __init__(self, header, format='%m/%d/%y %H:%M', on_none='', **kwargs):
        Col.__init__(self, header, **kwargs)
        self.format = format
        self.on_none = on_none
    
    def process(self, key):
        value = self.extract(key)
        if value == None:
            return self.on_none
        return value.strftime(self.format)
