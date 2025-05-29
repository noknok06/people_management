# people_management/management/commands/setup_sample_data.py
from django.core.management.base import BaseCommand
from django.db import transaction
from people_management.models import Organization, Person, Tag, OrganizationRelation, PersonRelation
import random


class Command(BaseCommand):
    help = 'サンプルデータを作成します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='既存データを削除してから作成',
        )
        parser.add_argument(
            '--organizations',
            type=int,
            default=10,
            help='作成する組織数（デフォルト: 10）',
        )
        parser.add_argument(
            '--people',
            type=int,
            default=50,
            help='作成する人物数（デフォルト: 50）',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('既存データを削除中...')
            Person.objects.all().delete()
            Organization.objects.all().delete()
            Tag.objects.all().delete()
            OrganizationRelation.objects.all().delete()
            PersonRelation.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('既存データを削除しました。'))

        with transaction.atomic():
            self.create_tags()
            self.create_organizations(options['organizations'])
            self.create_people(options['people'])
            self.create_organization_relations()
            self.create_person_relations()

        self.stdout.write(
            self.style.SUCCESS(
                f'サンプルデータの作成が完了しました。\n'
                f'- 組織: {Organization.objects.count()}個\n'
                f'- 人物: {Person.objects.count()}人\n'
                f'- タグ: {Tag.objects.count()}個\n'
                f'- 組織関係: {OrganizationRelation.objects.count()}個\n'
                f'- 人物関係: {PersonRelation.objects.count()}個'
            )
        )

    def create_tags(self):
        """タグを作成"""
        tags_data = [
            {'name': '営業', 'color': '#007bff', 'description': '営業関連業務'},
            {'name': '技術', 'color': '#28a745', 'description': '技術開発関連'},
            {'name': '管理職', 'color': '#dc3545', 'description': '管理職・リーダー'},
            {'name': 'プロジェクト', 'color': '#ffc107', 'description': 'プロジェクト関連'},
            {'name': '新人', 'color': '#17a2b8', 'description': '新入社員・若手'},
            {'name': 'ベテラン', 'color': '#6f42c1', 'description': 'ベテラン・経験豊富'},
            {'name': '企画', 'color': '#fd7e14', 'description': '企画・戦略関連'},
            {'name': '人事', 'color': '#20c997', 'description': '人事関連業務'},
            {'name': '財務', 'color': '#e83e8c', 'description': '財務・経理関連'},
            {'name': 'マーケティング', 'color': '#6c757d', 'description': 'マーケティング関連'},
        ]

        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'color': tag_data['color'],
                    'description': tag_data['description']
                }
            )
            if created:
                self.stdout.write(f'タグを作成: {tag.name}')

    def create_organizations(self, count):
        """組織を作成"""
        # 部門（レベル0）
        departments = [
            {'name': '経営企画部門', 'description': '経営戦略の企画・立案を行う部門'},
            {'name': '営業部門', 'description': '売上拡大と顧客開拓を担当する部門'},
            {'name': '技術部門', 'description': 'システム開発・技術革新を推進する部門'},
            {'name': '管理部門', 'description': '人事・総務・経理を担当する部門'},
        ]

        created_departments = []
        for dept_data in departments:
            dept, created = Organization.objects.get_or_create(
                name=dept_data['name'],
                level=0,
                defaults={'description': dept_data['description']}
            )
            created_departments.append(dept)
            if created:
                self.stdout.write(f'部門を作成: {dept.name}')

        # 部（レベル1）
        divisions_data = [
            # 経営企画部門の下
            {'name': '経営戦略部', 'parent': created_departments[0], 'description': '中長期経営戦略の策定'},
            {'name': '事業企画部', 'parent': created_departments[0], 'description': '新規事業の企画・推進'},
            # 営業部門の下
            {'name': '法人営業部', 'parent': created_departments[1], 'description': '法人顧客への営業活動'},
            {'name': '個人営業部', 'parent': created_departments[1], 'description': '個人顧客への営業活動'},
            # 技術部門の下
            {'name': '開発部', 'parent': created_departments[2], 'description': 'システム・製品開発'},
            {'name': 'インフラ部', 'parent': created_departments[2], 'description': 'ITインフラの構築・運用'},
            # 管理部門の下
            {'name': '人事部', 'parent': created_departments[3], 'description': '人事制度・採用・教育'},
            {'name': '総務部', 'parent': created_departments[3], 'description': '総務・法務・広報'},
        ]

        created_divisions = []
        for div_data in divisions_data:
            div, created = Organization.objects.get_or_create(
                name=div_data['name'],
                level=1,
                parent=div_data['parent'],
                defaults={'description': div_data['description']}
            )
            created_divisions.append(div)
            if created:
                self.stdout.write(f'部を作成: {div.name}')

        # 課（レベル2）
        sections_data = [
            # 経営戦略部の下
            {'name': '戦略企画課', 'parent': created_divisions[0]},
            {'name': '経営分析課', 'parent': created_divisions[0]},
            # 事業企画部の下
            {'name': '新規事業課', 'parent': created_divisions[1]},
            # 法人営業部の下
            {'name': '大手法人課', 'parent': created_divisions[2]},
            {'name': '中小法人課', 'parent': created_divisions[2]},
            # 個人営業部の下
            {'name': '営業推進課', 'parent': created_divisions[3]},
            # 開発部の下
            {'name': 'システム開発課', 'parent': created_divisions[4]},
            {'name': '品質管理課', 'parent': created_divisions[4]},
            # インフラ部の下
            {'name': 'ネットワーク課', 'parent': created_divisions[5]},
            # 人事部の下
            {'name': '採用課', 'parent': created_divisions[6]},
            {'name': '人事企画課', 'parent': created_divisions[6]},
            # 総務部の下
            {'name': '総務課', 'parent': created_divisions[7]},
            {'name': '法務課', 'parent': created_divisions[7]},
        ]

        for sec_data in sections_data:
            sec, created = Organization.objects.get_or_create(
                name=sec_data['name'],
                level=2,
                parent=sec_data['parent'],
                defaults={'description': f'{sec_data["name"]}の業務を担当'}
            )
            if created:
                self.stdout.write(f'課を作成: {sec.name}')

    def create_people(self, count):
        """人物を作成"""
        organizations = list(Organization.objects.all())
        tags = list(Tag.objects.all())
        
        # サンプル人名
        first_names = [
            '太郎', '花子', '次郎', '美咲', '三郎', '由美', '四郎', '真理',
            '五郎', '恵子', '健一', '智子', '浩二', '京子', '雅彦', '裕子',
            '和夫', '明美', '正義', '千代子', '博', '洋子', '隆', '幸子',
            '誠', '節子', '清', '悦子', '勝', '文子', '豊', '光子'
        ]
        
        last_names = [
            '田中', '佐藤', '鈴木', '高橋', '渡辺', '伊藤', '山本', '中村',
            '小林', '加藤', '吉田', '山田', '佐々木', '山口', '松本', '井上',
            '木村', '林', '清水', '山崎', '森', '池田', '橋本', '阿部',
            '石川', '斎藤', '前田', '藤田', '小川', '後藤', '岡田', '長谷川'
        ]
        
        positions = [
            '部長', '課長', '主任', '係長', '主査', '主事', '一般職',
            '課長代理', '部長代理', '担当課長', '専門職', '主任研究員',
            'シニアマネージャー', 'マネージャー', 'チームリーダー',
            'エキスパート', 'スペシャリスト', 'アシスタント'
        ]

        personalities = [
            '明るく積極的な性格で、チームワークを大切にします。',
            '冷静で分析力に優れ、論理的思考が得意です。',
            '責任感が強く、リーダーシップを発揮します。',
            '創造性豊かで、新しいアイデアを提案することが多いです。',
            '協調性があり、周囲との関係を大切にします。',
            '几帳面で細かい作業が得意です。',
            'コミュニケーション能力が高く、営業に向いています。',
            '技術的な知識が豊富で、問題解決能力に優れています。',
            '経験豊富で、若手の指導に熱心です。',
            '新しい技術への興味が強く、常に学習を続けています。'
        ]

        for i in range(count):
            name = f"{random.choice(last_names)} {random.choice(first_names)}"
            organization = random.choice(organizations)
            position = random.choice(positions)
            personality = random.choice(personalities)
            
            person, created = Person.objects.get_or_create(
                name=name,
                organization=organization,
                defaults={
                    'position': position,
                    'personality': personality,
                    'email': f"{name.replace(' ', '').lower()}@company.example.com",
                    'phone': f"03-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                }
            )
            
            if created:
                # ランダムにタグを割り当て
                selected_tags = random.sample(tags, random.randint(1, 3))
                person.tags.set(selected_tags)
                self.stdout.write(f'人物を作成: {person.name} ({organization.name})')

    def create_organization_relations(self):
        """組織関係を作成"""
        organizations = list(Organization.objects.all())
        relation_types = ['cooperation', 'reporting', 'support', 'partnership', 'communication']
        
        # ランダムに組織関係を作成
        for _ in range(min(15, len(organizations) // 2)):
            from_org, to_org = random.sample(organizations, 2)
            relation_type = random.choice(relation_types)
            
            relation, created = OrganizationRelation.objects.get_or_create(
                from_organization=from_org,
                to_organization=to_org,
                relation_type=relation_type,
                defaults={
                    'description': f'{from_org.name}と{to_org.name}の{relation.get_relation_type_display()}',
                    'strength': random.randint(1, 5)
                }
            )
            
            if created:
                self.stdout.write(f'組織関係を作成: {from_org.name} → {to_org.name}')

    def create_person_relations(self):
        """人物関係を作成"""
        people = list(Person.objects.all())
        relation_types = ['manager', 'colleague', 'mentor', 'project_team', 'collaboration']
        
        # ランダムに人物関係を作成
        for _ in range(min(30, len(people) // 3)):
            from_person, to_person = random.sample(people, 2)
            relation_type = random.choice(relation_types)
            
            relation, created = PersonRelation.objects.get_or_create(
                from_person=from_person,
                to_person=to_person,
                relation_type=relation_type,
                defaults={
                    'description': f'{from_person.name}と{to_person.name}の{relation.get_relation_type_display()}'
                }
            )
            
            if created:
                self.stdout.write(f'人物関係を作成: {from_person.name} → {to_person.name}')


# people_management/management/commands/export_data.py
from django.core.management.base import BaseCommand
from django.http import HttpResponse
import csv
import json
from people_management.models import Organization, Person, Tag, OrganizationRelation, PersonRelation


class Command(BaseCommand):
    help = 'データをエクスポートします'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['csv', 'json'],
            default='csv',
            help='エクスポート形式（csv または json）',
        )
        parser.add_argument(
            '--model',
            choices=['person', 'organization', 'all'],
            default='all',
            help='エクスポートするモデル',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='出力ファイル名（指定しない場合は標準出力）',
        )

    def handle(self, *args, **options):
        format_type = options['format']
        model_type = options['model']
        output_file = options['output']

        if format_type == 'csv':
            self.export_csv(model_type, output_file)
        else:
            self.export_json(model_type, output_file)

    def export_csv(self, model_type, output_file):
        """CSV形式でエクスポート"""
        if model_type == 'person' or model_type == 'all':
            self.export_people_csv(output_file)
        
        if model_type == 'organization' or model_type == 'all':
            self.export_organizations_csv(output_file)

    def export_people_csv(self, output_file):
        """人物データをCSVエクスポート"""
        filename = output_file or 'people_export.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                '氏名', '役職', '所属組織', '組織パス', 'メールアドレス', 
                '電話番号', '性格', '備考', 'タグ', '作成日時', '更新日時'
            ])
            
            for person in Person.objects.select_related('organization').prefetch_related('tags'):
                tags = ', '.join([tag.name for tag in person.tags.all()])
                writer.writerow([
                    person.name,
                    person.position,
                    person.organization.name,
                    person.organization.get_full_path(),
                    person.email,
                    person.phone,
                    person.personality,
                    person.notes,
                    tags,
                    person.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    person.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                ])
        
        self.stdout.write(
            self.style.SUCCESS(f'人物データを {filename} にエクスポートしました。')
        )

    def export_organizations_csv(self, output_file):
        """組織データをCSVエクスポート"""
        filename = output_file or 'organizations_export.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                '組織名', '階層レベル', '親組織', '組織パス', '説明', 
                'メンバー数', '作成日時', '更新日時'
            ])
            
            for org in Organization.objects.select_related('parent').annotate(
                member_count=models.Count('members')
            ):
                writer.writerow([
                    org.name,
                    org.get_level_display(),
                    org.parent.name if org.parent else '',
                    org.get_full_path(),
                    org.description,
                    org.member_count,
                    org.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    org.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                ])
        
        self.stdout.write(
            self.style.SUCCESS(f'組織データを {filename} にエクスポートしました。')
        )

    def export_json(self, model_type, output_file):
        """JSON形式でエクスポート"""
        data = {}
        
        if model_type == 'person' or model_type == 'all':
            data['people'] = self.get_people_data()
        
        if model_type == 'organization' or model_type == 'all':
            data['organizations'] = self.get_organizations_data()
        
        if model_type == 'all':
            data['tags'] = self.get_tags_data()
            data['organization_relations'] = self.get_organization_relations_data()
            data['person_relations'] = self.get_person_relations_data()
        
        filename = output_file or 'export_data.json'
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'データを {filename} にエクスポートしました。')
        )

    def get_people_data(self):
        """人物データを取得"""
        people = []
        for person in Person.objects.select_related('organization').prefetch_related('tags'):
            people.append({
                'id': person.id,
                'name': person.name,
                'position': person.position,
                'organization': person.organization.name,
                'organization_path': person.organization.get_full_path(),
                'email': person.email,
                'phone': person.phone,
                'personality': person.personality,
                'notes': person.notes,
                'tags': [tag.name for tag in person.tags.all()],
                'created_at': person.created_at,
                'updated_at': person.updated_at,
            })
        return people

    def get_organizations_data(self):
        """組織データを取得"""
        organizations = []
        for org in Organization.objects.select_related('parent'):
            organizations.append({
                'id': org.id,
                'name': org.name,
                'level': org.level,
                'level_display': org.get_level_display(),
                'parent': org.parent.name if org.parent else None,
                'path': org.get_full_path(),
                'description': org.description,
                'member_count': org.members.count(),
                'created_at': org.created_at,
                'updated_at': org.updated_at,
            })
        return organizations

    def get_tags_data(self):
        """タグデータを取得"""
        tags = []
        for tag in Tag.objects.all():
            tags.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
            })
        return tags

    def get_organization_relations_data(self):
        """組織関係データを取得"""
        relations = []
        for rel in OrganizationRelation.objects.select_related(
            'from_organization', 'to_organization'
        ).prefetch_related('tags'):
            relations.append({
                'from_organization': rel.from_organization.name,
                'to_organization': rel.to_organization.name,
                'relation_type': rel.get_relation_type_display(),
                'description': rel.description,
                'strength': rel.strength,
                'tags': [tag.name for tag in rel.tags.all()],
                'created_at': rel.created_at,
            })
        return relations

    def get_person_relations_data(self):
        """人物関係データを取得"""
        relations = []
        for rel in PersonRelation.objects.select_related(
            'from_person', 'to_person'
        ).prefetch_related('tags'):
            relations.append({
                'from_person': rel.from_person.name,
                'to_person': rel.to_person.name,
                'relation_type': rel.get_relation_type_display(),
                'description': rel.description,
                'tags': [tag.name for tag in rel.tags.all()],
                'created_at': rel.created_at,
            })
        return relations