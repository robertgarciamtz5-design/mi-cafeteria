from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database
import json
from datetime import datetime
import os

app = Flask(__name__, template_folder="pages", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "clave_super_secreta")

# Página principal: redirige al login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        user = database.login_user(correo, contrasena)
        if user:
            session['usuario_id'] = user['id']
            session['nombre'] = user['nombre']
            session['carrito'] = []
            flash('Inicio de sesión exitoso')
            return redirect(url_for('menu'))
        else:
            flash('Correo o contraseña incorrectos')
    return render_template('login.html')

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        contrasena = request.form['contrasena']
        try:
            database.register_user(nombre, correo, telefono, contrasena)
            flash('Usuario registrado con éxito')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error al registrar usuario')
    return render_template('register.html')

# Página del menú
@app.route('/menu')
def menu():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if 'carrito' not in session:
        session['carrito'] = []
    
    try:
        items, semana_rotativa = database.get_menu_por_categoria()
        semana_actual = database.get_semana_actual()
        
        return render_template('menu.html', 
                             nombre=session['nombre'], 
                             items=items,
                             semana_actual=semana_actual,
                             semana_rotativa=semana_rotativa)
    except Exception as e:
        flash('Error cargando el menú')
        return render_template('menu.html', 
                             nombre=session['nombre'], 
                             items={'bebidas': [], 'snacks': [], 'menu_dia': []},
                             semana_actual=1,
                             semana_rotativa=1)

# Agregar producto al carrito
@app.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    try:
        producto_id = int(request.json.get('producto_id'))
        cantidad = int(request.json.get('cantidad', 1))
        
        producto = database.get_producto_por_id(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'})
        
        if 'carrito' not in session:
            session['carrito'] = []
        
        carrito = session['carrito']
        
        # Verificar si el producto ya está en el carrito
        producto_en_carrito = None
        for item in carrito:
            if item['id'] == producto_id:
                producto_en_carto = item
                break
        
        if producto_en_carrito:
            producto_en_carrito['cantidad'] += cantidad
        else:
            carrito.append({
                'id': producto['id'],
                'nombre': producto['nombre'],
                'precio': float(producto['precio']),
                'cantidad': cantidad,
                'categoria': producto['categoria']
            })
        
        session['carrito'] = carrito
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Producto agregado al carrito',
            'total_items': sum(item['cantidad'] for item in carrito)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Quitar producto del carrito
@app.route('/quitar_del_carrito', methods=['POST'])
def quitar_del_carrito():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    try:
        producto_id = int(request.json.get('producto_id'))
        
        if 'carrito' not in session:
            session['carrito'] = []
        
        carrito = session['carrito']
        carrito = [item for item in carrito if item['id'] != producto_id]
        
        session['carrito'] = carrito
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Producto removido del carrito',
            'total_items': sum(item['cantidad'] for item in carrito)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Ver carrito
@app.route('/carrito')
def ver_carrito():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if 'carrito' not in session:
        session['carrito'] = []
    
    carrito = session['carrito']
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    
    return render_template('carrito.html', 
                         nombre=session['nombre'], 
                         carrito=carrito, 
                         total=total)

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
