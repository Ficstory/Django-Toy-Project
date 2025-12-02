from django.urls import path
from . import views

app_name = 'contentfetch'

urlpatterns = [
    path('', views.stock_finder,name='stock_finder'),
    path('delete_comment/<int:pk>/', views.delete_comment, name='delete_comment'),
    # 회원가입(F02)
    path('signup/', views.signup, name='signup'),
    # 프로필/관심종목(F05)
    path('profile/', views.profile, name='profile'),
    path('profile/add/', views.add_interest, name='add_interest'),
    path('profile/delete/<int:pk>/', views.delete_interest, name='delete_interest'),
    # 종목 상세(F06) - 관심종목 클릭 시 이동
    path('stocks/<str:stock_name>/', views.stock_detail, name='stock_detail'),
    

]

