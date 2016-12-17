import json
import sys
from django.core import serializers
from inspect import getframeinfo, getouterframes, currentframe


def logify_object(obj):
    return json.dumps(json.loads(serializers.serialize("json", obj)), sort_keys=True, indent=4)


def logify_dict(d):
    return json.dumps(d, sort_keys=True, indent=4)


def logify_exception_info():
    return "Filename: {0.tb_frame.f_code.co_filename}\nLine: {0.tb_lineno}\n".format(sys.exc_info()[2])


def current_line():
    return getouterframes(currentframe())[1].lineno
