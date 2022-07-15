from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки.',
        )

    def test_models_have_correct_object_name(self):
        '''модели posts имеют ожидаемые __str__'''
        models_str = {self.post: self.post.text[:15],
                      self.group: self.group.title}

        for model, excepted_values in models_str.items():
            with self.subTest(model=model):
                self.assertEqual(model.__str__(), excepted_values)
