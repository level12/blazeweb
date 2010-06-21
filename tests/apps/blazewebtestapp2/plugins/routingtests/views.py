from blazeweb.views import View
from blazeweb.routing import current_url

class CurrentUrl(View):

    def default(self):
        return current_url()
