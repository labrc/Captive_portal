# Captive Portal WiFi

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

[🇺🇸 **English Version**](#captive-portal-wifi-1) | [🇦🇷 **Versión en Español**](#captive-portal-wifi)

---

# 🇦🇷 Captive Portal WiFi

Un portal cautivo WiFi moderno y escalable para hoteles, restaurantes y espacios públicos con autenticación por correo electrónico, panel de administración e integración con UniFi.

## 🌐 **Características Principales**

### ✅ **Portal de Usuario**
- Formulario de acceso con nombre, email y teléfono
- Validación de correo electrónico
- Redirección automática post-registro
- Interfaz multi-idioma (con banderas opcionales)
- Logo personalizable

### 🛠 **Panel de Administración**
- Autenticación segura con cookies firmadas
- Vista de todos los registros en tiempo real
- Exportación CSV automática/configurable
- Limpieza automática de base de datos después de exportar
- Logs detallados para depuración

### 🗄 **Gestión de Datos**
- PostgreSQL con conexión pool asíncrona
- Límite configurable de registros antes de exportar
- Exportaciones automáticas por volumen o manuales
- Nombres de tabla personalizables (sanitizados automáticamente)
- Sistema de respaldo seguro con verificación de integridad

### 🔄 **Integración UniFi**
- Compatible con UDM y CloudKey
- Multiples modelos de autenticación (1, 2, 4)
- Sesiones configurables (hasta 24 horas)
- Autenticación automática de clientes en la red

### 🔒 **Seguridad**
- Certificados SSL auto-generados o personalizados
- Contenedores Docker aislados
- Conexiones HTTPS forzadas vía Nginx
- Cookies HTTP-only y SameSite
- Passwords hasheados

## 📋 **Requisitos Previos**

- **Docker** y **Docker Compose**
- **UniFi Controller** accesible en la red
- Puertos 80 y 443 libres

## 🚀 **Instalación Rápida**

### 1. Clonar el repositorio
```bash
git clone https://github.com/labrc/Captive_portal.git
cd Captive_portal
