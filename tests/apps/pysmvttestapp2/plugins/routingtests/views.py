from pysmvt.views import View
from pysmvt.routing import current_url

class CurrentUrl(View):

    def default(self):
        return current_url()
