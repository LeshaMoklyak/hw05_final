import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            author=PostCreateFormTests.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guess_client = Client()
        self.user = User.objects.create(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post"""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый заголовок2',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.latest('id')
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username,
        }))
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый заголовок2',
                group=self.group.id,
            ).exists()
        )
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post"""
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='new_group_title',
            slug='new_group_slug',
            description='new_group_description'

        )
        form_data = {
            'text': 'Тестовый пост',
            'group': new_group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edit_post = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edit_post.text, 'Тестовый пост')
        self.assertEqual(edit_post.group, new_group)

        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.id}))
        self.assertTrue(Post.objects.filter(
            text='Тестовый пост',
            group=new_group,
        ).exists()
        )
        old_group_response = self.authorized_client.get(
            reverse('posts:post_list', args=(self.group.slug,))
        )
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count, 0
        )

    def test_create_post_with_image(self):
        """Валидная форма создает запись с картинкой в Post"""
        tasks_count = Post.objects.count()

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
        form_data = {
            'text': 'Изменение картинки',
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Изменение картинки',
                image='posts/small.gif'
            ).exists()
        )

    def test_create_comment(self):
        """Валидная форма создает запись в Comment"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'новый комментарий'
        }

        response = self.guess_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='новый комментарий',
            ).exists()
        )
        Comment.objects.create(
            post=self.post,
            author=self.user,
            created=self.authorized_client
        )
        new_comment = Comment.objects.latest('id')
        self.assertEqual(new_comment.author, self.user)
        self.assertEqual(new_comment.post, self.post)
