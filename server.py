from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database
import json
from datetime import datetime
import os

app = Flask(__name__, template_folder="pages")
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
            session['carrito'] = []  # Inicializar carrito vacío
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
        database.register_user(nombre, correo, telefono, contrasena)
        flash('Usuario registrado con éxito')
        return redirect(url_for('login'))
    return render_template('register.html')

# Página del menú (solo si está logueado)
@app.route('/menu')
def menu():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    # Inicializar carrito si no existe
    if 'carrito' not in session:
        session['carrito'] = []
    
    items, semana_rotativa = database.get_menu_por_categoria()
    semana_actual = database.get_semana_actual()
    
    return render_template('menu.html', 
                         nombre=session['nombre'], 
                         items=items,
                         semana_actual=semana_actual,
                         semana_rotativa=semana_rotativa)

# Agregar producto al carrito
@app.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    producto_id = int(request.json.get('producto_id'))
    cantidad = int(request.json.get('cantidad', 1))
    
    producto = database.get_producto_por_id(producto_id)
    if not producto:
        return jsonify({'success': False, 'message': 'Producto no encontrado'})
    
    # Inicializar carrito si no existe
    if 'carrito' not in session:
        session['carrito'] = []
    
    carrito = session['carrito']
    
    # Verificar si el producto ya está en el carrito
    producto_en_carrito = None
    for item in carrito:
        if item['id'] == producto_id:
            producto_en_carrito = item
            break
    
    if producto_en_carrito:
        # Actualizar cantidad si ya existe
        producto_en_carrito['cantidad'] += cantidad
    else:
        # Agregar nuevo producto al carrito
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

# Quitar producto del carrito
@app.route('/quitar_del_carrito', methods=['POST'])
def quitar_del_carrito():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    producto_id = int(request.json.get('producto_id'))
    
    if 'carrito' not in session:
        session['carrito'] = []
    
    carrito = session['carrito']
    
    # Buscar y remover el producto
    carrito = [item for item in carrito if item['id'] != producto_id]
    
    session['carrito'] = carrito
    session.modified = True
    
    return jsonify({
        'success': True, 
        'message': 'Producto removido del carrito',
        'total_items': sum(item['cantidad'] for item in carrito)
    })

# Actualizar cantidad en el carrito
@app.route('/actualizar_cantidad', methods=['POST'])
def actualizar_cantidad():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    producto_id = int(request.json.get('producto_id'))
    cantidad = int(request.json.get('cantidad', 1))
    
    if cantidad <= 0:
        return quitar_del_carrito() # Llama a la función para remover si la cantidad es 0 o menos
    
    if 'carrito' not in session:
        session['carrito'] = []
    
    carrito = session['carrito']
    
    # Actualizar cantidad
    for item in carrito:
        if item['id'] == producto_id:
            item['cantidad'] = cantidad
            break
    
    session['carrito'] = carrito
    session.modified = True
    
    return jsonify({
        'success': True, 
        'message': 'Cantidad actualizada',
        'total_items': sum(item['cantidad'] for item in carrito)
    })

# Ver carrito
@app.route('/carrito')
def ver_carrito():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    # Inicializar carrito si no existe
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