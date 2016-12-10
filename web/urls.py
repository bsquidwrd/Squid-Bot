"""gaming URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import TemplateView

from gaming import views


urlpatterns = [
    url(r'^humans.txt$', TemplateView.as_view(template_name='humans.txt', content_type='text/plain'), name='humans'),
    url(r'^$', views.index_view, name='index'),
    url(r'^server/(?P<server_id>\w+)/$', views.server_view, name='server'),
    url(r'^user/(?P<user_id>\w+)/$', views.user_view, name='user'),
    url(r'^accounts/update/', views.update_account_view, name='account_update'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', admin.site.urls),
]
