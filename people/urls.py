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
    path('organizations/<int:pk>/edit/', views.OrganizationUpdateView.as_view(), name='organization_edit'),
    path('organizations/<int:pk>/delete/', views.OrganizationDeleteView.as_view(), name='organization_delete'),
    
    # 組織関係
    path('organization-relations/', views.OrganizationRelationListView.as_view(), name='organization_relation_list'),
    path('organization-relations/<int:pk>/', views.OrganizationRelationDetailView.as_view(), name='organization_relation_detail'),
    path('organization-relations/create/', views.OrganizationRelationCreateView.as_view(), name='organization_relation_create'),
    path('organization-relations/<int:pk>/edit/', views.OrganizationRelationUpdateView.as_view(), name='organization_relation_edit'),
    path('organization-relations/<int:pk>/delete/', views.OrganizationRelationDeleteView.as_view(), name='organization_relation_delete'),
    path('organization-relations/matrix/', views.organization_relation_matrix_view, name='organization_relation_matrix'),
    
    # 関連図
    path('graph/', views.RelationshipGraphView.as_view(), name='relationship_graph'),
    
    # API（JSON データ）
    path('api/organization-graph/', views.organization_graph_data, name='organization_graph_data'),
    path('api/person-graph/', views.person_graph_data, name='person_graph_data'),
    
    # タグ管理
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/edit/', views.TagUpdateView.as_view(), name='tag_edit'),
    
    # タグ管理 AJAX API
    path('api/tags/create/', views.create_tag_ajax, name='create_tag_ajax'),
    path('api/tags/<int:tag_id>/update/', views.update_tag_ajax, name='update_tag_ajax'),
    path('api/tags/<int:tag_id>/delete/', views.delete_tag_ajax, name='delete_tag_ajax'),
    path('api/tags/<int:tag_id>/details/', views.get_tag_details, name='get_tag_details'),
    
    # 組織関係 AJAX API
    path('api/organization-relations/create/', views.create_organization_relation_ajax, name='create_organization_relation_ajax'),
    path('api/organization-relations/<int:relation_id>/delete/', views.delete_organization_relation_ajax, name='delete_organization_relation_ajax'),
]