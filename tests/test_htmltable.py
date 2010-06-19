import config
import difflib
import unittest
from nose.tools import eq_
from pysmvt.htmltable import Table, Col, A
from pysmvt.routing import Rule
from pysmvt.testing import inrequest

def eq_or_diff(actual, expected):
    assert actual == expected, \
    '\n'.join(list(
        difflib.unified_diff(actual.split('\n'), expected.split('\n'))
    ))

def test_basic():
    data = (
        {'color': 'red', 'number': 1},
        {'color': 'green', 'number': 2},
        {'color': 'blue', 'number': 3},
    )
    t = Table()
    t.color = Col('Color')
    t.number = Col('Number')
    result = """<table cellpadding="0" cellspacing="0" summary="">
    <thead>
        <tr>
            <th>Color</th>
            <th>Number</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>red</td>
            <td>1</td>
        </tr>
        <tr>
            <td>green</td>
            <td>2</td>
        </tr>
        <tr>
            <td>blue</td>
            <td>3</td>
        </tr>
    </tbody>
</table>"""
    eq_(result, t.render(data))

def test_row_dec():
    data = (
        {'color': 'red', 'number': 1},
        {'color': 'green', 'number': 2},
        {'color': 'blue', 'number': 3},
    )
    def row_decorator(row_num, row_attrs, row):
        if row_num % 2 == 0:
            row_attrs.add_attr('class', 'even')
        else:
            row_attrs.add_attr('class', 'odd')
        row_attrs.add_attr('class', row['color'])
    t = Table(row_dec = row_decorator)
    t.color = Col('Color')
    t.number = Col('Number')
    result = """<table cellpadding="0" cellspacing="0" summary="">
    <thead>
        <tr>
            <th>Color</th>
            <th>Number</th>
        </tr>
    </thead>
    <tbody>
        <tr class="odd red">
            <td>red</td>
            <td>1</td>
        </tr>
        <tr class="even green">
            <td>green</td>
            <td>2</td>
        </tr>
        <tr class="odd blue">
            <td>blue</td>
            <td>3</td>
        </tr>
    </tbody>
</table>"""
    eq_or_diff(result, t.render(data))

class ATestSettings(config.Testruns):
    def init(self):
        config.Testruns.init(self)

        self.routing.routes.extend([
            Rule('/index/<arg1>/<arg2>', endpoint='mod:Index'),
        ])

class TestA(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.app = config.make_wsgi(ATestSettings)

    @inrequest()
    def test_links(self):
        dbobj_fake = {'arg1': 1, 'arg2': 2, 'db1': 10, 'db2': 20, 'title': 'fake_object'}
        dummy_col = Col('test')
        dummy_col.crow = dbobj_fake

        a1 = A('mod:Index', 'arg1:db1', 'arg2', label='split', class_='name_split', title='Different names for arg and field')
        a2 = A('mod:Index', 'arg1', 'arg2:db2', class_='name_single', title='Same names for arg and field')

        self.assertEqual(a1.process('title',dummy_col.extract), '<a class="name_split" href="/index/10/2" title="Different names for arg and field">split</a>')
        self.assertEqual(a2.process('title',dummy_col.extract), '<a class="name_single" href="/index/1/20" title="Same names for arg and field">fake_object</a>')
