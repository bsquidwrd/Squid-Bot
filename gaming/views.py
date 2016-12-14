import re
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect

from gaming.forms import UpdateAccountForm
from gaming.models import Server, DiscordUser, ServerUser
from gaming.utils import logify_exception_info


def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:

        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.

    '''
    query = None # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


def index_view(request):
    template = 'gaming/serverlist.html'
    servers = Server.objects.all()
    search = request.GET.get('search', None)
    if search:
        servers = servers.filter(get_query(search, ['name', 'server_id', 'owner__name']))
        messages.add_message(request, messages.INFO, 'Servers filtered based on query "{}"'.format(search))
    context = {
        'title': 'Server List',
        'servers': servers,
        'search': search,
    }
    return render(request, template, context)


def server_view(request, server_id):
    template = 'gaming/server.html'
    search = request.GET.get('search', None)
    try:
        server = Server.objects.get(server_id=server_id)
    except:
        messages.add_message(request, messages.ERROR, "Requested server does not exist!")
        return redirect('index')

    serverusers = ServerUser.objects.filter(server=server, user__bot=False)
    if search:
        serverusers = serverusers.filter(get_query(search, ['user__name', 'user__user_id']))
        messages.add_message(request, messages.INFO, 'Users filtered based on query "{}"'.format(search))

    context = {
        'server': server,
        'serverusers': serverusers,
        'search': search,
    }
    return render(request, template, context)


def update_account_view(request):
    template = 'gaming/update_account.html'

    user = request.user
    if not user.is_authenticated():
        messages.add_message(request, messages.WARNING, 'Please login before accessing that page')
        return redirect('account_login')

    if request.method == 'POST':
        form = UpdateAccountForm(request.POST, instance=user)
        if form.is_valid():
            try:
                u = form.save()
                if u.is_active:
                    messages.add_message(request, messages.SUCCESS, 'Profile saved successfully!')
                    form = UpdateAccountForm(instance=u)
                else:
                    return redirect('account_logout')
            except Exception as e:
                log_item = Log.objects.create(message="Error saving form for user {}\n{}".format(user, logify_exception_info()))
                messages.add_message(request, messages.ERROR, 'An error occurred saving the settings.')
                messages.add_message(request, messages.ERROR, 'Please contact your administrator with the following: {}'.format(log_item.message_token))
        else:
            messages.add_message(request, messages.WARNING, 'The form is not valid, please try again.')
    else:
        form = UpdateAccountForm(instance=user)

    context = {
        'form': form,
    }
    return render(request, template, context)


def user_view(request, user_id):
    template = 'gaming/user.html'

    try:
        discorduser = DiscordUser.objects.get(user_id=user_id)
    except:
        messages.add_message(request, messages.ERROR, "Requested user does not exist!")
        return redirect('index')

    context = {
        'discorduser': discorduser,
    }
    return render(request, template, context)
