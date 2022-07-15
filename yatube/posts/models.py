from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, unique=True, verbose_name='Имя')
    slug = models.SlugField(unique=True, verbose_name='Адрес')
    description = models.TextField(verbose_name='Сообщество')

    def __str__(self):
        return self.title


class Post(models.Model):

    title = models.TextField(max_length=20,
                             verbose_name='Оглавление ващей записи', blank=True, 
                             help_text='Придумайте краткое описание вашего поста')

    text = models.TextField(verbose_name='Текст',
                            help_text='Здесь напишите текст вашей записи ')
    
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts', verbose_name='Автор')
    group = models.ForeignKey('Group', related_name='posts',
                              on_delete=models.SET_NULL,
                              blank=True, null=True,
                              verbose_name='Сообщество',
                              help_text='Укажите группу в которой'
                              'вы желаете разместить запись.')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    like = models.IntegerField('Like', blank=True)


    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments',
                             on_delete=models.CASCADE,
                             verbose_name='комментируемая запись',)
    author = models.ForeignKey(User, related_name='comments',
                               on_delete=models.CASCADE,
                               verbose_name='Автор еомментария',)
    text = models.TextField(verbose_name='Текст комментария')
    created = models.DateTimeField(verbose_name='Время и дата комментария',
                                   auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='following',
                               on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['author', 'user'],
                                               name='unique_follow')]
