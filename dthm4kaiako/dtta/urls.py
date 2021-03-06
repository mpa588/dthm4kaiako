"""URL routing for DTTA application."""

from django.urls import path
from . import views

app_name = 'dtta'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('membership/', views.MembershipView.as_view(), name='membership'),
    path('page/<int:pk>/', views.PageDetailView.as_view()),
    path('page/<int:pk>/<slug:slug>/', views.PageDetailView.as_view(), name='page'),
    path('news/', views.NewsArticleListView.as_view(), name='news_article_list'),
    path('news/<int:pk>/', views.NewsArticleDetailView.as_view()),
    path('news/<int:pk>/<slug:slug>/', views.NewsArticleDetailView.as_view(), name='news_article'),
]
