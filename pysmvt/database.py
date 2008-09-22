# -*- coding: utf-8 -*-
from pysmvt.application import request_context as rc
from sqlalchemy.orm import sessionmaker, scoped_session

def get_engine():
    if hasattr(rc.application, 'dbEngine') == False :
        from sqlalchemy import create_engine
        rc.application.dbEngine = create_engine(rc.application.settings.dbUri, echo=rc.application.settings.dbEcho)   
    
    return rc.application.dbEngine

def get_metadata():
    if hasattr(rc.application, 'dbMetaData') == False :
        from sqlalchemy import MetaData
        rc.application.dbMetaData = MetaData()
        rc.application.dbMetaData.bind = get_engine()
        
    return rc.application.dbMetaData

def get_session_cls():
    if hasattr(rc.application, 'db_scoped_session') == False :
        rc.application.db_scoped_session = scoped_session(sessionmaker(get_engine()))
    return rc.application.db_scoped_session

# an alias that can be used to avoid confusion when working in close
# proximity to beaker sessions
get_dbsession_cls = get_session_cls

def get_session():
    return get_session_cls()()

# an alias that can be used to avoid confusion when working with beaker sessions
get_dbsession = get_session

# Pagination
from werkzeug import cached_property

# from Werkzeug Shorty example
class Pagination(object):

    def __init__(self, query, per_page, page, endpoint):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint

    @cached_property
    def count(self):
        return self.query.count()

    @cached_property
    def entries(self):
        return self.query.offset((self.page - 1) * self.per_page) \
                         .limit(self.per_page).all()

    has_previous = property(lambda x: x.page > 1)
    has_next = property(lambda x: x.page < x.pages)
    previous = property(lambda x: x.page - 1)
    next = property(lambda x: x.page + 1)
    pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)