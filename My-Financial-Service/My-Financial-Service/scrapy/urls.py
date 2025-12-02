# scrapy/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 루트 접근 시 /pjt05/ 로 이동
    path('', RedirectView.as_view(url='/pjt05/', permanent=False)),

    path('pjt05/admin/', admin.site.urls),

    # ★ 네임스페이스 포함해서 include
    path('pjt05/', include(('contentfetch.urls', 'contentfetch'), namespace='contentfetch')),

    # 로그인/로그아웃
    path('login/',  auth_views.LoginView.as_view(
        template_name='contentfetch/login.html',
        next_page='contentfetch:stock_finder'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='contentfetch:stock_finder'
    ), name='logout'),
]
