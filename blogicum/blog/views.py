from typing import Any
from django import http
from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.contrib.auth import get_user_model

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserUpdateForm
from .utils import published, add_comment_count

User = get_user_model()


class IndexMixin:
    model = Post
    paginate_by = 10


class IndexListView(IndexMixin, ListView):
    template_name = 'blog/index.html'
    queryset = add_comment_count(
        Post.published().select_related('location', 'category', 'author')
    )


class CategoryListView(IndexMixin, ListView):
    template_name = 'blog/category.html'
    category = None

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return add_comment_count(
            Post.published()
            .select_related('location', 'category', 'author')
            .filter(category__slug=self.category.slug)
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostMixin:
    model = Post
    form_class = PostForm
    note = None


class PostDetailView(PostMixin, DetailView):
    template_name = 'blog/detail.html'

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        self.note = get_object_or_404(Post, pk=kwargs['pk'])
        if self.note.author != request.user and not self.note.is_published:
            raise Http404("Страница не найдена")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.note.comment.select_related('author')
        return context


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostUpdateView(PostMixin, LoginRequiredMixin, UpdateView):
    template_name = 'blog/create.html'

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        post = get_object_or_404(Post, pk=kwargs['pk'])
        if post.author != request.user:
            return HttpResponseRedirect(
                reverse('blog:post_detail', kwargs={'pk': post.id})
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'pk': self.object.id})


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        # if request.user.is_authenticated:
        self.note = get_object_or_404(
            Post, pk=kwargs['post_id'], author=request.user
        )
        # else:
        #     return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = PostForm(instance=self.note)
        context['form'] = form
        return context


class CommentMixin:
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'


class CommentCreateView(CommentMixin, LoginRequiredMixin, CreateView):
    note = None

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        self.note = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.author = self.request.user
        form.instance.post = self.note
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'pk': self.note.pk})


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    template_name = 'blog/comment.html'

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        if request.user.is_authenticated:
            get_object_or_404(
                Comment, pk=kwargs['comment_id'], author=request.user
            )
        else:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail', kwargs={'pk': self.kwargs['post_id']}
        )


class CommentDeleteView(CommentMixin, LoginRequiredMixin, DeleteView):
    template_name = 'blog/comment.html'

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if request.user.is_authenticated:
            get_object_or_404(
                Comment, pk=kwargs['comment_id'], author=request.user
            )
        else:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail', kwargs={'pk': self.kwargs['post_id']}
        )


class ProfileMixin:
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    profile = None


class ProfileDetailView(ProfileMixin, DetailView):
    template_name = 'blog/profile.html'

    def get_object(self):
        self.profile = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return self.profile

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['profile'] = self.profile
        page_obj = add_comment_count(
            Post.objects.select_related(
                'location', 'category', 'author'
            ).filter(author=self.profile)
        )
        if self.profile != self.request.user:
            page_obj = published(page_obj)
        context['page_obj'] = Paginator(
            page_obj,
            10,
        ).get_page(self.request.GET.get('page'))
        if not page_obj:
            raise Http404("Страница не найдена")
        return context


class ProfileUpdateView(ProfileMixin, LoginRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect('login')
        self.profile = get_object_or_404(User, username=kwargs['username'])
        if self.profile != request.user:
            return redirect(
                'blog:edit_profile_with_name', request.user.username
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:profile', args=(self.request.user.username,))


class EditProfileRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('blog:edit_profile_with_name', request.user.username)
