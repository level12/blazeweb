from werkzeug.routing import Rule

from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):

        self.for_me.routes = ([
            Rule('/tests/rvb', endpoint='tests:Rvb'),
            Rule('/tests/rvbwsnip', endpoint='tests:RvbWithSnippet'),
            Rule('/tests/get', endpoint='tests:Get'),
            Rule('/tests/post', endpoint='tests:Post'),
            Rule('/tests/prep', endpoint='tests:Prep'),
            Rule('/tests/raiseexc', endpoint='tests:RaiseExc'),
            Rule('/tests/doforward', endpoint='tests:DoForward'),
            Rule('/tests/text', endpoint='tests:Text'),
            Rule('/tests/textwsnip', endpoint='tests:TextWithSnippet'),
            Rule('/tests/textwsnip2', endpoint='tests:TextWithSnippet2'),
            Rule('/tests/badmod', endpoint='fatfinger:NotExistant'),
            Rule('/tests/noview', endpoint='tests:NotExistant'),
            Rule('/tests/html', endpoint='tests:Html'),
            Rule('/tests/redirect', endpoint='tests:Redirect'),
            Rule('/tests/permredirect', endpoint='tests:PermRedirect'),
            Rule('/tests/custredirect', endpoint='tests:CustRedirect'),
            Rule('/tests/heraise', endpoint='tests:HttpExceptionRaise'),
            Rule('/tests/forwardloop', endpoint='tests:ForwardLoop'),
            Rule('/tests/urlargs', endpoint='tests:UrlArguments'),
            Rule('/tests/urlargs/<int:anum>', endpoint='tests:UrlArguments'),
            Rule('/tests/urlargs/<towho>', endpoint='tests:UrlArguments'),
            Rule('/tests/getargs', endpoint='tests:GetArguments'),
            Rule('/tests/getargs2', endpoint='tests:GetArguments2'),
            Rule('/tests/getargs3', endpoint='tests:GetArguments3'),
            Rule('/tests/reqgetargs', endpoint='tests:RequiredGetArguments'),
            Rule('/tests/listgetargs', endpoint='tests:ListGetArguments'),
            Rule('/tests/customvalidator', endpoint='tests:CustomValidator'),
            Rule('/tests/badvalidator', endpoint='tests:BadValidator'),
            Rule('/tests/appfallback', endpoint='tests:InApp2'),
            Rule('/tests/htmltemplatefilearg', endpoint='tests:HtmlTemplateFileArg'),
            Rule('/tests/templateinheritance', endpoint='tests:TemplateInheritance'),
            Rule('/tests/parenttemplate', endpoint='tests:ParentTemplate'),
            Rule('/tests/parenttemplateinheritance', endpoint='tests:ParentTemplateInheritance'),
            Rule('/tests/modlevelpriority', endpoint='tests:ModLevelPriority'),
            Rule('/tests/htmlsnippetwithcss', endpoint='tests:HtmlSnippetWithCssParent'),
            Rule('/tests/usermessages', endpoint='tests:UserMessages'),
            Rule('/tests/tchooser/<rtype>', endpoint='tests:TemplateChooser'),
            Rule('/tests/text.txt/<towho>', endpoint='tests:text.txt'),
            Rule('/jsonify-exception', endpoint='tests:JsonifyException'),
        ])

        self.for_me.foo = 'baz'
