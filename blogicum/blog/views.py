from typing import Any

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model, Q
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, UserUpdateForm
from .models import Category, Comment, Post, User
from .utils import add_comment_count

NUM_POST_PER_PAGE = 10


class IndexListView(ListView):
    model = Post
    paginate_by = NUM_POST_PER_PAGE
    template_name = 'blog/index.html'
    queryset = add_comment_count(
        Post.objects.published().select_related(
            'location', 'category', 'author'
        )
    )


class CategoryListView(ListView):
    model = Post
    paginate_by = NUM_POST_PER_PAGE
    template_name = 'blog/category.html'

    def get_category(self) -> Category:
        return get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )

    def get_queryset(self) -> QuerySet[Any]:
        return add_comment_count(
            self.get_category()
            .posts.published()
            .select_related('location', 'category', 'author')
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return dict(
            **super().get_context_data(**kwargs),
            **{'category': self.get_category()}
        )


class PostFormMixin:
    model = Post
    form_class = PostForm


class PostCheckAuthorMixin(LoginRequiredMixin, PostFormMixin):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)


class PostDetailView(PostFormMixin, DetailView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self) -> Post:
        if self.request.user.is_authenticated:
            query = Q(is_published=True) | Q(author=self.request.user)
        else:
            query = Q(is_published=True)

        post = get_object_or_404(
            Post,
            query,
            pk=self.kwargs['post_id'],
        )
        return post

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return dict(
            **super().get_context_data(**kwargs),
            **{
                'form': CommentForm(),
                'comments': self.object.comments.select_related('author'),
            }
        )


class PostCreateView(PostFormMixin, LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'

    def form_valid(self, form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:profile', args=[self.request.user.username])


class PostUpdateView(PostCheckAuthorMixin, UpdateView):
    def get_success_url(self) -> str:
        return reverse('blog:post_detail', args=[self.object.id])


class PostDeleteView(PostCheckAuthorMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return dict(
            **super().get_context_data(**kwargs),
            **{'form': PostForm(instance=self.object)}
        )


class CommentMixin(LoginRequiredMixin):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])


class CommentUpdDelMixin(CommentMixin):
    template_name = 'blog/comment.html'

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        get_object_or_404(
            Comment, pk=kwargs['comment_id'], author=request.user
        )
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(CommentMixin, CreateView):
    def form_valid(self, form: CommentForm) -> HttpResponse:
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post.objects.published(),
            pk=self.kwargs['post_id'],
        )
        return super().form_valid(form)


class CommentUpdateView(CommentUpdDelMixin, UpdateView):
    pass


class CommentDeleteView(CommentUpdDelMixin, DeleteView):
    pass


class ProfileDetailView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUM_POST_PER_PAGE
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_profile(self) -> User:
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self) -> QuerySet[Any]:
        qs = add_comment_count(
            self.get_profile().posts.select_related(
                'location', 'category', 'author'
            )
        )
        if self.get_profile() != self.request.user:
            return qs.published()
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return dict(
            **super().get_context_data(**kwargs),
            **{'profile': self.get_profile()}
        )


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def get_object(self) -> User:
        return self.request.user

    def get_success_url(self) -> str:
        return reverse('blog:profile', args=[self.request.user.username])
