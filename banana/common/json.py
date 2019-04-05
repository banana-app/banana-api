from dataclasses_json import dataclass_json, DataClassJsonMixin
from dataclasses_json.core import _decode_dataclass, _isinstance_safe, _ExtendedEncoder as DataclassEncoder, JSON, \
    _override, _overrides, _asdict
from dataclasses_json.api import A
from typing import List, Optional, Union, Tuple, Callable, Collection
from uuid import UUID
from enum import Enum
import json
from datetime import date, datetime


# Those things are just dirty hacks to:
# * properly handle date properties in dataclass serialization
# * properly handle date fields json deserialization

class _DateAwareJsonEncoder(DataclassEncoder):
    def default(self, o) -> JSON:
        to_json_op = getattr(o, "to_json", None)
        result: JSON
        if _isinstance_safe(o, Collection):
            if _isinstance_safe(o, Mapping):
                result = dict(o)
            else:
                result = list(o)
        elif _isinstance_safe(o, datetime):
            result = o.isoformat()
        elif _isinstance_safe(o, date):
            result = o.isoformat()
        elif _isinstance_safe(o, UUID):
            result = str(o)
        elif _isinstance_safe(o, Enum):
            result = o.value
        elif to_json_op != None and callable(to_json_op):
            result = {k: v for k, v in o.__dict__.items() if not (k.startswith('_'))}
        else:
            result = json.JSONEncoder.default(self, o)
        return result


def _date_hook(json_dict):
    for (key, value) in json_dict.items():
        # noinspection PyBroadException
        try:
            json_dict[key] = datetime.strptime(value, "%Y-%M-%d").date()
        except:
            pass
    return json_dict


class BananaDataclassJsonMixin(DataClassJsonMixin):

    def to_json(self,
                *,
                cls=_DateAwareJsonEncoder,
                skipkeys: bool = False,
                ensure_ascii: bool = True,
                check_circular: bool = True,
                allow_nan: bool = True,
                indent: Optional[Union[int, str]] = None,
                separators: Tuple[str, str] = None,
                default: Callable = None,
                sort_keys: bool = False,
                **kw) -> str:
        kvs = _override(_asdict(self), _overrides(self), 'encoder')
        return json.dumps(kvs,
                          cls=_DateAwareJsonEncoder,
                          skipkeys=skipkeys,
                          ensure_ascii=ensure_ascii,
                          check_circular=check_circular,
                          allow_nan=allow_nan,
                          indent=indent,
                          separators=separators,
                          default=default,
                          sort_keys=sort_keys,
                          **kw)

    @classmethod
    def from_json(cls: A,
                  s: str,
                  *,
                  object_hook=_date_hook,
                  encoding=None,
                  parse_float=None,
                  parse_int=None,
                  parse_constant=None,
                  infer_missing=False,
                  **kw) -> A:
        kvs = json.loads(s,
                         object_hook=_date_hook,
                         encoding=encoding,
                         parse_float=parse_float,
                         parse_int=parse_int,
                         parse_constant=parse_constant,
                         **kw)
        return _decode_dataclass(cls, kvs, infer_missing)


def json_serializable(cls):
    cls.to_json = BananaDataclassJsonMixin.to_json
    # unwrap and rewrap classmethod to tag it to cls rather than the literal
    # DataClassJsonMixin ABC
    cls.from_json = classmethod(BananaDataclassJsonMixin.from_json.__func__)
    cls.schema = classmethod(BananaDataclassJsonMixin.schema.__func__)
    # register cls as a virtual subclass of DataClassJsonMixin
    BananaDataclassJsonMixin.register(cls)
    return cls
