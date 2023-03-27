from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from http import HTTPStatus

from ..models import Post, Group


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=PostsURLTests.author,
            text='Тестовый пост'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_public_pages(self):
        """Тестирование доступных страниц """
        context = [
            '/',
            '/group/test-slug/',
            '/profile/auth/',
            '/posts/1/',
        ]
        for adress in context:
            with self.subTest(adress=adress):
                cache.clear()
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_url(self):
        """Тестирование недоступных страниц """
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url(self):
        """Тестирование /create """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url(self):
        """Тестирование /post_edit """
        response = self.author_client.get(
            f'/posts/{PostsURLTests.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_template(self):
        """Тестирование общедоступных шаблонов """
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_post_template(self):
        """Тестирование шаблона создания поста """
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_post_template(self):
        """Тестирование шаблона редактирования поста """
        response = self.author_client.get(
            f'/posts/{PostsURLTests.post.id}/edit/'
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_redirect_post_for_guest_user(self):
        """Тестирование редиректа при попытке редактирования поста гостем"""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.id}/edit/'))

    def test_redirect_post_for_authorized_client(self):
        """Тестирование редиректа при редактирования поста не автором"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/'))
