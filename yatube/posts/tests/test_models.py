from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names_group(self):
        """Проверка корректности работы метода __str__ мо"""
        group = PostModelTest.group
        post = PostModelTest.post
        expected_object_title = group.title
        self.assertEqual(expected_object_title, str(group))
        expected_object_text = post.text
        self.assertEqual(expected_object_text, str(post))

    def test_models_post_have_verbose_name(self):
        """verbose_name поля title и group совпадает с ожидаемым."""
        post = PostModelTest.post
        verbose_text = post._meta.get_field('text').verbose_name
        verbose_group = post._meta.get_field('group').verbose_name
        self.assertEqual(verbose_text, 'Текст поста')
        self.assertEqual(verbose_group, 'Группа')

    def test_models_post_have_help_text(self):
        """help_text поля title и group совпадает с ожидаемым."""
        post = PostModelTest.post
        help_text_text = post._meta.get_field('text').help_text
        help_text_group = post._meta.get_field('group').help_text
        self.assertEqual(help_text_text, 'Текст нового поста')
        self.assertEqual(
            help_text_group, 'Группа, к которой будет относиться пост'
        )
