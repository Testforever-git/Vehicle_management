import sqlite3
import os
from datetime import datetime

def init_database():
    # 连接到SQLite数据库（如果不存在则会创建）
    conn = sqlite3.connect('vehicle_system.db')
    cursor = conn.cursor()
    
    # 读取SQL文件内容
    with open('create_db.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 执行SQL语句创建表
    cursor.executescript(sql_content)
    
    # 插入默认角色数据
    roles = [
        ('viewer', 'Viewer', '查看者'),
        ('sales', 'Sales', '销售'),
        ('engineer', 'Engineer', '工程师'),
        ('finance', 'Finance', '财务'),
        ('admin', 'Administrator', '管理员'),
        ('customer', 'Customer', '客户')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO role (role_code, name_jp, name_cn) 
        VALUES (?, ?, ?)
    ''', roles)
    
    # 插入默认管理员用户
    cursor.execute('''
        INSERT OR IGNORE INTO user (username, password_hash, role_id, is_active) 
        VALUES ('admin', 'pbkdf2:sha256:260000$...', 
                (SELECT id FROM role WHERE role_code = 'admin'), 1)
    ''')
    
    # 插入一些示例车辆数据
    sample_vehicle = {
        'vin': 'JH4NA21691T000001',
        'plate_no': '品川500 あ12-345',
        'brand_cn': '本田',
        'brand_jp': 'ホンダ',
        'model_cn': '思域',
        'model_jp': 'シビック',
        'color_cn': '白色',
        'color_jp': 'ホワイト',
        'model_year': 2023,
        'type_designation_code': 'AABC-12345',
        'classification_number': '1-123-4567',
        'engine_code': 'K20C1',
        'engine_layout': 'Inline',
        'displacement_cc': 2000,
        'fuel_type': 'Gasoline',
        'drive_type': 'FWD',
        'transmission': 'CVT',
        'ownership_type': 'Company',
        'garage_name': '品川营业所',
        'garage_address_jp': '東京都品川区○○○-○○○',
        'garage_address_cn': '东京都品川区○○○-○○○',
        'garage_postcode': '141-0021',
        'purchase_date': '2023-01-15',
        'purchase_price': 2500000.00,
        'note': '公司用车，定期维护'
    }
    
    placeholders = ', '.join(['?' for _ in sample_vehicle])
    columns = ', '.join(sample_vehicle.keys())
    
    cursor.execute(f'''
        INSERT OR IGNORE INTO vehicle ({columns}) 
        VALUES ({placeholders})
    ''', list(sample_vehicle.values()))
    
    # 获取插入的车辆ID
    vehicle_id = cursor.lastrowid
    if vehicle_id is None:
        cursor.execute("SELECT id FROM vehicle WHERE vin = 'JH4NA21691T000001'")
        vehicle_id = cursor.fetchone()[0]
    
    # 插入对应的车辆状态
    cursor.execute('''
        INSERT OR IGNORE INTO vehicle_status 
        (vehicle_id, status, mileage, fuel_level, location_desc, update_source) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (vehicle_id, 'available', 15230, 85, '品川营业所', 'manual'))
    
    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")
    print("Database file: vehicle_system.db")
    print("Default admin user: admin")

if __name__ == "__main__":
    init_database()