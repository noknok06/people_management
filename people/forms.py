# people/forms.py
from django import forms
from .models import Person, Organization, Tag, PersonRelation, OrganizationRelation


class PersonForm(forms.ModelForm):
    """人物作成・編集フォーム"""
    
    class Meta:
        model = Person
        fields = [
            'name', 'photo', 'organization', 'position', 
            'personality', 'email', 'phone', 'tags', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '氏名を入力してください'
            }),
            'organization': forms.Select(attrs={
                'class': 'form-control'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '役職を入力してください'
            }),
            'personality': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '性格や特徴を入力してください'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'メールアドレスを入力してください'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '電話番号を入力してください'
            }),
            'tags': forms.CheckboxSelectMultiple(),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考を入力してください'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            })
        }


class OrganizationForm(forms.ModelForm):
    """組織作成・編集フォーム"""
    
    class Meta:
        model = Organization
        fields = ['name', 'level', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '組織名を入力してください'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '組織の説明を入力してください'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 親組織の選択肢を階層に応じて制限
        if 'level' in self.data:
            level = int(self.data.get('level', 0))
            if level > 0:
                self.fields['parent'].queryset = Organization.objects.filter(level=level-1)
            else:
                self.fields['parent'].queryset = Organization.objects.none()
        elif self.instance.pk and self.instance.level > 0:
            self.fields['parent'].queryset = Organization.objects.filter(
                level=self.instance.level-1
            )


class PersonSearchForm(forms.Form):
    """人物検索フォーム"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '名前、役職、組織名、性格で検索...'
        })
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        empty_label="すべての組織",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="すべてのタグ",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class PersonRelationForm(forms.ModelForm):
    """人物関係作成・編集フォーム"""
    
    class Meta:
        model = PersonRelation
        fields = ['from_person', 'to_person', 'relation_type', 'description', 'tags']
        widgets = {
            'from_person': forms.Select(attrs={'class': 'form-control'}),
            'to_person': forms.Select(attrs={'class': 'form-control'}),
            'relation_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '関係の詳細を入力してください'
            }),
            'tags': forms.CheckboxSelectMultiple()
        }


class OrganizationRelationForm(forms.ModelForm):
    """組織関係作成・編集フォーム"""
    
    class Meta:
        model = OrganizationRelation
        fields = [
            'from_organization', 'to_organization', 'relation_type', 
            'description', 'tags', 'strength'
        ]
        widgets = {
            'from_organization': forms.Select(attrs={'class': 'form-control'}),
            'to_organization': forms.Select(attrs={'class': 'form-control'}),
            'relation_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '関係の詳細を入力してください'
            }),
            'tags': forms.CheckboxSelectMultiple(),
            'strength': forms.Select(attrs={'class': 'form-control'})
        }


class TagForm(forms.ModelForm):
    """タグ作成・編集フォーム"""
    
    class Meta:
        model = Tag
        fields = ['name', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'タグ名を入力してください'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'タグの説明を入力してください'
            })
        }


class BulkImportForm(forms.Form):
    """一括インポートフォーム"""
    csv_file = forms.FileField(
        label="CSVファイル",
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.csv'
        }),
        help_text="CSV形式のファイルをアップロードしてください"
    )
    import_type = forms.ChoiceField(
        label="インポート種類",
        choices=[
            ('person', '人物データ'),
            ('organization', '組織データ'),
            ('person_relation', '人物関係データ'),
            ('organization_relation', '組織関係データ'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    update_existing = forms.BooleanField(
        label="既存データを更新する",
        required=False,
        help_text="チェックすると、既存のデータも更新されます"
    )