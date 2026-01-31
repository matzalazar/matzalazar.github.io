---
layout: post
title: "CCT en Django"
date: 2025-05-21
category: arquitectura
description: "Implementación de validación temporal estricta en Django usando constraints para evitar estados inválidos"
---

## Cómo gestionar Convenios Colectivos de Trabajo en Django

### Introducción

Un lunes cualquiera, el departamento de Recursos Humanos se encuentra revisando los partes horarios de la semana. Alguien trabajó 10 horas el 1º de mayo. Otra persona cumplió su turno de 8 a 17 el sábado. Algunos, incluso, trabajaron en el feriado gremial del 22 de abril. Cada uno de ellos pertenece a un sindicato distinto: UOCRA, SMATA y UTA. ¿Cómo se liquida todo esto sin errores?

En entornos laborales con pluralidad sindical, cada convenio colectivo de trabajo (CCT) impone sus propias reglas para clasificar las horas trabajadas: cuándo se considera hora extra, cuándo corresponde el 50%, cuándo el 100% y cuándo el temido 200% por laborar en un feriado nacional o gremial. Gestionar todo esto manualmente es no solo propenso a errores, sino también ineficiente y difícil de escalar.

Django, con su ORM y su estructura modular, ofrece una base ideal para estructurar lógicas sindicales complejas. En este artículo exploramos una arquitectura flexible que permite:

1. Centralizar las reglas de cada sindicato en módulos independientes.
2. Añadir nuevos convenios sin alterar los modelos existentes.
3. Ejecutar pruebas automatizadas para prevenir errores y regresiones.

### Modelado: Persona y Sindicato

Comenzamos con dos modelos fundamentales: `Persona` y `Sindicato`. Cada persona está vinculada a un sindicato a través de una `ForeignKey`, y es ese sindicato quien define cómo deben clasificarse sus horas.

```python
# empleados/models.py

class Persona(models.Model):
    nombre = models.CharField(max_length=100, default='')
    apellido = models.CharField(max_length=100, default='')
    dni = models.CharField(max_length=15, unique=True, default='')
    sindicato = models.ForeignKey("Sindicato", on_delete=models.SET_NULL, null=True, blank=True)
```

La lógica no debe estar en los modelos, sino separada. En `utils.py` definimos:

```python
# empleados/utils.py

from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from pathlib import Path
import json

FERIADOS_PATH = Path(__file__).resolve().parent / "ref" / "feriados.json"

def es_feriado(fecha: date) -> bool:
    try:
        with open(FERIADOS_PATH, "r", encoding="utf-8") as f:
            feriados = json.load(f)
        return fecha.strftime("%Y-%m-%d") in feriados
    except FileNotFoundError:
        return False

@dataclass
class ClasificacionHoras:
    total: float = 0.0
    normales: float = 0.0
    hs_50: float = 0.0
    hs_100: float = 0.0
    hs_200: float = 0.0
```

#### Lógicas sindicales

**¿Por qué separar cada sindicato en funciones y no en clases?**  

Intentar usar herencia de clases puede resultar caótico: cada cambio en un sindicato rompe otro. Al migrar a funciones independientes:  
- Pueden trabajar en reglas independientes sin tocar otras lógicas.  
- Los tests se ejecutan más rápido (sin herencia que mockear).  

Así implementamos SMATA:

```python
def clasificar_horas_smata(fecha, hora_entrada, hora_salida, es_feriado=False) -> ClasificacionHoras:
    entrada = datetime.combine(fecha, hora_entrada)
    salida = datetime.combine(fecha, hora_salida)
    if salida <= entrada:
        salida += timedelta(days=1)

    total_segundos = (salida - entrada).total_seconds()
    tramos = int(total_segundos // (15 * 60))

    horas = ClasificacionHoras()
    horas.total = round(total_segundos / 3600, 2)

    dia = entrada.weekday()
    tipo_excedente = "feriado" if es_feriado else ("50" if dia < 5 or (dia == 5 and entrada.time() < time(13, 0)) else "100")

    for i in range(tramos):
        if es_feriado:
            if i < 36:
                horas.hs_100 += 0.25
            else:
                horas.hs_200 += 0.25
        else:
            if i < 36:
                horas.normales += 0.25
            else:
                if tipo_excedente == "50":
                    horas.hs_50 += 0.25
                else:
                    horas.hs_100 += 0.25

    return horas
```

Y así la UOCRA:

