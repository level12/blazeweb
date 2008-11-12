# -*- coding: utf-8 -*-
import sys
from pysmvt import settings, ag
from pysmvt.application import request_context as rc
from pysmvt.utils import traceback_depth, module_import
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
import elixir

def load_orm_models():
    for module in settings.modules.keys():
            try:
                module_import('%s.model.orm' % module, [])
            except ImportError:
                # check the exception depth to make sure the import
                # error we caught was just .model or .model.orm missing
                _, _, tb = sys.exc_info()
                # 2 = view class name wasn't found
                # 3 = .model wasn't found
                #print traceback_depth(tb)
                if traceback_depth(tb) in (3,):
                    pass
                else:
                    raise

def load_metadata_models():
    for module in settings.modules.keys():
            try:
                module_import('%s.model.metadata' % module, [])
            except ImportError:
                # check the exception depth to make sure the import
                # error we caught was just .model or .model.orm missing
                _, _, tb = sys.exc_info()
                # 2 = view class name wasn't found
                # 3 = .model wasn't found
                #print traceback_depth(tb)
                if traceback_depth(tb) in (3,):
                    pass
                else:
                    raise

def load_models():
    # load all the ORM objects
    load_orm_models()
    
    # now setup ORM metadata
    elixir.setup_all()
    
    # now load metadata
    load_metadata_models()

def get_engine():
    if hasattr(rc, 'db_engine') == False :
        rc.db_engine = create_engine(settings.db.uri, echo=settings.db.echo, strategy='threadlocal')   
    
    return rc.db_engine

def get_metadata():
    if hasattr(ag, 'dbMetaData') == False :
        from sqlalchemy import MetaData
        ag.dbMetaData = MetaData()
        
    return ag.dbMetaData

def get_session_cls():
    if not ag.get('db_scoped_session', None):
        ag.db_scoped_session = scoped_session(sessionmaker())
    ag.db_scoped_session.configure(bind=get_engine())
    return ag.db_scoped_session

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
