from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group, Follow


User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=PostViewsTest.author,
            text='Тестовый пост номер',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_pages_auth_user_correct_template(self):
        """Проверка корректности шаблонов"""
        templates_pages_names = {
            'posts:index': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/group_list.html': (
                reverse('posts:post_list', kwargs={'slug': 'test-slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'auth'})
            )
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_auth_user_correct_template(self):
        """Проверка корректности шаблонов для авторизованного пользователя"""
        templates_pages_names = {
            'posts/create_post.html': (
                reverse('posts:post_edit',
                        kwargs={'post_id': PostViewsTest.post.id}
                        )
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': PostViewsTest.post.id}
                        )
            )
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Проверка контекста главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, PostViewsTest.post.text)
        self.assertEqual(first_object.author, PostViewsTest.post.author)
        self.assertEqual(first_object.group, PostViewsTest.group)
        self.assertEqual(first_object.image, PostViewsTest.post.image)

    def test_paginator(self):
        """Проверка корректности паджинатора"""
        paginator_objects = []
        for item in range(0, 15):
            new_post = Post(
                author=PostViewsTest.author,
                text=f'Тестовый пост {item}',
                group=PostViewsTest.group
            )
            paginator_objects.append(new_post)
        Post.objects.bulk_create(paginator_objects)
        paginator_data = {
            'index': reverse('posts:index'),
            'group': reverse(
                'posts:post_list',
                kwargs={'slug': PostViewsTest.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PostViewsTest.author.username}
            )
        }
        for paginator_place, paginator_page in paginator_data.items():
            with self.subTest(paginator_place=paginator_place):
                response_page_1 = self.authorized_client.get(paginator_page)
                response_page_2 = self.authorized_client.get(
                    paginator_page + '?page=2'
                )
                self.assertEqual(len(
                    response_page_1.context['page_obj']),
                    10
                )
                self.assertEqual(len(
                    response_page_2.context['page_obj']),
                    6
                )

    def test_group_list_show_correct_context(self):
        """Проверка контекста страниц групп"""
        response = self.authorized_client.\
            get(reverse('posts:post_list', kwargs={
                'slug': PostViewsTest.group.slug
            }))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        group_obj = response.context['group']
        self.assertEqual(group_obj.title, PostViewsTest.group.title)
        self.assertEqual(
            group_obj.description, PostViewsTest.group.description
        )
        page_obj = response.context['page_obj'][0]
        self.assertEqual(page_obj.author, PostViewsTest.author)
        self.assertEqual(page_obj.text, PostViewsTest.post.text)
        self.assertEqual(page_obj.image, PostViewsTest.post.image)

    def test_profile_show_correct_context(self):
        """Проверка контекста профиля"""
        response = self.authorized_client.\
            get(reverse('posts:profile', kwargs={'username': 'auth'}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        profile_obj = response.context['author']
        self.assertEqual(
            profile_obj.username, PostViewsTest.author.username
        )

        page_obj = response.context['page_obj'][0]
        self.assertEqual(page_obj.text, PostViewsTest.post.text)
        self.assertEqual(page_obj.group, PostViewsTest.group)
        self.assertEqual(page_obj.image, PostViewsTest.post.image)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста одного поста"""
        response = self.authorized_client.\
            get(reverse(
                'posts:post_detail', kwargs={'post_id': PostViewsTest.post.id}
            ))
        page_obj = response.context['post']
        self.assertEqual(page_obj.text, PostViewsTest.post.text)
        self.assertEqual(page_obj.group, PostViewsTest.group)
        self.assertEqual(page_obj.author, PostViewsTest.author)
        self.assertEqual(page_obj.image, PostViewsTest.post.image)

    def test_create_post_show_correct_context(self):
        """Проверка контекста создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Проверка контекста редактирования поста"""
        response = self.author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': PostViewsTest.post.id})
        )
        form_field = response.context.get('form').instance.id
        self.assertEqual(form_field, PostViewsTest.post.id)

    def test_create_post_with_one_group(self):
        """Проверка создания поста только в одной группе"""
        responce = self.authorized_client.get(reverse(
            'posts:post_list', kwargs={'slug': 'test-slug2'}))
        page_obj = responce.context['page_obj']
        self.assertEqual(len(page_obj), 0)

    def test_index_cache(self):
        """Проверка кеша главной страницы"""
        cache.clear()
        responce = self.authorized_client.get(reverse('posts:index'))
        Post.objects.get(pk=self.post.id).delete()
        self.assertIn(self.post.text.encode(), responce.content)
        cache.clear()
        self.assertNotEqual(self.post.text.encode(), responce.content)

    def test_authors_follow(self):
        """Проверка подписки на авторов"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists()
        )

    def test_authors_unfollow(self):
        """Проверка отписки от авторов"""
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists()
        )

    def test_existence_of_follow_user(self):
        """Проверка наличия подписки на авторов"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            ))
        new_post = Post.objects.create(
            text='новый пост для проверки',
            author=self.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_existence_of_unfollow_user(self):
        """Проверка наличия отписки от автора"""
        Post.objects.create(
            text='Новый пост для проверки',
            author=self.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
