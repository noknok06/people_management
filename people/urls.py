# people/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ホーム
    path('', views.HomeView.as_view(), name='home'),
    
    # 人物関連
    path('people/', views.PersonListView.as_view(), name='person_list'),
    path('people/<int:pk>/', views.PersonDetailView.as_view(), name='person_detail'),
    path('people/create/', views.PersonCreateView.as_view(), name='person_create'),
    path('people/<int:pk>/edit/', views.PersonUpdateView.as_view(), name='person_edit'),
    
    # 組織関連
    path('organizations/', views.OrganizationListView.as_view(), name='organization_list'),
    path('organizations/<int:pk>/', views.OrganizationDetailView.as_view(), name='organization_detail'),
    path('organizations/create/', views.OrganizationCreateView.as_view(), name='organization_create'),
    
    # 関連図
    path('graph/', views.RelationshipGraphView.as_view(), name='relationship_graph'),
    
    # API（JSON データ）
    path('api/organization-graph/', views.organization_graph_data, name='organization_graph_data'),
    path('api/person-graph/', views.person_graph_data, name='person_graph_data'),
    
    # タグ
    path('tags/', views.TagListView.as_view(), name='tag_list'),
]

