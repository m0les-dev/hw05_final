from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст длиннее 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_text_label(self):
        """verbose_name поля text совпадает с ожидаемым."""
        verbose_test = PostModelTest.post
        verbose = verbose_test._meta.get_field('text').verbose_name
        self.assertEqual(verbose, 'Текст поста')

    def test_text_help_text(self):
        """help_text поля title совпадает с ожидаемым."""
        helptext_test = PostModelTest.post
        help_text = helptext_test._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Введите текст поста')


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_group_label(self):
        """verbose_name поля group совпадает с ожидаемым."""
        verbose_test = GroupModelTest.group
        verbose = verbose_test._meta.get_field('title').verbose_name
        self.assertEqual(verbose, 'Название группы')

    def test_group_help_text(self):
        """help_text поля group совпадает с ожидаемым."""
        helptext_test = GroupModelTest.group
        help_text = helptext_test._meta.get_field('title').help_text
        self.assertEqual(help_text, 'Введите название группы')
