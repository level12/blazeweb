from werkzeug.routing import Rule

from pysmvt.utils import QuickSettings, pprint

class Settings(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        self.routes = ([
            Rule('/tests/rvb', endpoint='tests:Rvb'),
            Rule('/tests/rvbwsnip', endpoint='tests:RvbWithSnippet'),
            Rule('/tests/get', endpoint='tests:Get'),
            Rule('/tests/post', endpoint='tests:Post'),
            Rule('/tests/prep', endpoint='tests:Prep'),
            Rule('/tests/noactionmethod', endpoint='tests:NoActionMethod'),
            Rule('/tests/tworespondingviews', endpoint='tests:TwoRespondingViews'),
            Rule('/tests/doforward', endpoint='tests:DoForward'),
            Rule('/tests/badforward', endpoint='tests:BadForward'),
            Rule('/tests/badroute', endpoint='tests:HwSnippet'),
            Rule('/tests/text', endpoint='tests:Text'),
            Rule('/tests/textwsnip', endpoint='tests:TextWithSnippet'),
            Rule('/tests/textwsnip2', endpoint='tests:TextWithSnippet2'),
            Rule('/tests/badmod', endpoint='fatfinger:NotExistant'),
            Rule('/tests/noview', endpoint='tests:NotExistant'),
            Rule('/tests/html', endpoint='tests:Html'),
            Rule('/tests/htmlcssjs', endpoint='tests:HtmlCssJs'),
        ])
        
        # no more values can be added
        self.lock()