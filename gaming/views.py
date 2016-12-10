from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect

from gaming.forms import UpdateAccountForm
from gaming.models import Server, DiscordUser, ServerUser
from gaming.utils import logify_exception_info


def index_view(request):
    template = 'gaming/serverlist.html'
    servers = Server.objects.all()
    context = {
        'title': 'Server List',
        'servers': servers,
    }
    return render(request, template, context)


def server_view(request, server_id):
    template = 'gaming/server.html'
    try:
        server = Server.objects.get(server_id=server_id)
    except:
        messages.add_message(request, messages.ERROR, "Requested server does not exist!")
        return redirect('index')

    serverusers = ServerUser.objects.filter(server=server, user__bot=False).exclude(user=server.owner)

    context = {
        'server': server,
        'serverusers': serverusers,
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
