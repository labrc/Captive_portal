# Captive Portal WiFi

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

🇦🇷 [Versión en Español](#versión-en-español) | 🇺🇸 [English Version](#english-version)

---

# 🇦🇷 Versión en Español

Un portal cautivo WiFi moderno y escalable para hoteles, restaurantes y espacios públicos con autenticación por correo electrónico, panel de administración e integración con UniFi.

## 🌐 Características Principales

### ✅ Portal de Usuario
- Formulario de acceso con nombre, email y teléfono
- Validación de correo electrónico
- Redirección automática post-registro
- Interfaz multi-idioma (con banderas opcionales)
- Logo personalizable

### 🛠 Panel de Administración
- Autenticación segura con cookies firmadas
- Vista de todos los registros en tiempo real
- Exportación CSV automática/configurable
- Limpieza automática de base de datos después de exportar
- Logs detallados para depuración

### 🗄 Gestión de Datos
- PostgreSQL con conexión pool asíncrona
- Límite configurable de registros antes de exportar
- Exportaciones automáticas por volumen o manuales
- Nombres de tabla personalizables (sanitizados automáticamente)
- Sistema de respaldo seguro con verificación de integridad

### 🔄 Integración UniFi
- Compatible con UDM y CloudKey
- Multiples modelos de autenticación (1, 2, 4)
- Sesiones configurables (hasta 24 horas)
- Autenticación automática de clientes en la red

### 🔒 Seguridad
- Certificados SSL auto-generados o personalizados
- Contenedores Docker aislados
- Conexiones HTTPS forzadas vía Nginx
- Cookies HTTP-only y SameSite
- Passwords hasheados

## 📋 Requisitos Previos

- Docker y Docker Compose
- UniFi Controller accesible en la red
- Puertos 80 y 443 libres

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone https://github.com/labrc/Captive_portal.git
cd Captive_portal
```

### 2. Configurar el archivo config.ini
```ini
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
modelo = 2
```

### 3. Levantar los servicios
```bash
docker-compose up -d
```

### 4. Acceder al portal
- Portal de usuarios: \`http://tu-servidor\`
- Panel admin: \`http://tu-servidor/admin\`
- Login admin: \`http://tu-servidor/login\`

## 🐳 Estructura Docker

```
📦 Captive_portal
├── 📁 certs/          # Certificados SSL (auto-generados)
├── 📁 db_data/        # Volumen PostgreSQL
├── 📁 exports/        # CSVs exportados
├── 📁 logs/           # Logs de la aplicación
├── 📁 static/         # CSS, JS, imágenes
├── 📁 templates/      # HTML templates
├── 📄 main.py         # Aplicación FastAPI
├── 📄 database.py     # Lógica de base de datos
├── 📄 config.ini      # Configuración (montado como volumen)
├── 📄 Dockerfile      # Imagen de la aplicación
├── 📄 docker-compose.yml  # Orquestación
└── 📄 nginx.conf      # Configuración Nginx
```

### Servicios incluidos:
- certs-init: Genera certificados SSL si no existen
- db: PostgreSQL 16 con health checks
- captive_app: Aplicación FastAPI con Gunicorn
- nginx: Reverse proxy con SSL

## ⚙️ Configuración Detallada

### Base de Datos
```ini
[Database]
max_records = 1000      # Registros antes de exportar automáticamente
cleanup_on_export = yes # Vaciar tabla después de exportar
table_name = usuarios   # Nombre personalizable de tabla
```

### Exportaciones
```ini
[Export]
export_dir = exports
absolute_export_path = /app/exports
date_format = %Y-%m-%d_%H-%M-%S
separador_alternativo = True  # Usar ; en lugar de ,
```

### UniFi
```ini
[Unifi]
controller = https://10.0.0.1  # IP de tu UniFi Controller
site = default                 # Sitio UniFi
username = Portal              # Usuario local UniFi
password = Portal123           # Password del usuario
session_minutes = 1440         # 24 horas
modelo = 2                     # 2 para UDM, 1 para CloudKey
```

## 📊 Uso del Panel Admin

### Acceso
1. Navegar a \`http://servidor/login\`
2. Usar credenciales de \`config.ini\`
3. Session cookie válida por 8 horas

### Funcionalidades
- Ver registros: Tabla con todos los usuarios registrados
- Exportar CSV: Descarga manual con "Exportar CSV"
- Exportación automática: Cuando se alcanza \`max_records\`
- Logs: Depuración activable en \`config.ini\`

## 🔧 Mantenimiento

### Reiniciar servicios
```bash
docker-compose restart
```

### Ver logs
```bash
docker-compose logs -f captive_app
```

### Backup de datos
```bash
# Los CSVs se guardan automáticamente en ./exports/
# Backup manual de la base de datos:
docker exec captive_db pg_dump -U portalPortal captive_portal > backup.sql
```

### Actualizar
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

## 🐛 Solución de Problemas

### Problema: No se crean las tablas
Solución:
```bash
docker-compose down -v  # Elimina volúmenes
docker-compose up -d
```

### Problema: Error de conexión a UniFi
Verificar:
1. IP del controller correcta en \`config.ini\`
2. Usuario local creado en UniFi
3. Firewall permite conexiones al puerto 443

### Problema: No se generan certificados SSL
Solución manual:
```bash
cd certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt -subj '/CN=portal.local'
```

## 📁 Estructura de Archivos Exportados

```
exports/
├── info_de_personas_2024-01-15_14-30-22.csv
├── info_de_personas_2024-01-16_09-15-45.csv
└── info_de_personas_2024-01-17_11-20-33.csv
```

Formato CSV (ejemplo):
```csv
ID;Nombre;Email;Teléfono;MAC;IP;AP MAC;Fecha
1;Juan Pérez;juan@email.com;+341234567;AA:BB:CC:DD:EE:FF;192.168.1.100;00:11:22:33:44:55;2024-01-15 14:30:22
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (\`git checkout -b feature/nueva-funcionalidad\`)
3. Commit cambios (\`git commit -am 'Añadir nueva funcionalidad'\`)
4. Push a la rama (\`git push origin feature/nueva-funcionalidad\`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 👨‍💻 Autor

LabRC - [GitHub](https://github.com/labrc)

---

# 🇺🇸 English Version

A modern and scalable WiFi captive portal for hotels, restaurants, and public spaces with email authentication, admin panel, and UniFi integration.

## 🌐 Key Features

### ✅ User Portal
- Access form with name, email, and phone
- Email validation
- Automatic post-registration redirect
- Multi-language interface (with optional flags)
- Customizable logo

### 🛠 Admin Panel
- Secure authentication with signed cookies
- Real-time view of all registrations
- Configurable automatic CSV export
- Automatic database cleanup after export
- Detailed debugging logs

### 🗄 Data Management
- PostgreSQL with async connection pooling
- Configurable record limit before export
- Automatic exports by volume or manual
- Customizable table names (automatically sanitized)
- Secure backup system with integrity verification

### 🔄 UniFi Integration
- Compatible with UDM and CloudKey
- Multiple authentication models (1, 2, 4)
- Configurable sessions (up to 24 hours)
- Automatic client authentication on network

### 🔒 Security
- Auto-generated or custom SSL certificates
- Isolated Docker containers
- Forced HTTPS connections via Nginx
- HTTP-only and SameSite cookies
- Hashed passwords

## 📋 Prerequisites

- Docker and Docker Compose
- UniFi Controller accessible on the network
- Ports 80 and 443 available

## 🚀 Quick Installation

### 1. Clone the repository
```bash
git clone https://github.com/labrc/Captive_portal.git
cd Captive_portal
```

### 2. Configure the config.ini file
```ini
[General]
hotel_name = My Hotel
logo_file = my_logo.png
default_language = en

[Admin]
username = admin
password = strong_password
port = 80

[Database]
max_records = 500
table_name = wifi_users

[Unifi]
controller = https://10.0.0.1
username = unifi_user
password = unifi_password
modelo = 2
```

### 3. Start the services
```bash
docker-compose up -d
```

### 4. Access the portal
- User portal: \`http://your-server\`
- Admin panel: \`http://your-server/admin\`
- Admin login: \`http://your-server/login\`

## 🐳 Docker Structure

```
📦 Captive_portal
├── 📁 certs/          # SSL certificates (auto-generated)
├── 📁 db_data/        # PostgreSQL volume
├── 📁 exports/        # Exported CSVs
├── 📁 logs/           # Application logs
├── 📁 static/         # CSS, JS, images
├── 📁 templates/      # HTML templates
├── 📄 main.py         # FastAPI application
├── 📄 database.py     # Database logic
├── 📄 config.ini      # Configuration (mounted as volume)
├── 📄 Dockerfile      # Application image
├── 📄 docker-compose.yml  # Orchestration
└── 📄 nginx.conf      # Nginx configuration
```

### Included services:
- certs-init: Generates SSL certificates if missing
- db: PostgreSQL 16 with health checks
- captive_app: FastAPI application with Gunicorn
- nginx: Reverse proxy with SSL

## ⚙️ Detailed Configuration

### Database
```ini
[Database]
max_records = 1000      # Records before automatic export
cleanup_on_export = yes # Clear table after exporting
table_name = users      # Customizable table name
```

### Exports
```ini
[Export]
export_dir = exports
absolute_export_path = /app/exports
date_format = %Y-%m-%d_%H-%M-%S
separador_alternativo = True  # Use ; instead of ,
```

### UniFi
```ini
[Unifi]
controller = https://10.0.0.1  # Your UniFi Controller IP
site = default                 # UniFi site
username = Portal              # Local UniFi user
password = Portal123           # User password
session_minutes = 1440         # 24 hours
modelo = 2                     # 2 for UDM, 1 for CloudKey
```

## 📊 Admin Panel Usage

### Access
1. Navigate to \`http://server/login\`
2. Use credentials from \`config.ini\`
3. Session cookie valid for 8 hours

### Functionality
- View records: Table with all registered users
- Export CSV: Manual download with 'Export CSV'
- Automatic export: When \`max_records\` is reached
- Logs: Debugging activatable in \`config.ini\`

## 🔧 Maintenance

### Restart services
```bash
docker-compose restart
```

### View logs
```bash
docker-compose logs -f captive_app
```

### Data backup
```bash
# CSVs are automatically saved in ./exports/
# Manual database backup:
docker exec captive_db pg_dump -U portalPortal captive_portal > backup.sql
```

### Update
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

## 🐛 Troubleshooting

### Issue: Tables not created
Solution:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d
```

### Issue: UniFi connection error
Verify:
1. Correct controller IP in \`config.ini\`
2. Local user created in UniFi
3. Firewall allows connections to port 443

### Issue: SSL certificates not generated
Manual solution:
```bash
cd certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt -subj '/CN=portal.local'
```

## 📁 Exported Files Structure

```
exports/
├── info_de_personas_2024-01-15_14-30-22.csv
├── info_de_personas_2024-01-16_09-15-45.csv
└── info_de_personas_2024-01-17_11-20-33.csv
```

CSV format (example):
```csv
ID;Name;Email;Phone;MAC;IP;AP MAC;Date
1;John Doe;john@email.com;+341234567;AA:BB:CC:DD:EE:FF;192.168.1.100;00:11:22:33:44:55;2024-01-15 14:30:22
```

## 🤝 Contributing

1. Fork the project
2. Create a branch (\`git checkout -b feature/new-feature\`)
3. Commit changes (\`git commit -am 'Add new feature'\`)
4. Push to the branch (\`git push origin feature/new-feature\`)
5. Open a Pull Request

## 📄 License

This project is under the MIT License.

## 👨‍💻 Author

LabRC - [GitHub](https://github.com/labrc)

---

¿Necesitas ayuda adicional? Abre un issue en GitHub o contacta al autor.
Need additional help? Open an issue on GitHub or contact the author.
