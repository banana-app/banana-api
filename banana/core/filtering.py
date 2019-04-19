from typing import Type

from funcy import some, monkey
from marshmallow import Schema, fields, EXCLUDE
from sqlalchemy.orm import Query
from whatever import _

from banana.common import total_pages

_ops = {
    'eq': lambda query, atr, v: query.filter(atr == v),
    'neq': lambda query, atr, v: query.filter(atr != v),
    'like': lambda query, atr, v: query.filter(atr.like(f'%{v}%'))
}


def _value(v):
    if v.lower() == 'true':
        return True
    elif v.lower() == 'false':
        return False
    elif v.lower() == 'null' or v.lower() == 'none':
        return None
    else:
        return v


def _is_logical_term(term):
    return True if term.lower() == 'or' or term == 'and' else False


@monkey(Query)
def with_filters(self, query_string, supported_attributes, ignored=['page', 'page_size', 'order_by', 'order_direction']):
    from urllib.parse import parse_qs
    parsed_query = parse_qs(query_string)
    query = self
    for k, v in parsed_query.items():
        if some(_ == k.decode('utf-8'), ignored):
            continue
        attribute, op = k.decode('utf-8').split(':', 1)
        query = _ops[op](query, supported_attributes[attribute], _value(v[0].decode('utf-8')))
    return query


def using_attributes(**kwargs):
    return dict(**kwargs)


class PageWithOrderSchema:

    @classmethod
    def with_page_size(cls, size: int) -> Type[Schema]:
        class _PageWithOrderSchema(Schema):
            page = fields.Integer(missing=1)
            order_by = fields.String(missing='created_datetime')
            order_direction = fields.String(missing='desc')
            page_size = fields.Integer(missing=size)

        return _PageWithOrderSchema

    class Meta:
        unknown = EXCLUDE


def paginated(items: dict):
    return {
        'total_items': items.total,
        'pages': total_pages(items.total, len(items.items)) if len(items.items) > 0 else 0,
        'items': items.items}