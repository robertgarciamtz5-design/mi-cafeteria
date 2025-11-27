import mysql.connector
import os
from datetime import datetime

def get_connection():
    # En Render usaremos una base de datos MySQL externa
    # Por ahora usaremos SQLite para que funcione
    import sqlite3
    return sqlite3.connect('cafeteria.db')

def get_semana_actual():
    """Obtiene el número de la semana actual del año"""
    return datetime.now().isocalendar()[1]

def get_menu_por_categoria():
    connection = get_connection()
    
    # Para SQLite necesitamos un adaptador diferente
    if 'sqlite3' in str(type(connection)):
        cursor = connection.cursor()
        
        # Obtener semana actual y aplicar módulo para rotación (1-6)
        semana_actual = get_semana_actual()
        semana_rotativa = (semana_actual - 1) % 6 + 1  # Rota entre 1-6
        
        # Obtener productos normales (bebidas y snacks)
        cursor.execute("SELECT * FROM menu WHERE categoria IN ('bebidas', 'snacks') ORDER BY categoria, nombre")
        productos_normales = cursor.fetchall()
        
        # Convertir a diccionarios
        productos_normales_dict = []
        for prod in productos_normales:
            productos_normales_dict.append({
                'id': prod[0],
                'nombre': prod[1],
                'precio': float(prod[2]),
                'categoria': prod[3],
                'semana_menu': prod[4]
            })
        
        # Obtener menú del día de la semana rotativa
        cursor.execute("SELECT * FROM menu WHERE categoria = 'menu_dia' AND semana_menu = ? ORDER BY nombre", (semana_rotativa,))
        menu_dia_actual = cursor.fetchall()
        
        # Convertir a diccionarios
        menu_dia_actual_dict = []
        for prod in menu_dia_actual:
            menu_dia_actual_dict.append({
                'id': prod[0],
                'nombre': prod[1],
                'precio': float(prod[2]),
                'categoria': prod[3],
                'semana_menu': prod[4]
            })
        
        connection.close()
        
        # Organizar por categorías
        menu_organizado = {
            'bebidas': [],
            'snacks': [],
            'menu_dia': menu_dia_actual_dict
        }
        
        for item in productos_normales_dict:
            categoria = item['categoria']
            if categoria in menu_organizado:
                menu_organizado[categoria].append(item)
        
        return menu_organizado, semana_rotativa
    else:
        # Código original para MySQL
        cursor = connection.cursor(dictionary=True)
        
        # Obtener semana actual y aplicar módulo para rotación (1-6)
        semana_actual = get_semana_actual()
        semana_rotativa = (semana_actual - 1) % 6 + 1  # Rota entre 1-6
        
        # Obtener productos normales (bebidas y snacks)
        cursor.execute("SELECT * FROM menu WHERE categoria IN ('bebidas', 'snacks') ORDER BY categoria, nombre")
        productos_normales = cursor.fetchall()
        
        # Obtener menú del día de la semana rotativa
        cursor.execute("SELECT * FROM menu WHERE categoria = 'menu_dia' AND semana_menu = %s ORDER BY nombre", (semana_rotativa,))
        menu_dia_actual = cursor.fetchall()
        
        connection.close()
        
        # Organizar por categorías
        menu_organizado = {
            'bebidas': [],
            'snacks': [],
            'menu_dia': menu_dia_actual
        }
        
        for item in productos_normales:
            categoria = item['categoria']
            menu_organizado[categoria].append(item)
        
        return menu_organizado, semana_rotativa

def get_producto_por_id(producto_id):
    connection = get_connection()
    
    if 'sqlite3' in str(type(connection)):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM menu WHERE id = ?", (producto_id,))
        producto = cursor.fetchone()
        connection.close()
        
        if producto:
            return {
                'id': producto[0],
                'nombre': producto[1],
                'precio': float(producto[2]),
                'categoria': producto[3],
                'semana_menu': producto[4]
            }
        return None
    else:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM menu WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        connection.close()
        return producto

def init_db():
    """Inicializa la base de datos SQLite"""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Crear tabla menu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            categoria TEXT,
            semana_menu INTEGER
        )
    ''')
    
    # Crear tabla usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            telefono TEXT NOT NULL,
            contrasena TEXT NOT NULL
        )
    ''')
    
    # Insertar datos de ejemplo
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        # Insertar menú de ejemplo
        menu_items = [
            # Bebidas
            ('Café Americano', 25.00, 'bebidas', None),
            ('Latte', 40.00, 'bebidas', None),
            ('Jumex', 18.00, 'bebidas', None),
            ('Pepsi', 20.00, 'bebidas', None),
            ('Gatorade', 25.00, 'bebidas', None),
            
            # Snacks
            ('Pan de Chocolate', 20.00, 'snacks', None),
            ('Galletas', 15.00, 'snacks', None),
            ('Sabritas', 22.00, 'snacks', None),
            ('Muffin de Arándanos', 25.00, 'snacks', None),
            ('Croissant', 18.00, 'snacks', None),
            
            # Menú del día - Semana 1
            ('Huevos al Gusto', 70.00, 'menu_dia', 1),
            ('Sándwich de Pollo', 65.00, 'menu_dia', 1),
            ('Ensalada César', 55.00, 'menu_dia', 1),
            ('Pasta Alfredo', 75.00, 'menu_dia', 1),
            ('Sopa del Día', 45.00, 'menu_dia', 1),
            
            # Semana 2
            ('Pechuga a la Plancha', 80.00, 'menu_dia', 2),
            ('Pescado al Limón', 95.00, 'menu_dia', 2),
            ('Lasagna', 90.00, 'menu_dia', 2),
            ('Hamburguesa Clásica', 70.00, 'menu_dia', 2),
            ('Pizza Margherita', 85.00, 'menu_dia', 2),
        ]
        
        cursor.executemany(
            "INSERT INTO menu (nombre, precio, categoria, semana_menu) VALUES (?, ?, ?, ?)",
            menu_items
        )
    
    connection.commit()
    connection.close()

def register_user(nombre, correo, telefono, contrasena):
    connection = get_connection()
    cursor = connection.cursor()
    
    if 'sqlite3' in str(type(connection)):
        query = "INSERT INTO usuarios (nombre, correo, telefono, contrasena) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (nombre, correo, telefono, contrasena))
    else:
        query = "INSERT INTO usuarios (nombre, correo, telefono, contrasena) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nombre, correo, telefono, contrasena))
    
    connection.commit()
    connection.close()

def login_user(correo, contrasena):
    connection = get_connection()
    
    if 'sqlite3' in str(type(connection)):
        cursor = connection.cursor()
        query = "SELECT * FROM usuarios WHERE correo = ? AND contrasena = ?"
        cursor.execute(query, (correo, contrasena))
        user = cursor.fetchone()
        connection.close()
        
        if user:
            return {
                'id': user[0],
                'nombre': user[1],
                'correo': user[2],
                'telefono': user[3],
                'contrasena': user[4]
            }
        return None
    else:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE correo = %s AND contrasena = %s"
        cursor.execute(query, (correo, contrasena))
        user = cursor.fetchone()
        connection.close()
        return user

# Inicializar la base de datos al importar
init_db()