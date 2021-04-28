from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from hashid_field import Hashid


class MyJsonEncoder(DjangoJSONEncoder):

    def default(self, obj):
        if isinstance(obj, Hashid):
            return str(obj)
        return super().default(obj)

class MyJsonResponse(JsonResponse):
    def __init__(self, data, safe=True,
                 json_dumps_params=None, **kwargs):
        super(MyJsonResponse, self).__init__(data=data, encoder=MyJsonEncoder, safe=safe, json_dumps_params=json_dumps_params, **kwargs)
