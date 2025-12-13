from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('vehicle_system.db')
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

# 首页
@app.route('/')
def index():
    return render_template('dashboard.html')

# 仪表盘
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# 车辆列表
@app.route('/vehicle/list')
def vehicle_list():
    conn = get_db_connection()
    vehicles = conn.execute('''
        SELECT v.*, vs.status, vs.mileage, vs.fuel_level 
        FROM vehicle v 
        LEFT JOIN vehicle_status vs ON v.id = vs.vehicle_id
    ''').fetchall()
    conn.close()
    return render_template('vehicle/list.html', vehicles=vehicles)

# 车辆详情
@app.route('/vehicle/<int:vehicle_id>')
def vehicle_detail(vehicle_id):
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicle WHERE id = ?', (vehicle_id,)).fetchone()
    vehicle_status = conn.execute('SELECT * FROM vehicle_status WHERE vehicle_id = ?', (vehicle_id,)).fetchone()
    conn.close()
    
    if vehicle:
        return render_template('vehicle/detail.html', vehicle=vehicle, vehicle_status=vehicle_status)
    else:
        return "Vehicle not found", 404

# 车辆编辑
@app.route('/vehicle/<int:vehicle_id>/edit', methods=['GET', 'POST'])
def vehicle_edit(vehicle_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        # 获取表单数据
        vin = request.form['vin']
        plate_no = request.form['plate_no']
        brand_cn = request.form.get('brand_cn', '')
        brand_jp = request.form.get('brand_jp', '')
        model_cn = request.form.get('model_cn', '')
        model_jp = request.form.get('model_jp', '')
        color_cn = request.form.get('color_cn', '')
        color_jp = request.form.get('color_jp', '')
        model_year = request.form.get('model_year', type=int)
        type_designation_code = request.form.get('type_designation_code', '')
        classification_number = request.form.get('classification_number', '')
        engine_code = request.form.get('engine_code', '')
        engine_layout = request.form.get('engine_layout', '')
        displacement_cc = request.form.get('displacement_cc', type=int)
        fuel_type = request.form.get('fuel_type', '')
        drive_type = request.form.get('drive_type', '')
        transmission = request.form.get('transmission', '')
        ownership_type = request.form.get('ownership_type', '')
        owner_id = request.form.get('owner_id', type=int)
        driver_id = request.form.get('driver_id', type=int)
        garage_name = request.form.get('garage_name', '')
        garage_address_jp = request.form.get('garage_address_jp', '')
        garage_address_cn = request.form.get('garage_address_cn', '')
        garage_postcode = request.form.get('garage_postcode', '')
        purchase_date = request.form.get('purchase_date', '')
        purchase_price = request.form.get('purchase_price', type=float)
        note = request.form.get('note', '')
        
        # 更新车辆信息
        conn.execute('''
            UPDATE vehicle 
            SET vin = ?, plate_no = ?, brand_cn = ?, brand_jp = ?, model_cn = ?, model_jp = ?, 
                color_cn = ?, color_jp = ?, model_year = ?, type_designation_code = ?, 
                classification_number = ?, engine_code = ?, engine_layout = ?, displacement_cc = ?, 
                fuel_type = ?, drive_type = ?, transmission = ?, ownership_type = ?, 
                owner_id = ?, driver_id = ?, garage_name = ?, garage_address_jp = ?, 
                garage_address_cn = ?, garage_postcode = ?, purchase_date = ?, 
                purchase_price = ?, note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (vin, plate_no, brand_cn, brand_jp, model_cn, model_jp, color_cn, color_jp, 
              model_year, type_designation_code, classification_number, engine_code, 
              engine_layout, displacement_cc, fuel_type, drive_type, transmission, 
              ownership_type, owner_id, driver_id, garage_name, garage_address_jp, 
              garage_address_cn, garage_postcode, purchase_date, purchase_price, 
              note, vehicle_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))
    else:
        vehicle = conn.execute('SELECT * FROM vehicle WHERE id = ?', (vehicle_id,)).fetchone()
        conn.close()
        
        if vehicle:
            return render_template('vehicle/edit.html', vehicle=vehicle)
        else:
            return "Vehicle not found", 404

# 车辆文件管理
@app.route('/vehicle/<int:vehicle_id>/files', methods=['GET', 'POST'])
def vehicle_files(vehicle_id):
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicle WHERE id = ?', (vehicle_id,)).fetchone()
    conn.close()
    
    if vehicle:
        return render_template('vehicle/files.html', vehicle=vehicle)
    else:
        return "Vehicle not found", 404

# 车辆日志
@app.route('/vehicle/<int:vehicle_id>/logs')
def vehicle_logs(vehicle_id):
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicle WHERE id = ?', (vehicle_id,)).fetchone()
    conn.close()
    
    if vehicle:
        return render_template('vehicle/logs.html', vehicle=vehicle)
    else:
        return "Vehicle not found", 404

# 管理员 - 用户管理
@app.route('/admin/users')
def admin_users():
    return render_template('admin/users.html')

# 管理员 - 字段权限管理
@app.route('/admin/field_permissions')
def admin_field_permissions():
    return render_template('admin/field_permissions.html')

# 公共二维码页面 (public)
@app.route('/v/<qr_slug>')
def qr_public(qr_slug):
    # 在实际应用中，这里会根据qr_slug查找对应的车辆
    # 为了演示，我们使用一个示例车辆
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicle WHERE id = 1').fetchone()
    vehicle_status = conn.execute('SELECT * FROM vehicle_status WHERE vehicle_id = 1').fetchone()
    conn.close()
    
    if vehicle and vehicle_status:
        return render_template('public/qr_public.html', 
                               vehicle=vehicle, 
                               vehicle_status=vehicle_status, 
                               qr_slug=qr_slug)
    else:
        return "Vehicle not found", 404

# 公共二维码页面 (detail)
@app.route('/v/<qr_slug>/detail')
def qr_detail(qr_slug):
    # 在实际应用中，这里会根据qr_slug查找对应的车辆
    # 为了演示，我们使用一个示例车辆
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicle WHERE id = 1').fetchone()
    vehicle_status = conn.execute('SELECT * FROM vehicle_status WHERE vehicle_id = 1').fetchone()
    conn.close()
    
    if vehicle and vehicle_status:
        return render_template('public/qr_detail.html', 
                               vehicle=vehicle, 
                               vehicle_status=vehicle_status, 
                               qr_slug=qr_slug)
    else:
        return "Vehicle not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)