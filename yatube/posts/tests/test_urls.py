from http import HTTPStatus
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='Текстовое описание',
        )
        cls.post = Post.objects.create(
            text='Текстовый текст',
            author=cls.user,
            group=cls.group,
        )

        cls.guest_client = Client()

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_post_guest_url(self):
        url_names = [
            '/',
            '/group/test-slug/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_authorized_url(self):
        url_names = [
            '/create/',
            reverse('posts:post_edit', args=[self.post.id]),
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_post_edit_correct_template(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              args=[self.post.id]))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            cache.clear()
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Несуществующая страница"""
        response = self.client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
