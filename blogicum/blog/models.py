from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count

User = get_user_model()


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now(),
        )

    def add_comment_count(self):
        return self.annotate(comment_count=Count('comments')).order_by(
            '-pub_date'
        )


class PublishedModel(models.Model):
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено'
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f'{self.is_published=}|{self.created_at: %Y-%m-%d %H:%M:%S}'


class Location(PublishedModel):
    name = models.CharField(max_length=256, verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return f'{self.name[:20]}|{super().__str__()}'


class Category(PublishedModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        ),
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return (
            f'{self.title[:20]}|{self.slug[:20]}|'
            f'{self.description[:20]}|{super().__str__()}'
        )


class Post(PublishedModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем'
            ' — можно делать отложенные публикации.'
        ),
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )
    image = models.ImageField('Фото', upload_to='posts_images', blank=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'

    def __str__(self):
        return (
            f'{self.title[:20]}|{self.text[:20]}'
            f'|{self.pub_date: %Y-%m-%d %H:%M:%S}|{self.author.username[:20]}'
            f'|{self.location.name[:20]}|{self.category.title[:20]}'
            f'|{super().__str__()}'
        )


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Публикация',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания комментария',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)
        default_related_name = 'comments'

    def __str__(self) -> str:
        return (
            f'{self.text[:20]}|{self.post.title[:20]}'
            f'|{self.created_at: %Y-%m-%d %H:%M:%S}'
            f'|{self.author.username[:20]}'
        )