```python
def clasificar_horas_uocra(fecha, hora_entrada, hora_salida, es_feriado=False) -> ClasificacionHoras:
    if fecha.month == 4 and fecha.day == 22:
        es_feriado = True

    entrada = datetime.combine(fecha, hora_entrada)
    salida = datetime.combine(fecha, hora_salida)
    if salida <= entrada:
        salida += timedelta(days=1)

    total_segundos = (salida - entrada).total_seconds()
    tramos = int(total_segundos // (15 * 60))

    horas = ClasificacionHoras()
    horas.total = round(total_segundos / 3600, 2)
    dia = entrada.weekday()
    tipo_excedente = "feriado" if es_feriado else ("50" if dia < 5 or (dia == 5 and entrada.time() < time(13, 0)) else "100")

    for i in range(tramos):
        if es_feriado:
            if i < 36:
                horas.hs_100 += 0.25
            else:
                horas.hs_200 += 0.25
        else:
            if i < 36:
                horas.normales += 0.25
            else:
                if tipo_excedente == "50":
                    horas.hs_50 += 0.25
                else:
                    horas.hs_100 += 0.25

    return horas
```

### Integración con modelos

```python
# empleados/models.py

from empleados.utils import clasificar_horas_smata, clasificar_horas_uocra

CLASIFICADORES = {
    "smata": clasificar_horas_smata,
    "uocra": clasificar_horas_uocra,
}

class Sindicato(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    def clasificar_horas(self, fecha, hora_entrada, hora_salida):
        clasificador = CLASIFICADORES.get(self.nombre.lower())
        if clasificador:
            return clasificador(fecha, hora_entrada, hora_salida)
        return ClasificacionHoras()

class Turno(models.Model):
    persona = models.ForeignKey("Persona", on_delete=models.CASCADE)
    inicio = models.DateTimeField()
    fin = models.DateTimeField()

    def clasificar(self):
        if not self.persona.sindicato:
            return ClasificacionHoras()
        return self.persona.sindicato.clasificar_horas(
            self.inicio.date(), self.inicio.time(), self.fin.time()
        )
```

De este modo, obtenemos un código limpio y escalable, en donde frente a nuevos convenios para gestionar, sólo debemos añadir la función correspondiente en `utils.py` y agregar un nuevo `CLASIFICADOR` al modelo. 

### Pruebas automatizadas

```python
# empleados/tests/test_clasificadores.py

from datetime import date, time
from django.test import TestCase
from empleados.utils import clasificar_horas_smata

class ClasificadorSmataTest(TestCase):
    def test_jornada_normal(self):
        resultado = clasificar_horas_smata(
            fecha=date(2024, 5, 13),
            hora_entrada=time(8, 0),
            hora_salida=time(17, 0),
            es_feriado=False
        )
        self.assertEqual(resultado.normales, 9.0)
        self.assertEqual(resultado.hs_50, 0.0)
        self.assertEqual(resultado.hs_100, 0.0)
        self.assertEqual(resultado.hs_200, 0.0)

    def test_excedente_diario(self):
        resultado = clasificar_horas_smata(
            fecha=date(2024, 5, 13),
            hora_entrada=time(8, 0),
            hora_salida=time(19, 0),
            es_feriado=False
        )
        self.assertEqual(resultado.normales, 9.0)
        self.assertEqual(resultado.hs_50, 2.0)

    def test_feriado_total(self):
        resultado = clasificar_horas_smata(
            fecha=date(2024, 5, 1),
            hora_entrada=time(8, 0),
            hora_salida=time(18, 0),
            es_feriado=True
        )
        self.assertEqual(resultado.hs_100, 9.0)
        self.assertEqual(resultado.hs_200, 1.0)
        self.assertEqual(resultado.normales, 0.0)
```

### Conclusión y siguientes pasos

El diseño presentado permite integrar reglas sindicales complejas y cambiantes dentro de una app Django sin comprometer la mantenibilidad. Mediante:

1. **Desacoplamiento inteligente**: las reglas están fuera de los modelos.
2. **Patrones flexibles**: la estrategia se basa en funciones intercambiables.
3. **Extensibilidad clara**: nuevos convenios requieren solo registrar una función.

Este enfoque permite:

- **Evitar sistemas propietarios caros.**
- **Responder a cambios sindicales con rapidez.**
- **Asegurar la calidad con tests automáticos.**

### Posibles mejoras:

- Modelar feriados en la base de datos relacional, en lugar de un archivo JSON. Esto permitiría gestionarlos por jurisdicción o año, y facilitar su actualización desde un panel administrativo.
- Las lógicas nocturnas o de turnos partidos ya están contempladas: cuando la hora de `entrada` es mayor que la hora de salida `salida`, se asume que el turno cruza medianoche y se ajusta con `salida += timedelta(days=1)`.
- Integrar con sistemas de fichaje mediante tarjetas RFID, marcadores biométricos u otras tecnologías de control horario.

Una arquitectura clara puede ahorrar miles en errores de liquidación. Y sobre todo: puede crecer con tu empresa.
