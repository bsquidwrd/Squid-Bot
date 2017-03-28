import json
import sys
from django.core import serializers
from inspect import getframeinfo, getouterframes, currentframe

DISCORD_MSG_CHAR_LIMIT = 2000


def paginate(content, *, length=DISCORD_MSG_CHAR_LIMIT, reserve=0):
    """
    Split up a large string or list of strings into chunks for sending to Discord.
    """
    if type(content) == str:
        contentlist = content.split('\n')
    elif type(content) == list:
        contentlist = content
    else:
        raise ValueError("Content must be str or list, not %s" % type(content))

    chunks = []
    currentchunk = ''

    for line in contentlist:
        if len(currentchunk) + len(line) < length - reserve:
            currentchunk += line + '\n'
        else:
            chunks.append(currentchunk)
            currentchunk = ''

    if currentchunk:
        chunks.append(currentchunk)

    return chunks


def logify_object(obj):
    """
    Returns a JSON string containing usually a Queryset of items based on :attr:`obj`
    """
    return json.dumps(json.loads(serializers.serialize("json", obj)), sort_keys=True, indent=4)


def logify_dict(d):
    """
    Returns a JSON string containing the information within a :attr:`d`
    """
    return json.dumps(d, sort_keys=True, indent=4)


def logify_exception_info():
    """
    Returns a string with information about the last exception that was thrown.
    """
    return "Filename: {0.tb_frame.f_code.co_filename}\nLine: {0.tb_lineno}\n".format(sys.exc_info()[2])


def current_line():
    """
    Returns the current line the function is called from
    """
    return getouterframes(currentframe())[1].lineno


def get_current_commit():
    """
    Returns the current version the bot is running
    """
    # from gaming import __version__
    # return __version__
    import subprocess
    return subprocess.check_output(["git", "rev-parse", "--verify", "HEAD"])
