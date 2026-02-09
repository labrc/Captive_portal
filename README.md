# Captive Portal WiFi

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

[🇺🇸 **English Version**](#captive-portal-wifi-1) \| [🇪🇸 **Versión en
Español**](#captive-portal-wifi)

------------------------------------------------------------------------

# 🇪🇸 Captive Portal WiFi

Un portal cautivo WiFi moderno y escalable para hoteles, restaurantes y
espacios públicos con autenticación por correo electrónico, panel de
administración e integración con UniFi.

## 🌐 Características Principales

### ✅ Portal de Usuario

-   Formulario de acceso con nombre, email y teléfono
-   Validación de correo electrónico
-   Redirección automática post-registro
-   Interfaz multi-idioma (con banderas opcionales)
-   Logo personalizable

### 🛠 Panel de Administración

-   Autenticación segura con cookies firmadas
-   Vista de todos los registros en tiempo real
-   Exportación CSV automática/configurable
-   Limpieza automática de base de datos después de exportar
-   Logs detallados para depuración

### 🗄 Gestión de Datos

-   PostgreSQL con conexión pool asíncrona
-   Límite configurable de registros antes de exportar
-   Exportaciones automáticas por volumen o manuales
-   Nombres de tabla personalizables (sanitizados automáticamente)
-   Sistema de respaldo seguro con verificación de integridad

### 🔄 Integración UniFi

-   Compatible con UDM y CloudKey
-   Multiples modelos de autenticación (1, 2, 4)
-   Sesiones configurables (hasta 24 horas)
-   Autenticación automática de clientes en la red

### 🔒 Seguridad

-   Certificados SSL auto-generados o personalizados
-   Contenedores Docker aislados
-   Conexiones HTTPS forzadas vía Nginx
-   Cookies HTTP-only y SameSite
-   Passwords hasheados

## 📋 Requisitos Previos

-   Docker y Docker Compose
-   UniFi Controller accesible en la red
-   Puertos 80 y 443 libres

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

``` bash
git clone https://github.com/labrc/Captive_portal.git
cd Captive_portal
```

### 2. Configurar el archivo config.ini

``` ini
[General]
hotel_name = Mi Hotel
logo_file = mi_logo.png
default_language = es

[Admin]
username = admin
password = contraseña_fuerte
port = 80

[Database]
max_records = 500
table_name = registros_wifi

[Unifi]
controller = https://10.0.0.1
username = usuario_unifi
password = password_unifi
modelo = 2  # Para UDM
```

### 3. Levantar los servicios

``` bash
docker-compose up -d
```

### 4. Acceder al portal

Portal de usuarios: http://tu-servidor\
Panel admin: http://tu-servidor/admin\
Login admin: http://tu-servidor/login

------------------------------------------------------------------------

## 🐳 Estructura Docker

📦 Captive_portal ├── 📁 certs/\
├── 📁 db_data/\
├── 📁 exports/\
├── 📁 logs/\
├── 📁 static/\
├── 📁 templates/\
├── 📄 main.py\
├── 📄 database.py\
├── 📄 config.ini\
├── 📄 Dockerfile\
├── 📄 docker-compose.yml\
└── 📄 nginx.conf

### Servicios incluidos:

-   certs-init
-   db (PostgreSQL 16)
-   captive_app (FastAPI + Gunicorn)
-   nginx (Reverse proxy SSL)

------------------------------------------------------------------------

## ⚙️ Configuración Detallada

### Base de Datos

``` ini
[Database]
max_records = 1000
cleanup_on_export = yes
table_name = usuarios
```

### Exportaciones

``` ini
[Export]
export_dir = exports
absolute_export_path = /app/exports
date_format = %Y-%m-%d_%H-%M-%S
separador_alternativo = True
```

### UniFi

``` ini
[Unifi]
controller = https://10.0.0.1
site = default
username = Portal
password = Portal123
session_minutes = 1440
modelo = 2
```

------------------------------------------------------------------------

## 📊 Uso del Panel Admin

### Acceso

-   Navegar a http://servidor/login
-   Usar credenciales de config.ini
-   Cookie válida por 8 horas

### Funcionalidades

-   Ver registros
-   Exportar CSV manual
-   Exportación automática al alcanzar max_records
-   Logs activables

------------------------------------------------------------------------

## 🔧 Mantenimiento

### Reiniciar servicios

``` bash
docker-compose restart
```

### Ver logs

``` bash
docker-compose logs -f captive_app
```

### Backup base de datos

``` bash
docker exec captive_db pg_dump -U portalPortal captive_portal > backup.sql
```

### Actualizar

``` bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

------------------------------------------------------------------------

## 🐛 Solución de Problemas

### No se crean tablas

``` bash
docker-compose down -v
docker-compose up -d
```

### Error conexión UniFi

-   Verificar IP controller
-   Usuario local en UniFi
-   Firewall puerto 443

### No se generan certificados

``` bash
cd certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt -subj '/CN=portal.local'
```

------------------------------------------------------------------------

## 📁 Estructura Exportaciones

exports/ ├── info_de_personas_YYYY-MM-DD_HH-MM-SS.csv

Formato CSV: ID;Nombre;Email;Teléfono;MAC;IP;AP MAC;Fecha

------------------------------------------------------------------------

# 🇺🇸 Captive Portal WiFi

A modern and scalable WiFi captive portal for hotels, restaurants, and
public spaces with email authentication, admin panel, and UniFi
integration.

## 🌐 Key Features

### User Portal

-   Name, email, phone form
-   Email validation
-   Automatic redirect
-   Multi-language interface
-   Custom logo

### Admin Panel

-   Signed cookie authentication
-   Real-time registrations
-   Manual/automatic CSV export
-   Auto cleanup after export
-   Debug logs

### Data Management

-   PostgreSQL async pooling
-   Configurable export limits
-   Custom table names
-   Secure backups

### UniFi Integration

-   UDM & CloudKey compatible
-   Models 1, 2, 4
-   Sessions up to 24h
-   Auto client auth

### Security

-   SSL certificates
-   Docker isolation
-   Forced HTTPS
-   Secure cookies
-   Hashed passwords

------------------------------------------------------------------------

## 📄 License

MIT License

## 👨‍💻 Author

LabRC - GitHub
