# people/views.py

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import json

# 既存のインポートに追加
from .models import Person, Organization, Tag, OrganizationRelation, PersonRelation
from .forms import PersonForm, OrganizationForm, PersonSearchForm


class HomeView(ListView):
    """ホームページ - ダッシュボード"""
    template_name = 'people/home.html'
    context_object_name = 'recent_people'
    
    def get_queryset(self):
        return Person.objects.select_related('organization').order_by('-created_at')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_people'] = Person.objects.count()
        context['total_organizations'] = Organization.objects.count()
        context['total_tags'] = Tag.objects.count()
        context['recent_organizations'] = Organization.objects.order_by('-created_at')[:5]
        return context


class PersonListView(ListView):
    """人物一覧・検索ビュー"""
    model = Person
    template_name = 'people/person_list.html'
    context_object_name = 'people'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Person.objects.select_related('organization').prefetch_related('tags')
        
        # 検索機能
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(position__icontains=search_query) |
                Q(organization__name__icontains=search_query) |
                Q(personality__icontains=search_query)
            )
        
        # 組織フィルタ
        org_filter = self.request.GET.get('organization')
        if org_filter:
            queryset = queryset.filter(organization_id=org_filter)
        
        # タグフィルタ
        tag_filter = self.request.GET.get('tag')
        if tag_filter:
            queryset = queryset.filter(tags__id=tag_filter)
        
        return queryset.distinct().order_by('organization__name', 'position', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PersonSearchForm(self.request.GET)
        context['organizations'] = Organization.objects.all()
        context['tags'] = Tag.objects.all()
        context['current_search'] = self.request.GET.get('search', '')
        context['current_org'] = self.request.GET.get('organization', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        return context


class PersonDetailView(DetailView):
    """人物詳細ビュー"""
    model = Person
    template_name = 'people/person_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object
        
        # 関連する人物関係を取得
        context['outgoing_relations'] = PersonRelation.objects.filter(
            from_person=person
        ).select_related('to_person', 'to_person__organization')
        
        context['incoming_relations'] = PersonRelation.objects.filter(
            to_person=person
        ).select_related('from_person', 'from_person__organization')
        
        # 同じ組織のメンバー
        context['colleagues'] = Person.objects.filter(
            organization=person.organization
        ).exclude(id=person.id)[:10]
        
        return context


class PersonCreateView(LoginRequiredMixin, CreateView):
    """人物作成ビュー"""
    model = Person
    form_class = PersonForm
    template_name = 'people/person_form.html'
    success_url = reverse_lazy('person_list')


class PersonUpdateView(LoginRequiredMixin, UpdateView):
    """人物更新ビュー"""
    model = Person
    form_class = PersonForm
    template_name = 'people/person_form.html'


class OrganizationListView(ListView):
    """組織一覧ビュー"""
    model = Organization
    template_name = 'people/organization_list.html'
    context_object_name = 'organizations'
    
    def get_queryset(self):
        return Organization.objects.annotate(
            member_count=Count('members')
        ).order_by('level', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 階層別に組織を整理
        departments = Organization.objects.filter(level=0).annotate(
            member_count=Count('members')
        )
        divisions = Organization.objects.filter(level=1).select_related('parent').annotate(
            member_count=Count('members')
        )
        sections = Organization.objects.filter(level=2).select_related('parent').annotate(
            member_count=Count('members')
        )
        
        context.update({
            'departments': departments,
            'divisions': divisions,
            'sections': sections,
        })
        return context


class OrganizationDetailView(DetailView):
    """組織詳細ビュー"""
    model = Organization
    template_name = 'people/organization_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        
        # 組織のメンバー
        context['members'] = Person.objects.filter(organization=org).order_by('position', 'name')
        
        # 子組織
        context['children'] = Organization.objects.filter(parent=org).annotate(
            member_count=Count('members')
        )
        
        # 組織関係
        context['outgoing_relations'] = OrganizationRelation.objects.filter(
            from_organization=org
        ).select_related('to_organization').prefetch_related('tags')
        
        context['incoming_relations'] = OrganizationRelation.objects.filter(
            to_organization=org
        ).select_related('from_organization').prefetch_related('tags')
        
        return context


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    """組織作成ビュー"""
    model = Organization
    form_class = OrganizationForm
    template_name = 'people/organization_form.html'
    success_url = reverse_lazy('organization_list')


class RelationshipGraphView(ListView):
    """関連図表示ビュー"""
    template_name = 'people/relationship_graph.html'
    
    def get_queryset(self):
        return Organization.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = Tag.objects.all()
        return context


def organization_graph_data(request):
    """組織関連図のJSONデータを提供"""
    try:
        tag_filter = request.GET.get('tag')
        
        # ノード（組織）データ
        organizations = Organization.objects.all()
        nodes = []
        for org in organizations:
            nodes.append({
                'id': str(org.id),  # 文字列に統一
                'name': org.name,
                'level': org.level,
                'member_count': org.members.count(),
                'full_path': org.get_full_path(),
            })
        
        # エッジ（関係）データ
        relations_query = OrganizationRelation.objects.select_related(
            'from_organization', 'to_organization'
        ).prefetch_related('tags')
        
        if tag_filter:
            relations_query = relations_query.filter(tags__id=tag_filter)
        
        edges = []
        for relation in relations_query:
            edges.append({
                'source': str(relation.from_organization.id),  # sourceに変更
                'target': str(relation.to_organization.id),    # targetに変更
                'type': relation.relation_type,
                'strength': relation.strength,
                'description': relation.description,
                'tags': [tag.name for tag in relation.tags.all()],
            })
        
        # データが空の場合はサンプルデータを返す
        if not nodes:
            nodes = [
                {'id': '1', 'name': 'サンプル部門', 'level': 0, 'member_count': 10, 'full_path': 'サンプル部門'},
                {'id': '2', 'name': 'サンプル部', 'level': 1, 'member_count': 5, 'full_path': 'サンプル部門 > サンプル部'},
                {'id': '3', 'name': 'サンプル課', 'level': 2, 'member_count': 3, 'full_path': 'サンプル部門 > サンプル部 > サンプル課'},
            ]
            edges = [
                {'source': '1', 'target': '2', 'type': 'reporting', 'strength': 3, 'description': '報告関係', 'tags': []},
                {'source': '2', 'target': '3', 'type': 'reporting', 'strength': 3, 'description': '報告関係', 'tags': []},
            ]
        
        return JsonResponse({
            'nodes': nodes,
            'edges': edges,
        })
        
    except Exception as e:
        # エラーが発生した場合はサンプルデータを返す
        return JsonResponse({
            'nodes': [
                {'id': '1', 'name': 'サンプル部門', 'level': 0, 'member_count': 10, 'full_path': 'サンプル部門'},
                {'id': '2', 'name': 'サンプル部', 'level': 1, 'member_count': 5, 'full_path': 'サンプル部門 > サンプル部'},
            ],
            'edges': [
                {'source': '1', 'target': '2', 'type': 'reporting', 'strength': 3, 'description': '報告関係', 'tags': []},
            ],
        })


def person_graph_data(request):
    """人物関連図のJSONデータを提供"""
    try:
        org_filter = request.GET.get('organization')
        tag_filter = request.GET.get('tag')
        
        # 人物データ
        people_query = Person.objects.select_related('organization').prefetch_related('tags')
        
        if org_filter:
            people_query = people_query.filter(organization_id=org_filter)
        
        nodes = []
        for person in people_query:
            nodes.append({
                'id': str(person.id),  # 文字列に統一
                'name': person.name,
                'position': person.position,
                'organization': person.organization.name,
                'photo_url': person.photo.url if person.photo else None,
                'tags': [tag.name for tag in person.tags.all()],
            })
        
        # 人物関係データ
        relations_query = PersonRelation.objects.select_related(
            'from_person', 'to_person'
        ).prefetch_related('tags')
        
        if org_filter:
            relations_query = relations_query.filter(
                Q(from_person__organization_id=org_filter) |
                Q(to_person__organization_id=org_filter)
            )
        
        if tag_filter:
            relations_query = relations_query.filter(tags__id=tag_filter)
        
        edges = []
        for relation in relations_query:
            # 両方の人物がノードに含まれている場合のみエッジを追加
            from_id = str(relation.from_person.id)
            to_id = str(relation.to_person.id)
            
            node_ids = [node['id'] for node in nodes]
            if from_id in node_ids and to_id in node_ids:
                edges.append({
                    'source': from_id,  # sourceに変更
                    'target': to_id,    # targetに変更
                    'type': relation.relation_type,
                    'description': relation.description,
                    'tags': [tag.name for tag in relation.tags.all()],
                })
        
        # データが空の場合はサンプルデータを返す
        if not nodes:
            nodes = [
                {'id': '1', 'name': '田中太郎', 'position': '部長', 'organization': 'サンプル部', 'photo_url': None, 'tags': ['管理職']},
                {'id': '2', 'name': '佐藤花子', 'position': '課長', 'organization': 'サンプル部', 'photo_url': None, 'tags': ['営業']},
                {'id': '3', 'name': '鈴木次郎', 'position': '主任', 'organization': 'サンプル部', 'photo_url': None, 'tags': ['技術']},
            ]
            edges = [
                {'source': '1', 'target': '2', 'type': 'manager', 'description': '上司・部下関係', 'tags': []},
                {'source': '2', 'target': '3', 'type': 'manager', 'description': '上司・部下関係', 'tags': []},
                {'source': '1', 'target': '3', 'type': 'communication', 'description': '連絡関係', 'tags': []},
            ]
        
        return JsonResponse({
            'nodes': nodes,
            'edges': edges,
        })
        
    except Exception as e:
        # エラーが発生した場合はサンプルデータを返す
        return JsonResponse({
            'nodes': [
                {'id': '1', 'name': '田中太郎', 'position': '部長', 'organization': 'サンプル部', 'photo_url': None, 'tags': ['管理職']},
                {'id': '2', 'name': '佐藤花子', 'position': '課長', 'organization': 'サンプル部', 'photo_url': None, 'tags': ['営業']},
            ],
            'edges': [
                {'source': '1', 'target': '2', 'type': 'manager', 'description': '上司・部下関係', 'tags': []},
            ],
        })


class TagListView(ListView):
    """タグ一覧ビュー"""
    model = Tag
    template_name = 'people/tag_list.html'
    context_object_name = 'tags'
    
    def get_queryset(self):
        return Tag.objects.annotate(
            person_count=Count('person'),
            org_relation_count=Count('organizationrelation'),
            person_relation_count=Count('personrelation')
        ).order_by('name')


class TagCreateView(LoginRequiredMixin, CreateView):
    """タグ作成ビュー"""
    model = Tag
    fields = ['name', 'color', 'description']
    template_name = 'people/tag_form.html'
    success_url = reverse_lazy('tag_list')


class TagUpdateView(LoginRequiredMixin, UpdateView):
    """タグ更新ビュー"""
    model = Tag
    fields = ['name', 'color', 'description']
    template_name = 'people/tag_form.html'
    success_url = reverse_lazy('tag_list')


@login_required
def create_tag_ajax(request):
    """AJAX タグ作成"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POSTメソッドが必要です'}, status=405)
    
    try:
        # JSONデータを取得
        data = json.loads(request.body)
        
        # データバリデーション
        name = data.get('name', '').strip()
        color = data.get('color', '#007bff')
        description = data.get('description', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'タグ名は必須です'})
        
        # 同名タグの重複チェック
        if Tag.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': 'そのタグ名は既に存在します'})
        
        # タグ作成
        tag = Tag.objects.create(
            name=name,
            color=color,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
                'created_at': tag.created_at.strftime('%Y/%m/%d') if hasattr(tag, 'created_at') else 'N/A'
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '無効なJSONデータです'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'サーバーエラー: {str(e)}'}, status=500)


@login_required
def update_tag_ajax(request, tag_id):
    """AJAX タグ更新"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POSTメソッドが必要です'}, status=405)
    
    try:
        tag = get_object_or_404(Tag, id=tag_id)
        data = json.loads(request.body)
        
        # データ更新
        tag.name = data.get('name', tag.name).strip()
        tag.color = data.get('color', tag.color)
        tag.description = data.get('description', tag.description).strip()
        
        if not tag.name:
            return JsonResponse({'success': False, 'error': 'タグ名は必須です'})
        
        # 同名タグの重複チェック（自分以外）
        if Tag.objects.filter(name=tag.name).exclude(id=tag.id).exists():
            return JsonResponse({'success': False, 'error': 'そのタグ名は既に存在します'})
        
        tag.save()
        
        return JsonResponse({
            'success': True,
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description
            }
        })
        
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'タグが見つかりません'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '無効なJSONデータです'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'サーバーエラー: {str(e)}'}, status=500)


