import json

from django.core.serializers.json import DjangoJSONEncoder


def serialize_json_ld(data):
    """Keep database content from closing an inline JSON-LD script tag."""
    return json.dumps(data, cls=DjangoJSONEncoder).translate(str.maketrans({
        '<': '\\u003C', '>': '\\u003E', '&': '\\u0026',
    }))
