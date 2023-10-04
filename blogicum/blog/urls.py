from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.IndexListView.as_view(), name='index'),
    path(
        'posts/<int:pk>/',
        views.PostDetailView.as_view(),
        name='post_detail',
    ),
    path('post/create/', views.PostCreateView.as_view(), name='create_post'),
    path(
        'category/<slug:slug>/',
        views.CategoryListView.as_view(),
        name='category_posts',
    ),
    path(
        'profile/<slug:username>/',
        views.ProfileDetailView.as_view(),
        name='profile',
    ),
]
