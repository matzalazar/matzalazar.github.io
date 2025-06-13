---
layout: default
title: Sistema de Gestión Empresarial
permalink: /projects/gestion/
---

## 📊 Sistema Integral de Gestión Empresarial

Este sistema fue desarrollado para centralizar y profesionalizar la gestión de una empresa prestadora de servicios, integrando todas sus áreas críticas: operaciones, recursos humanos, comercial, logística y patrimonio. Fue pensado desde el inicio para adaptarse a una lógica organizativa compleja, con múltiples roles, trazabilidad completa y compatibilidad con normas de calidad como **ISO 9001**.

---

### 🎯 Contexto

La empresa operaba inicialmente con distintos sistemas y planillas desconectadas entre sí, lo que dificultaba la trazabilidad, el control de cumplimiento y la colaboración entre sectores. Cada área gestionaba sus propios registros de personal, turnos, stock, tareas y documentación, generando inconsistencias y cuellos de botella.

Se planteó la necesidad de contar con un sistema único, accesible y modular que permitiera integrar todas las funciones operativas y administrativas bajo una misma plataforma.

---

### 🔍 Desafíos

- Integrar sectores con lógicas muy diferentes (RRHH, Operaciones, Comercial, Logística).
- Establecer un flujo de trabajo completo, desde la cotización hasta la liquidación.
- Validar automáticamente condiciones sindicales, convenios colectivos y calendarios de trabajo.
- Garantizar trazabilidad de turnos, entregas de stock, documentación y vehículos.
- Implementar un sistema de auditoría que registre acciones de cada usuario.
- Diseñar dashboards diferenciados por rol, mostrando solo la información pertinente.
- Cumplir con los principios de gestión de calidad exigidos por auditorías externas.

---

### 🛠️ Solución

**1. Módulo Comercial**

Permite crear clientes, objetivos y cotizaciones con cobertura horaria. Una vez aprobadas, las cotizaciones generan órdenes de venta que sirven de base para facturación y permisos de trabajo. También se registra la relación con proveedores y compras.

**2. Módulo Operativo**

Los supervisores cargan turnos con información precisa sobre quién trabajó, cuándo y dónde. La gerencia genera permisos de trabajo que agrupan estos turnos y los valida formalmente. El sistema aplica automáticamente lógica sindical para calcular horas normales, al 50%, 100% o turnos cubiertos en días feriados.

**3. Recursos Humanos**

Gestión completa de empleados, historial laboral, documentación, fichas médicas, vacaciones y licencias especiales. Cada empleado está vinculado a un sindicato y a una empresa contratante. Los documentos y entregas están trazados en el historial del empleado.

**4. Logística y Stock**

Permite registrar y controlar entregas de ropa, elementos de seguridad y otros insumos. Las solicitudes pueden ser generadas por supervisores o RRHH y aprobadas por Logística, descontando automáticamente el inventario.

**5. Patrimonio**

Control detallado de herramientas y vehículos. Se registran estados operativos, asignaciones, documentación crítica (seguros, VTV, GNC), historial de mantenimientos y fechas de vencimiento. Se generan alertas sobre revisiones o servicios pendientes.

**6. Auditoría y Seguridad**

El sistema registra toda acción realizada sobre la base de datos: qué se hizo, quién lo hizo, desde qué IP y con qué navegador. Esto permite cumplir con requisitos de trazabilidad y control exigidos por la norma ISO 9001.

**7. Dashboard por Rol**

Cada usuario accede a un dashboard personalizado, con métricas e información relevante según su sector: RRHH, Logística, Comercial, Operaciones o Gerencia. Esto mejora la experiencia de uso y evita accesos innecesarios.

---

### ✅ Resultados

- Eliminación de registros paralelos y planillas dispersas.
- Integración fluida entre áreas operativas y administrativas.
- Reducción de errores en liquidación y control de stock.
- Mejora de la trazabilidad en procesos clave (turnos, permisos, entregas).
- Sistema listo para auditar bajo estándares ISO.
- Estructura modular escalable a nuevas funcionalidades y empresas.

---

📁 Este proyecto se encuentra en producción y se despliega en un entorno seguro sobre servidor Linux con base de datos PostgreSQL.

🔐 Por confidencialidad, el repositorio es privado. Si te interesa conocer más sobre este desarrollo, podés ponerte en contacto conmigo para una demostración controlada.