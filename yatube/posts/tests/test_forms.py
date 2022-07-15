import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormPost(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=123,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            group=cls.group,
            text='тестовый текст',
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        '''Валидная форма создает запись в posts'''
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {'text': 'тестовый текст', 'group': self.group.id,
                     'image': uploaded}
        page_post_creat = reverse('posts:post_create')
        page_profile = reverse('posts:profile',
                               kwargs={'username': self.user_author.username})

        response = self.authorized_client.post(page_post_creat, data=form_data,
                                               follow=True)

        self.assertRedirects(response, page_profile)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(Post.objects.first().image.size, uploaded.size)
        self.assertTrue(
            Post.objects.filter(
                text='тестовый текст',
                author=self.user_author,
                group=self.group.id,
            ).exists()
        )

    def test_comment_add(self):
        '''Комментарий попадает в БД'''
        form_data = {'text': 'Текст комментария'}
        page_add_comment = reverse('posts:add_comment',
                                   kwargs={'post_id': self.post.id})

        self.authorized_client.post(page_add_comment,
                                    data=form_data, follow=True)
        self.assertTrue(Comment.objects.filter(
            text='Текст комментария',
            author=self.user_author,
        ))

    def test_post_edit(self):
        '''Валидная форма изменяет запись в posts'''
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {'text': 'редактированый тестовый текст',
                     'group': self.group.id, 'image': uploaded}

        page_post_edit = reverse('posts:post_edit', args=(self.post.id,))
        page_post_detail = reverse('posts:post_detail', args=(self.post.id,))

        response = self.authorized_client.post(page_post_edit, data=form_data,
                                               follow=True)
        self.assertEqual(Post.objects.first().image.size, uploaded.size)
        self.assertRedirects(response, page_post_detail)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='редактированый тестовый текст',
                group=self.group.id,
                author=self.user_author,
            ).exists()
        )
