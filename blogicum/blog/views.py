from django.shortcuts import render, get_object_or_404

from blog.models import Post, Category


def index(request):
    return render(request, 'blog/index.html', {
        'post_list': Post.published().select_related(
            'location',
            'category',
            'author'
        )[0:5]
    })


def post_detail(request, post_id):
    return render(request, 'blog/detail.html', {
        'post': get_object_or_404(Post.published().select_related(
            'location',
            'category',
            'author'
        ), pk=post_id)
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    return render(request, 'blog/category.html', {
        'category': category,
        'post_list': Post.published().select_related(
            'location',
            'category',
            'author'
        ).filter(category__slug=category_slug)
    })
