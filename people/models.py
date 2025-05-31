# people/models.py
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Tag(models.Model):
    """タグモデル - フィルタリング用"""
    name = models.CharField(max_length=50, unique=True, verbose_name="タグ名")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="色")
    description = models.TextField(blank=True, verbose_name="説明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "タグ"
        verbose_name_plural = "タグ"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tag_list')


# 残りのモデルは既存のまま
class Organization(models.Model):
    """組織モデル - 3階層構造（部門→部→課）"""
    LEVEL_CHOICES = [
        (0, '部門'),
        (1, '部'),
        (2, '課'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="組織名")
    level = models.IntegerField(choices=LEVEL_CHOICES, verbose_name="階層レベル")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name="親組織"
    )
    description = models.TextField(blank=True, verbose_name="説明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "組織"
        verbose_name_plural = "組織"
        ordering = ['level', 'name']
    
    def __str__(self):
        level_name = dict(self.LEVEL_CHOICES)[self.level]
        if self.parent:
            return f"{self.parent.name} > {self.name} ({level_name})"
        return f"{self.name} ({level_name})"
    
    def get_absolute_url(self):
        return reverse('organization_detail', kwargs={'pk': self.pk})
    
    def get_full_path(self):
        """組織の完全パスを取得"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " > ".join(path)


class Person(models.Model):
    """人物モデル - 従業員情報"""
    name = models.CharField(max_length=100, verbose_name="氏名")
    photo = models.ImageField(
        upload_to='photos/', 
        blank=True, 
        null=True, 
        verbose_name="顔写真"
    )
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='members',
        verbose_name="所属組織"
    )
    position = models.CharField(max_length=100, verbose_name="役職")
    personality = models.TextField(blank=True, verbose_name="性格・特徴")
    email = models.EmailField(blank=True, verbose_name="メールアドレス")
    phone = models.CharField(max_length=20, blank=True, verbose_name="電話番号")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="タグ")
    notes = models.TextField(blank=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "人物"
        verbose_name_plural = "人物"
        ordering = ['organization', 'position', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    def get_absolute_url(self):
        return reverse('person_detail', kwargs={'pk': self.pk})


class OrganizationRelation(models.Model):
    """組織関係モデル - 組織間の連携関係"""
    RELATION_TYPES = [
        ('cooperation', '協力関係'),
        ('reporting', '報告関係'),
        ('support', 'サポート関係'),
        ('partnership', 'パートナー関係'),
        ('dependency', '依存関係'),
        ('communication', '連絡関係'),
        ('other', 'その他'),
    ]
    
    from_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='outgoing_relations',
        verbose_name="関係元組織"
    )
    to_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='incoming_relations',
        verbose_name="関係先組織"
    )
    relation_type = models.CharField(
        max_length=20, 
        choices=RELATION_TYPES, 
        default='cooperation',
        verbose_name="関係の種類"
    )
    description = models.TextField(blank=True, verbose_name="関係の詳細")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="関連タグ")
    strength = models.IntegerField(
        default=1, 
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="関係の強さ"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "組織関係"
        verbose_name_plural = "組織関係"
        unique_together = ['from_organization', 'to_organization', 'relation_type']
    
    def __str__(self):
        relation_name = dict(self.RELATION_TYPES)[self.relation_type]
        return f"{self.from_organization.name} → {self.to_organization.name} ({relation_name})"


class PersonRelation(models.Model):
    """人物関係モデル - 人物間の関係"""
    RELATION_TYPES = [
        ('manager', '上司・部下'),
        ('colleague', '同僚'),
        ('mentor', 'メンター・メンティー'),
        ('project_team', 'プロジェクトチーム'),
        ('collaboration', '協力関係'),
        ('communication', '頻繁な連絡'),
        ('other', 'その他'),
    ]
    
    from_person = models.ForeignKey(
        Person, 
        on_delete=models.CASCADE, 
        related_name='outgoing_person_relations',
        verbose_name="関係元人物"
    )
    to_person = models.ForeignKey(
        Person, 
        on_delete=models.CASCADE, 
        related_name='incoming_person_relations',
        verbose_name="関係先人物"
    )
    relation_type = models.CharField(
        max_length=20, 
        choices=RELATION_TYPES, 
        default='colleague',
        verbose_name="関係の種類"
    )
    description = models.TextField(blank=True, verbose_name="関係の詳細")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="関連タグ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    
    class Meta:
        verbose_name = "人物関係"
        verbose_name_plural = "人物関係"
        unique_together = ['from_person', 'to_person', 'relation_type']
    
    def __str__(self):
        relation_name = dict(self.RELATION_TYPES)[self.relation_type]
        return f"{self.from_person.name} → {self.to_person.name} ({relation_name})"