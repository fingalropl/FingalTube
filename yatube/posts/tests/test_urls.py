from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
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

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=123,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
        )

        cls.url_index = '/'
        cls.url_group = f'/group/{PostsURLTests.group.slug}/'
        cls.url_profile = f'/profile/{PostsURLTests.user.username}/'
        cls.url_post_detail = '/posts/1/'
        cls.url_post_create = '/create/'
        cls.url_post_edit = '/posts/1/edit/'

    def test_url_at_desired_location(self):
        '''url адреса доступны'''
        public_url = {
            self.url_index: HTTPStatus.OK,
            self.url_group: HTTPStatus.OK,
            self.url_profile: HTTPStatus.OK,
            self.url_post_detail: HTTPStatus.OK,
            self.url_post_create: HTTPStatus.FOUND,
            self.url_post_edit: HTTPStatus.FOUND,
        }

        for url, status_code in public_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_templates_for_guest(self):
        '''URL-adress использует ожидаемые шаблоны
        для незарегестривованных пользователей'''
        templates_url = {
            self.url_index: 'posts/index.html',
            self.url_group: 'posts/group_list.html',
            self.url_profile: 'posts/profile.html',
            self.url_post_detail: 'posts/post_detail.html',
        }

        for address, template in templates_url.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_template_for_authorized(self):
        '''URL-adress использует ожидаемые шаблоны
         для зарегестрированных пользователей'''
        response = self.not_author.get(self.url_post_create)

        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_template_for_author(self):
        '''URL-adress использует ожидаемые шаблоны для авторов поста'''
        response = self.authorized_client.get(self.url_post_edit)

        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_un_existing_page(self):
        '''Ошибка 404 на несуществующую страницу'''
        response = self.guest_client.get('/unexistint_page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_client_redirect(self):
        '''Перенаправление анонимного пользователя
        с создания и изменения поста'''
        url_page = {
            self.url_post_create: '/auth/login/?next=/create/',
            self.url_post_edit: '/auth/login/?next=/posts/1/edit/',
        }

        for adress, redict in url_page.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertRedirects(response, redict)

    def test_not_author_post_edit_redirect(self):
        '''Перенаправление не автора при редактировании поста'''
        page_post_edit = reverse('posts:post_detail', args=(self.post.id,))

        response = self.not_author.get(self.url_post_edit)

        self.assertRedirects(response, page_post_edit)
