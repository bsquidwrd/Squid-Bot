from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, RequestFactory
from django.urls import reverse

from gaming import utils
from gaming.models import Server, DiscordUser, ServerUser


class ViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='bsquidwrd', email='someone@example.com', password='top_secret')
        self.server = Server.objects.create(server_id='225471771355250688', name='Squid Bot Testing Server')
        self.discord_user = DiscordUser.objects.create(user_id='251960188217720832', name='Squid Testing Bot')

    def test_index(self):
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)

    def test_server_view(self):
        resp = self.client.get(reverse('server', kwargs={'server_id': self.server.server_id}))
        self.assertEqual(resp.status_code, 200)

    def test_user_view(self):
        resp = self.client.get(reverse('user', kwargs={'user_id': self.discord_user.user_id}))
        self.assertEqual(resp.status_code, 200)
