# -*- coding: utf-8 -*-

from pysmvt.view import RespondingViewBase
from pysmvt.routing import current_url

class CurrentUrl(RespondingViewBase):

    def default(self):
        return current_url()
        
