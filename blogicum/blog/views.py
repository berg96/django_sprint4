from typing import Any
from django.shortcuts import render, get_object_or_404
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)

from blog.models import Post, Category


class IndexListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/index.html'
    queryset = Post.published().select_related(
        'location', 'category', 'author'
    )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    queryset = Post.published().select_related(
        'location', 'category', 'author'
    )


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    # filter(category__slug=category_slug)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.object.posts.published().select_related(
            'location', 'category', 'author'
        )
        return context
