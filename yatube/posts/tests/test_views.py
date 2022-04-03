import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User, Comment, Follow

USERNAME = 'test-username'
USERNAME_B = 'yet-another-username'
INDEX = 'posts:index'
GROUP_LIST = 'posts:posts'
POST_CREATE = 'posts:post_create'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POSTS_PER_PAGE = 10
THIRD_PAGE = 3
EXIST = 1
NOT_EXIST = 0
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(
            username=USERNAME_B)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
        )
        small_gif = SMALL_GIF
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.another_authorized_client = Client()
        cls.another_authorized_client.force_login(
            cls.another_user)

        cls.PROFILE = 'posts:profile'
        cls.POST_DETAIL = 'posts:post_detail'
        cls.POST_EDIT = 'posts:post_edit'
        Follow.objects.create(user=PostPagesTests.user,
                              author=PostPagesTests.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_reverse_name_correct_html(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(INDEX): 'posts/index.html',
            reverse(GROUP_LIST, kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse(self.PROFILE, kwargs={'username': USERNAME}): (
                'posts/profile.html'
            ),
            reverse(self.POST_DETAIL, args=[self.post.id]): (
                'posts/post_detail.html'
            ),
            reverse(POST_CREATE): (
                'posts/create_post.html'
            ),
            reverse(self.POST_EDIT, args=[self.post.id]): (
                'posts/create_post.html'
            )
        }
        for reverse_name, template in templates_pages_names.items():
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_correct_context(self):
        """Корректный общий context."""
        templates_pages_names = {
            reverse(INDEX),
            reverse(GROUP_LIST, kwargs={'slug': self.group.slug}),
            reverse(self.PROFILE, kwargs={'username': self.user.username}),
            reverse(self.POST_DETAIL, args=[self.post.id]),
        }
        for reverse_name in templates_pages_names:
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if reverse_name == reverse(self.POST_DETAIL,
                                           args=[self.post.id]):
                    first_object = response.context['post']
                else:
                    first_object = response.context.get('page_obj')[0]
                post_author_0 = first_object.author
                post_id_0 = first_object.pk
                post_text_0 = first_object.text
                post_group_0 = first_object.group.slug
                post_image_0 = first_object.image
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_id_0, self.post.pk)
                self.assertEqual(post_author_0, self.post.author)
                self.assertEqual(post_group_0, self.group.slug)
                self.assertEqual(post_image_0, self.post.image)

    def test_post_edit_correct_context(self):
        """Корректный context у post_edit."""
        response = self.authorized_client.get(reverse(self.POST_EDIT,
                                                      args=[self.post.id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        """Корректный context у post_create."""
        response = self.authorized_client.get(reverse(POST_CREATE))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_main_page(self):
        """Новый пост отображается на главной странице
            и на странице группы."""
        cache.clear()
        url = ((reverse(INDEX)),
               reverse(GROUP_LIST, kwargs={'slug': self.group.slug}),)
        for urls in url:
            with self.subTest(url=url):
                response = self.authorized_client.get(urls)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_not_in_your_group(self):
        """Новый пост попал не в свою группу."""
        response = self.authorized_client.get(
            reverse(
                GROUP_LIST,
                kwargs={'slug': self.group.slug},))
        self.assertNotEqual(response.context.get('page_obj'), self.post)

    def test_profile_follow(self):
        """Подписка на автора (делаем запрос, смотрим что создался
        правильный объект Follow)"""
        follow_count = Follow.objects.filter(
            user=PostPagesTests.another_user).count()
        self.another_authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': USERNAME}
                    ))
        self.assertEqual(Follow.objects.filter(
            user=PostPagesTests.another_user).count(), follow_count + EXIST)

    def test_profile_unfollow(self):
        """Отписка от автора (создаем объект Follow, делаем запрос,
        смотрим что объект удалился)"""
        follow_count = Follow.objects.filter(
            user=PostPagesTests.user).count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': USERNAME_B}
                    ))
        self.assertEqual(Follow.objects.filter(
            user=PostPagesTests.user).count(), follow_count - EXIST)

    def test_follow_index(self):
        """Проверяем, что при подписке пост автора появляется
        в ленте пользователя
        и что при подписке одного юзера пост автора
        не появляется в ленте другого. """
        Post.objects.create(
            text='Другой текст поста',
            author=PostPagesTests.another_user)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']), EXIST)
        response = self.another_authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']), NOT_EXIST)


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.user_not_authorized = User.objects.create(username='NoName')
        self.user_authorized = User.objects.create(username='Leo')
        self.not_authorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_authorized_client_allowed_to_add_comment(self):
        '''Авторизованный пользователь может оставлять комментарий.'''
        comment_quantity = Comment.objects.count()
        form_data = {
            'text': 'Comment'
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id, }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_quantity + EXIST)

    def test_guest_client_not_allowed_to_add_comment(self):
        '''Неавторизованный пользователь не может оставлять комментарий.'''
        comment_quantity = Comment.objects.count()
        form_data = {'text': 'Оставляем комментарий'}
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id, }),
            data=form_data,
            follow=True
        )
        self.assertNotEqual(Comment.objects.count(), comment_quantity + EXIST)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(
            username=USERNAME_B)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
        )
        small_gif = SMALL_GIF
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.PROFILE = 'posts:profile'
        cls.POST_DETAIL = 'posts:post_detail'
        cls.POST_EDIT = 'posts:post_edit'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_cache(self):
        url = reverse(INDEX)
        response = self.client.get(url).content
        Post.objects.create(
            text='Текст тестовый',
            group=self.group,
            author=self.user
        )
        self.assertEqual(response, self.client.get(url).content)
        cache.clear()
        self.assertNotEqual(response, self.client.get(url).content)


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.PROFILE = 'posts:profile'
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
        )
        cls.post = (Post(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст') for i in range(1, 14))
        Post.objects.bulk_create(cls.post)

    def test_first_page_paginator(self):
        """Правильная работа паджинатора на первой странице."""
        urls = [
            reverse(INDEX),
            reverse(GROUP_LIST, kwargs={'slug': self.group.slug}),
            reverse(self.PROFILE, args=[USERNAME]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_PER_PAGE)

    def test_second_page_paginator(self):
        """Правильная работа паджинатора на второй странице."""
        urls = [
            reverse(INDEX) + '?page=2',
            reverse(GROUP_LIST,
                    kwargs={'slug': self.group.slug}) + '?page=2',
            reverse(self.PROFILE, args=[USERNAME]) + '?page=2',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), THIRD_PAGE)
