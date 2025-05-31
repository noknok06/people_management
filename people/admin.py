# people/admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import (
    Person, Organization, Tag, 
    OrganizationRelation, PersonRelation
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_preview', 'person_count', 'org_relation_count']
    list_filter = ['color']
    search_fields = ['name', 'description']
    ordering = ['-created_at']  # 新しい順に表示
    
    def color_preview(self, obj):
        return mark_safe(
            f'<div style="width:20px;height:20px;background-color:{obj.color};'
            f'border:1px solid #ccc;display:inline-block;"></div>'
        )
    color_preview.short_description = '色'
    
    def person_count(self, obj):
        return obj.person_set.count()
    person_count.short_description = '関連人物数'
    
    def org_relation_count(self, obj):
        return obj.organizationrelation_set.count()
    org_relation_count.short_description = '組織関係数'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'level_display', 'parent', 'member_count', 
        'created_at', 'updated_at'
    ]
    list_filter = ['level', 'created_at', 'parent']
    search_fields = ['name', 'description']
    ordering = ['level', 'name']
    list_per_page = 50
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'level', 'parent')
        }),
        ('詳細情報', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    
    def level_display(self, obj):
        level_colors = {
            0: '#dc3545',  # 部門（赤）
            1: '#fd7e14',  # 部（オレンジ）
            2: '#6f42c1',  # 課（紫）
        }
        color = level_colors.get(obj.level, '#6c757d')
        return mark_safe(
            f'<span style="color:{color};font-weight:bold;">'
            f'{obj.get_level_display()}</span>'
        )
    level_display.short_description = '階層レベル'
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'メンバー数'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            member_count=Count('members')
        )


class PersonRelationInline(admin.TabularInline):
    model = PersonRelation
    fk_name = 'from_person'
    extra = 1
    fields = ['to_person', 'relation_type', 'description']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'position', 'organization_display', 'photo_preview',
        'tag_list', 'created_at'
    ]
    list_filter = [
        'organization__level', 'organization', 'position', 
        'tags', 'created_at'
    ]
    search_fields = [
        'name', 'position', 'personality', 'email', 
        'organization__name'
    ]
    ordering = ['organization', 'position', 'name']
    list_per_page = 50
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'photo', 'organization', 'position')
        }),
        ('連絡先', {
            'fields': ('email', 'phone'),
            'classes': ('collapse',)
        }),
        ('詳細情報', {
            'fields': ('personality', 'notes', 'tags'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['tags']
    inlines = [PersonRelationInline]
    
    def organization_display(self, obj):
        return obj.organization.get_full_path()
    organization_display.short_description = '所属組織'
    
    def photo_preview(self, obj):
        if obj.photo:
            return mark_safe(
                f'<img src="{obj.photo.url}" style="width:40px;height:40px;'
                f'object-fit:cover;border-radius:50%;" />'
            )
        return '-'
    photo_preview.short_description = '写真'
    
    def tag_list(self, obj):
        tags = obj.tags.all()[:3]  # 最初の3つのタグのみ表示
        if not tags:
            return '-'
        
        tag_html = []
        for tag in tags:
            tag_html.append(
                f'<span style="background-color:{tag.color};color:white;'
                f'padding:2px 6px;border-radius:3px;font-size:11px;">'
                f'{tag.name}</span>'
            )
        
        more_count = obj.tags.count() - len(tags)
        if more_count > 0:
            tag_html.append(f'<small>+{more_count}</small>')
        
        return mark_safe(' '.join(tag_html))
    tag_list.short_description = 'タグ'


@admin.register(OrganizationRelation)
class OrganizationRelationAdmin(admin.ModelAdmin):
    list_display = [
        'from_organization', 'relation_type_display', 'to_organization',
        'strength_display', 'tag_list', 'created_at'
    ]
    list_filter = [
        'relation_type', 'strength', 'tags', 'created_at',
        'from_organization__level', 'to_organization__level'
    ]
    search_fields = [
        'from_organization__name', 'to_organization__name',
        'description'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('関係情報', {
            'fields': ('from_organization', 'to_organization', 'relation_type')
        }),
        ('詳細設定', {
            'fields': ('strength', 'description', 'tags'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['tags']
    
    def relation_type_display(self, obj):
        colors = {
            'cooperation': '#007bff',
            'reporting': '#28a745',
            'support': '#ffc107',
            'partnership': '#dc3545',
            'dependency': '#6f42c1',
            'communication': '#17a2b8',
        }
        color = colors.get(obj.relation_type, '#6c757d')
        return mark_safe(
            f'<span style="color:{color};font-weight:bold;">'
            f'{obj.get_relation_type_display()}</span>'
        )
    relation_type_display.short_description = '関係の種類'
    
    def strength_display(self, obj):
        stars = '★' * obj.strength + '☆' * (5 - obj.strength)
        return stars
    strength_display.short_description = '関係の強さ'
    
    def tag_list(self, obj):
        tags = obj.tags.all()[:2]
        if not tags:
            return '-'
        
        tag_html = []
        for tag in tags:
            tag_html.append(
                f'<span style="background-color:{tag.color};color:white;'
                f'padding:2px 4px;border-radius:2px;font-size:10px;">'
                f'{tag.name}</span>'
            )
        
        more_count = obj.tags.count() - len(tags)
        if more_count > 0:
            tag_html.append(f'<small>+{more_count}</small>')
        
        return mark_safe(' '.join(tag_html))
    tag_list.short_description = 'タグ'


@admin.register(PersonRelation)
class PersonRelationAdmin(admin.ModelAdmin):
    list_display = [
        'from_person', 'relation_type_display', 'to_person',
        'organizations_display', 'tag_list', 'created_at'
    ]
    list_filter = [
        'relation_type', 'tags', 'created_at',
        'from_person__organization', 'to_person__organization'
    ]
    search_fields = [
        'from_person__name', 'to_person__name',
        'description'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('関係情報', {
            'fields': ('from_person', 'to_person', 'relation_type')
        }),
        ('詳細情報', {
            'fields': ('description', 'tags'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['tags']
    
    def relation_type_display(self, obj):
        colors = {
            'manager': '#28a745',
            'colleague': '#007bff',
            'mentor': '#fd7e14',
            'project_team': '#6f42c1',
            'collaboration': '#17a2b8',
            'communication': '#ffc107',
        }
        color = colors.get(obj.relation_type, '#6c757d')
        return mark_safe(
            f'<span style="color:{color};font-weight:bold;">'
            f'{obj.get_relation_type_display()}</span>'
        )
    relation_type_display.short_description = '関係の種類'
    
    def organizations_display(self, obj):
        from_org = obj.from_person.organization.name
        to_org = obj.to_person.organization.name
        if from_org == to_org:
            return from_org
        return f"{from_org} ⇄ {to_org}"
    organizations_display.short_description = '所属組織'
    
    def tag_list(self, obj):
        tags = obj.tags.all()[:2]
        if not tags:
            return '-'
        
        tag_html = []
        for tag in tags:
            tag_html.append(
                f'<span style="background-color:{tag.color};color:white;'
                f'padding:2px 4px;border-radius:2px;font-size:10px;">'
                f'{tag.name}</span>'
            )
        
        more_count = obj.tags.count() - len(tags)
        if more_count > 0:
            tag_html.append(f'<small>+{more_count}</small>')
        
        return mark_safe(' '.join(tag_html))
    tag_list.short_description = 'タグ'


# 管理画面のサイト設定
admin.site.site_header = '企業人物・組織管理システム'
admin.site.site_title = '管理画面'
admin.site.index_title = 'システム管理'