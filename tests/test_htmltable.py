import difflib
from pysmvt.htmltable import Table, Col
from nose.tools import eq_

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