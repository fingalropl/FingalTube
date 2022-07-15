import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.user_not_author = User.objects.create_user(username='not_author')
        cls.not_author = Client()
        cls.not_author.force_login(cls.user_not_author)

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=123,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='тестовый текст',
            image=cls.uploaded,
        )

        cls.view_index = reverse('posts:index')
        cls.view_group_list = reverse('posts:group_list',
                                      kwargs={'slug': cls.group.slug})
        cls.view_profile = reverse('posts:profile',
                                   kwargs={'username': cls.user.username})
        cls.view_post_detail = reverse('posts:post_detail',
                                       kwargs={'post_id': cls.post.id})
        cls.view_post_create = reverse('posts:post_create')
        cls.view_post_edit = reverse('posts:post_edit',
                                     kwargs={'post_id': cls.post.id})
        cls.view_add_comment = reverse('posts:add_comment',
                                       kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        '''Страницы исользуют корректные шаблоны'''
        templates_pages_names = {
            self.view_index: 'posts/index.html',
            self.view_group_list: 'posts/group_list.html',
            self.view_profile: 'posts/profile.html',
            self.view_post_detail: 'posts/post_detail.html',
            self.view_post_edit: 'posts/post_create.html',
            self.view_post_create: 'posts/post_create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_idex_page_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом'''
        response = self.authorized_client.get(self.view_index)

        self.assertEqual(Post.objects.first().image.size, self.uploaded.size)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_posts_page_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом'''
        response = self.authorized_client.get(self.view_group_list)

        self.assertEqual(Post.objects.first().image.size, self.uploaded.size)
        self.assertEqual(response.context.get('group'), self.group)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_profile_page_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом'''
        response = self.authorized_client.get(self.view_profile)

        self.assertEqual(Post.objects.first().image.size, self.uploaded.size)
        self.assertEqual(response.context.get('author').username,
                         PostsPagesTests.user.username)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_post_detail_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом'''
        response = self.authorized_client.get(self.view_post_detail)

        self.assertEqual(Post.objects.first().image.size, self.uploaded.size)
        self.assertEqual(response.context.get('post'), self.post)

    def test_post_create_show_correct_context(self):
        '''Шаблон post_create сформирован с правильным контекстом'''
        response = self.authorized_client.get(self.view_post_create)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        '''Шаблон post_create, при редактировании,
        сформирован с правильным контекстом'''
        response = self.authorized_client.get(self.view_post_edit)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_to_page(self):
        '''Созданные посты добавляются на страницы'''
        pages = (
            self.view_index,
            self.view_group_list,
            self.view_profile,
        )
        for adress in pages:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.context['page_obj'][0], self.post)

    def test_post_added_to_necessary_group(self):
        '''Посты добавлються только в нужную группу'''
        bad_group = Group.objects.create(
            title='Плохое тестовая группа',
            slug=321,
            description='Тестовое описание',
        )

        response = self.authorized_client.get(reverse('posts:group_list',
                                                      args=[bad_group.slug]))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_guest_user_add_comment_redirect(self):
        '''не зарегистрированному пользователю нельзя оставить комментарий'''
        response = self.guest_client.post(self.view_add_comment)
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F')


class PaginatorViewsTest(TestCase):
    TEST_POSTS_PER_PAGE = 3
    SUMM_TEST_POSTS = settings.POSTS_PER_PAGE + TEST_POSTS_PER_PAGE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=123,
            description='Тестовое описание',
        )

        for post_text in range(cls.SUMM_TEST_POSTS):
            Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'текст номер {post_text}'
            )

        cls.view_index = reverse('posts:index')
        cls.view_group_list = reverse('posts:group_list',
                                      kwargs={'slug': cls.group.slug})
        cls.view_profile = reverse('posts:profile',
                                   kwargs={'username': cls.user.username})

    def test_first_page_contains_ten_records(self):
        '''Первая страница содержит правильное количество страниц'''
        page_paginator = (
            self.view_index,
            self.view_group_list,
            self.view_profile,
        )

        for address in page_paginator:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        '''Вторая страница содержит правильное количество страниц'''
        page_paginator = (
            self.view_index + '?page=2',
            self.view_group_list + '?page=2',
            self.view_profile + '?page=2',
        )

        for address in page_paginator:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.TEST_POSTS_PER_PAGE)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст',
        )
        cls.view_index = reverse('posts:index')

    def test_index_cache(self):
        test_post = Post.objects.create(
            author=self.user,
            text='Другой текст',
        )

        before_caching = self.authorized_client.get(self.view_index)
        after_caching = self.authorized_client.get(self.view_index)
        test_post.save()
        cache.clear()
        after_clear_cache = self.authorized_client.get(self.view_index)

        self.assertEqual(before_caching.content, after_caching.content)
        self.assertNotEqual(before_caching.content, after_clear_cache.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user_following = User.objects.create_user(username='following')
        cls.following_client = Client()
        cls.following_client.force_login(cls.user_following)
        cls.user_follower = User.objects.create_user(username='follower')
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.user_follower)

        cls.view_profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user_follower.username}
        )

        cls.post = Post.objects.create(
            author=cls.user_following,
            text='тестовый текст',
        )

    def test_follow(self):
        '''Проверка вохможности подписки'''
        page_profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username':
                    self.user_following.username})

        self.follower_client.get(page_profile_follow)

        self.assertTrue(Follow.objects.filter(user=self.user_follower,
                                              author=self.user_following))

    def test_unfollow(self):
        '''Проверка вохможности отписаться от автора'''
        page_profile_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username':
                    self.user_following.username})

        self.follower_client.get(page_profile_unfollow)

        self.assertEqual(Follow.objects.all().count(), 0)

    def test_follow_post(self):
        '''Пост появляться в шаблоне follow_index'''
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)

        self.follower_client.get(self.view_profile_follow)
        post_text = Post.objects.first().text

        self.assertEqual(post_text, 'тестовый текст')

    def test_follow_not_post(self):
        '''Пост автора не появиться в follow_index'''
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)

        response = self.following_client.get(self.view_profile_follow)

        self.assertNotEqual(response, 'тестовый текст')