@login_required
def delete_tag_ajax(request, tag_id):
    """AJAX タグ削除"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETEメソッドが必要です'}, status=405)
    
    try:
        tag = get_object_or_404(Tag, id=tag_id)
        
        # 使用中のタグかチェック
        person_count = tag.person_set.count()
        org_relation_count = tag.organizationrelation_set.count()
        person_relation_count = tag.personrelation_set.count()
        
        if person_count > 0 or org_relation_count > 0 or person_relation_count > 0:
            return JsonResponse({
                'success': False, 
                'error': f'このタグは現在使用中です（人物: {person_count}, 組織関係: {org_relation_count}, 人物関係: {person_relation_count}）'
            })
        
        tag.delete()
        
        return JsonResponse({'success': True, 'message': 'タグを削除しました'})
        
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'タグが見つかりません'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'サーバーエラー: {str(e)}'}, status=500)


def get_tag_details(request, tag_id):
    """タグ詳細取得（編集モーダル用）"""
    try:
        tag = get_object_or_404(Tag, id=tag_id)
        
        return JsonResponse({
            'success': True,
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
                'person_count': tag.person_set.count(),
                'org_relation_count': tag.organizationrelation_set.count(),
                'person_relation_count': tag.personrelation_set.count()
            }
        })
        
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'タグが見つかりません'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'サーバーエラー: {str(e)}'}, status=500)


# 既存のTagListViewを更新
class TagListView(ListView):
    """タグ一覧ビュー"""
    model = Tag
    template_name = 'people/tag_list.html'
    context_object_name = 'tags'
    
    def get_queryset(self):
        return Tag.objects.annotate(
            person_count=Count('person'),
            org_relation_count=Count('organizationrelation'),
            person_relation_count=Count('personrelation')
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 今月作成された新しいタグの数を計算
        from django.utils import timezone
        from datetime import datetime
        
        try:
            now = timezone.now()
            first_day_of_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
            
            context['new_tags_this_month'] = Tag.objects.filter(
                created_at__gte=first_day_of_month
            ).count() if hasattr(Tag, 'created_at') else 0
        except:
            context['new_tags_this_month'] = 0
        
        return context

class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    """組織更新ビュー"""
    model = Organization
    form_class = OrganizationForm
    template_name = 'people/organization_form.html'
    
    def get_success_url(self):
        return reverse_lazy('organization_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    """組織削除ビュー"""
    model = Organization
    template_name = 'people/organization_confirm_delete.html'
    success_url = reverse_lazy('organization_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # 子組織があるかチェック
        if self.object.children.exists():
            messages.error(request, 'この組織には子組織が存在するため、削除できません。先に子組織を削除または移動してください。')
            return redirect('organization_detail', pk=self.object.pk)
        
        # メンバーがいるかチェック
        if self.object.members.exists():
            messages.error(request, 'この組織にはメンバーが所属しているため、削除できません。先にメンバーを他の組織に移動してください。')
            return redirect('organization_detail', pk=self.object.pk)
        
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'組織「{self.object.name}」を削除しました。')
        return redirect(success_url)

class OrganizationRelationListView(ListView):
    """組織関係一覧ビュー"""
    model = OrganizationRelation
    template_name = 'people/organization_relation_list.html'
    context_object_name = 'relations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = OrganizationRelation.objects.select_related(
            'from_organization', 'to_organization'
        ).prefetch_related('tags').order_by('-created_at')
        
        # 検索機能
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(from_organization__name__icontains=search_query) |
                Q(to_organization__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # 関係タイプフィルタ
        relation_type = self.request.GET.get('relation_type')
        if relation_type:
            queryset = queryset.filter(relation_type=relation_type)
            
        # 強度フィルタ
        strength = self.request.GET.get('strength')
        if strength:
            queryset = queryset.filter(strength=strength)
            
        # タグフィルタ
        tag_filter = self.request.GET.get('tag')
        if tag_filter:
            queryset = queryset.filter(tags__id=tag_filter)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['relation_types'] = OrganizationRelation.RELATION_TYPES
        context['strength_choices'] = [(i, str(i)) for i in range(1, 6)]
        context['tags'] = Tag.objects.all()
        context['current_search'] = self.request.GET.get('search', '')
        context['current_relation_type'] = self.request.GET.get('relation_type', '')
        context['current_strength'] = self.request.GET.get('strength', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        
        # 統計情報
        context['total_relations'] = OrganizationRelation.objects.count()
        context['relation_type_stats'] = OrganizationRelation.objects.values(
            'relation_type'
        ).annotate(count=Count('id')).order_by('-count')
        
        return context


class OrganizationRelationDetailView(DetailView):
    """組織関係詳細ビュー"""
    model = OrganizationRelation
    template_name = 'people/organization_relation_detail.html'
    context_object_name = 'relation'


class OrganizationRelationCreateView(LoginRequiredMixin, CreateView):
    """組織関係作成ビュー"""
    model = OrganizationRelation
    form_class = OrganizationRelationForm
    template_name = 'people/organization_relation_form.html'
    success_url = reverse_lazy('organization_relation_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = Organization.objects.all().order_by('level', 'name')
        context['tags'] = Tag.objects.all()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, '組織関係を作成しました。')
        return super().form_valid(form)


class OrganizationRelationUpdateView(LoginRequiredMixin, UpdateView):
    """組織関係更新ビュー"""
    model = OrganizationRelation
    form_class = OrganizationRelationForm
    template_name = 'people/organization_relation_form.html'
    
    def get_success_url(self):
        return reverse_lazy('organization_relation_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = Organization.objects.all().order_by('level', 'name')
        context['tags'] = Tag.objects.all()
        context['is_edit'] = True
        return context
    
    def form_valid(self, form):
        messages.success(self.request, '組織関係を更新しました。')
        return super().form_valid(form)


class OrganizationRelationDeleteView(LoginRequiredMixin, DeleteView):
    """組織関係削除ビュー"""
    model = OrganizationRelation
    template_name = 'people/organization_relation_confirm_delete.html'
    success_url = reverse_lazy('organization_relation_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'組織関係「{self.object}」を削除しました。')
        return redirect(success_url)


@login_required
def create_organization_relation_ajax(request):
    """AJAX 組織関係作成"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POSTメソッドが必要です'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        from_org_id = data.get('from_organization')
        to_org_id = data.get('to_organization')
        relation_type = data.get('relation_type')
        description = data.get('description', '').strip()
        strength = data.get('strength', 1)
        
        # バリデーション
        if not from_org_id or not to_org_id:
            return JsonResponse({'success': False, 'error': '組織を選択してください'})
            
        if from_org_id == to_org_id:
            return JsonResponse({'success': False, 'error': '同じ組織同士の関係は作成できません'})
        
        # 組織の存在確認
        try:
            from_org = Organization.objects.get(id=from_org_id)
            to_org = Organization.objects.get(id=to_org_id)
        except Organization.DoesNotExist:
            return JsonResponse({'success': False, 'error': '指定された組織が見つかりません'})
        
        # 重複チェック
        if OrganizationRelation.objects.filter(
            from_organization=from_org,
            to_organization=to_org,
            relation_type=relation_type
        ).exists():
            return JsonResponse({'success': False, 'error': '同じ関係が既に存在します'})
        
        # 関係作成
        relation = OrganizationRelation.objects.create(
            from_organization=from_org,
            to_organization=to_org,
            relation_type=relation_type,
            description=description,
            strength=strength
        )
        
        return JsonResponse({
            'success': True,
            'relation': {
                'id': relation.id,
                'from_organization': relation.from_organization.name,
                'to_organization': relation.to_organization.name,
                'relation_type': relation.get_relation_type_display(),
                'strength': relation.strength,
                'description': relation.description
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '無効なJSONデータです'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'サーバーエラー: {str(e)}'}, status=500)


@login_required
def delete_organization_relation_ajax(request, relation_id):
    """AJAX 組織関係削除"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETEメソッドが必要です'}, status=405)
    
    try:
        relation = get_object_or_404(OrganizationRelation, id=relation_id)
        relation.delete()
        
        return JsonResponse({'success': True, 'message': '組織関係を削除しました'})
        
    except OrganizationRelation.DoesNotExist:
        return JsonResponse({'success': False, 'error': '組織関係が見つかりません'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'サーバーエラー: {str(e)}'}, status=500)


def organization_relation_matrix_view(request):
    """組織関係マトリックス表示"""
    organizations = Organization.objects.all().order_by('level', 'name')
    relations = OrganizationRelation.objects.select_related(
        'from_organization', 'to_organization'
    ).all()
    
    # マトリックス用のデータ構造を作成
    matrix = {}
    for org in organizations:
        matrix[org.id] = {}
        for other_org in organizations:
            matrix[org.id][other_org.id] = []
    
    # 関係をマトリックスに配置
    for relation in relations:
        from_id = relation.from_organization.id
        to_id = relation.to_organization.id
        matrix[from_id][to_id].append(relation)
    
    context = {
        'organizations': organizations,
        'matrix': matrix,
        'relations': relations,
        'relation_types': OrganizationRelation.RELATION_TYPES,
    }
    
    return render(request, 'people/organization_relation_matrix.html', context)        