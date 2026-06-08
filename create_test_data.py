"""创建测试数据脚本"""
# -*- coding: utf-8 -*-
import sys
import io
import uuid
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('.')

from app.database import SessionLocal, init_db
from app.models.audit import Item, Material
from app.models.document import Template
from datetime import datetime
import os
import json

def create_items():
    """创建526条标准项测试数据"""
    db = SessionLocal()

    try:
        # 检查是否已有数据
        existing_count = db.query(Item).count()
        if existing_count > 0:
            print(f'标准项表已有 {existing_count} 条数据，跳过创建')
            return

        print('开始创建526条标准项...')

        # 标准项章节分布
        sections = ['安全计算环境', '安全通信网络', '安全区域边界', '安全管理中心', '安全管理制度', '安全管理机构', '人员安全管理', '系统建设管理', '系统运维管理']

        # 标准项类型
        item_types = ['技术要求', '管理要求', None]

        # 生成526条标准项
        for i in range(1, 527):
            section = sections[i % len(sections)]
            item_type = item_types[i % len(item_types)]

            # 生成标准项要求
            requirement = f'应{["建立", "制定", "实施", "采用", "部署", "配置", "启用", "设置"][i % 8]}{["安全", "访问", "身份", "数据", "网络", "系统", "应用", "审计"][i % 8]}{["控制机制", "保护措施", "鉴别机制", "加密措施", "隔离策略", "防护策略", "认证机制", "监控机制"][i % 8]}'

            item = Item(
                id=str(i).zfill(4),
                requirement=requirement,
                section=section,
                item_type=item_type,
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(item)

            if i % 50 == 0:
                print(f'  已创建 {i} 条标准项...')

        db.commit()
        print(f'[OK] 成功创建 526 条标准项')

    except Exception as e:
        db.rollback()
        print(f'[ERROR] 创建标准项失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def create_templates():
    """创建02-06文档模板"""
    db = SessionLocal()

    try:
        # 检查是否已有模板
        existing_templates = db.query(Template).filter(
            Template.document_type.like('申报书-%')
        ).all()

        if len(existing_templates) >= 6:
            print(f'已存在 {len(existing_templates)} 个申报书模板，跳过创建')
            return

        print('开始创建02-06文档模板...')

        # 创建02-06文档模板
        for cat in ['02', '03', '04', '05', '06']:
            # 检查是否已存在
            existing = db.query(Template).filter(
                Template.document_type == f'申报书-{cat}'
            ).first()

            if existing:
                print(f'  申报书-{cat} 已存在，跳过')
                continue

            template = Template(
                name=f'0{cat}文档模板',
                document_type=f'申报书-{cat}',
                file_path=f'/templates/declaration_0{cat}.docx',
                status='active',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(template)
            print(f'  [OK] 创建申报书-{cat}模板')

        db.commit()
        print('[OK] 成功创建02-06文档模板')

    except Exception as e:
        db.rollback()
        print(f'[ERROR] 创建文档模板失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def create_evidence_list():
    """创建证据清单测试数据"""
    from config import UPLOAD_DIR

    evidence_list_path = os.path.join(UPLOAD_DIR, "evidence", "evidence_list.json")

    # 检查是否已存在
    if os.path.exists(evidence_list_path):
        try:
            with open(evidence_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if len(data.get('items', [])) > 0:
                    print(f'证据清单已存在 {len(data["items"])} 条数据，跳过创建')
                    return
        except:
            pass

    print('开始创建证据清单测试数据...')

    # 创建证据清单目录
    os.makedirs(os.path.dirname(evidence_list_path), exist_ok=True)

    # 生成证据清单数据
    items = []
    evidence_types = ['身份认证', '访问控制', '安全审计', '数据完整性', '数据保密性', '产品采购', '自主可控', '密码应用']

    for i in range(1, 51):  # 创建50条举证材料
        item = {
            "id": str(uuid.uuid4()),
            "序号": i,
            "章节名称": evidence_types[i % len(evidence_types)],
            "举证名称": f'{i:02d}-{evidence_types[i % len(evidence_types)]}证明材料',
            "样例举证": f'{i:02d}-{evidence_types[i % len(evidence_types)]}.png',
            "局点上传举证材料": None,
            "审核结果": "待审核",
            "样例举证文件": None,
            "局点上传文件": None,
            "举证诊断结果": None,
        }
        items.append(item)

    evidence_data = {
        "file_path": evidence_list_path,
        "items": items,
        "updated_at": datetime.now().isoformat()
    }

    # 保存证据清单
    with open(evidence_list_path, 'w', encoding='utf-8') as f:
        json.dump(evidence_data, f, ensure_ascii=False, indent=2)

    print(f'[OK] 成功创建 {len(items)} 条证据清单数据')


def create_materials():
    """创建举证材料测试数据"""
    db = SessionLocal()

    try:
        # 检查是否已有材料
        existing_count = db.query(Material).count()
        if existing_count > 0:
            print(f'举证材料表已有 {existing_count} 条数据，跳过创建')
            return

        print('开始创建举证材料测试数据...')

        # 获取基地列表
        from app.models.audit import Base_
        bases = db.query(Base_).all()

        if not bases:
            print('  未找到基地数据，跳过创建举证材料')
            return

        # 为每个基地创建一些举证材料
        for base in bases:
            # 为前100个标准项创建材料
            for i in range(1, 101):
                material = Material(
                    id=str(uuid.uuid4()),
                    item_id=str(i).zfill(4),
                    base_id=base.id,
                    material_type='evidence',
                    file_format='pdf',
                    file_path=f'/materials/{base.id}/{i}.pdf',
                    content_text=f'举证材料内容 {i}...',
                    version=1,
                    uploaded_at=datetime.now()
                )
                db.add(material)

            print(f'  [OK] 为基地 {base.name} 创建了100条举证材料')

        db.commit()
        print('[OK] 成功创建举证材料测试数据')

    except Exception as e:
        db.rollback()
        print(f'[ERROR] 创建举证材料失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """主函数"""
    print('=' * 60)
    print('开始创建测试数据')
    print('=' * 60)

    # 初始化数据库
    init_db()
    print('[OK] 数据库初始化完成\n')

    # 创建标准项
    create_items()
    print()

    # 创建文档模板
    create_templates()
    print()

    # 创建证据清单
    create_evidence_list()
    print()

    # 创建举证材料
    create_materials()
    print()

    print('=' * 60)
    print('测试数据创建完成！')
    print('=' * 60)


if __name__ == '__main__':
    main()
