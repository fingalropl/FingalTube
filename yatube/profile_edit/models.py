from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileEdit(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Пользователь')
    profile_image = models.ImageField('Картинка профиля',
                                      upload_to='profile_image/',
                                      blank=True)
    description = models.TextField('Описание', 
                                help_text='Расскажите немного о себе и вашем контенте')
