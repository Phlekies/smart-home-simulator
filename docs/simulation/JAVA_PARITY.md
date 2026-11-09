# Paridad con Java: antenas, polarización y contraste multipath (B-121)

Versión 1 · 2026-11-01. Arnés: `services/simulator/benchmarks/java_parity.py` y
`java_parity/JavaParity.java`. Evidencia: [`evidence/java-parity.json`](evidence/java-parity.json).
Pruebas sin JDK: `services/simulator/tests/test_java_parity.py`.

## Cómo se obtuvo

El script compila en un directorio temporal los paquetes `model`, `physics` y `simulation` del
código Java original, junto con el arnés. Deja fuera las clases que dependen de la interfaz
(`LinkValidator`). Después ejecuta `PropagationEngine.computeCell`. Desde ADR-009, las fuentes se
extraen de la etiqueta `java-desktop-final` (`--java-ref`), porque Java ya no está en `main`; el 2026-11-09 la
ejecución desde la etiqueta reprodujo exactamente los mismos valores. **El código Java no se
modifica** y no se instala ni se descarga nada.

- **Entorno:** Java 22.0.2 en Windows 11 y Python 3.13.
- **Fuentes Java:** commit `7e016cd`.
- **Fecha:** 2026-11-01.

```powershell
.venv/Scripts/python.exe services/simulator/benchmarks/java_parity.py --output docs/simulation/evidence/java-parity.json
```

Las pruebas de `pytest` vuelven a calcular el lado Python a partir de los casos guardados. Así,
cualquier cambio del estimador o de la importación aparece sin necesidad de Java.

## Paridad del trayecto directo (antenas y polarización)

En modo directo Java no tiene reflexiones, difracción, difusión, desvanecimiento ni umbral de
descarte. Se probaron 76 sondas:

| Grupo | Qué cubre |
|---|---|
| `pattern-0…3` | Haz `cos^k` de 30–120°, nitidez 1–4, lóbulos laterales de 10–25 dB y orientaciones 0°, 45°, −30° y 200°, en 14 direcciones (dentro, en el borde y fuera del haz) |
| `polarization-*` | Polarizaciones de 0, 30, 60, 89, 90 y 135° frente a un receptor de 0 y 90°, incluido el tope de 26 dB del desajuste cruzado |
| `walls-2400MHz`, `walls-5200MHz` | Ladrillo y hormigón con grosor, pérdida por metro, ganancia del sistema, exponente 2.6, antena directiva y polarización de 45° frente a 15° |

**Resultado: diferencia máxima de 0.0022 dB.** Se debe a que Java usa la constante redondeada
32.45 dB en la pérdida en espacio libre. La tolerancia de las pruebas es de 0.01 dB. La importación
conserva todos los campos de antena y polarización de los sensores y la ganancia y polarización del
hub (prueba con el ejemplo de apartamento, que tiene un sensor direccional).

Diferencias de modelo explicadas y que se mantienen:
- **Diagrama del receptor.** Java aplica el diagrama de antena solo al emisor (sensor); el receptor
  (hub) es una ganancia escalar. El estimador aplica a cada radio su propio diagrama en ambos
  sentidos. Con receptor omnidireccional, como en los ejemplos Java, ambos coinciden.
- **Alturas.** Java es 2D. La importación da 1.4 m a los sensores y 1.3 m al hub. En los ejemplos,
  esa diferencia vertical cambia la potencia menos de 0.01 dB.
- **Suelo numérico.** Java no informa potencias inferiores a −150 dBm. El estimador sí las calcula
  (por ejemplo, −152.8 dBm en el sensor S4 del almacén).

## Contraste con el motor multipath de Java

Para cada sensor de los tres ejemplos se calculó la señal en el hub con los ajustes del ejemplo:
reflexiones, difracción y difusión activas, y umbral de descarte de −115 dBm. Se usaron los dos
modos de Java, rayos (suma incoherente) y ondas (suma coherente), y se compararon con el trayecto
directo. Es una comparación **entre modelos**: ninguno está validado con medidas.

| Ejemplo | Enlaces comparables | Rayos − directo (dB) | Ondas − directo (dB) |
|---|---|---|---|
| Apartamento | 6 de 6 | +1.2 a +3.6 (media +2.5) | −7.0 a +4.4 (media −0.8) |
| Oficina | 7 de 7 | +0.3 a +2.4 (media +1.4) | −5.8 a +3.9 (media −0.1) |
| Almacén | 3 de 5 | +2.3 a +32.6 (media +18.0) | +6.2 a +33.2 (media +20.3) |

Interpretación:
- **Viviendas y oficinas:** las contribuciones adicionales suman 0.3–3.6 dB en potencia
  incoherente. En suma coherente, la interferencia entre trayectos mueve el valor ±7 dB según la
  posición exacta, un efecto de tipo desvanecimiento que el estimador directo no representa.
- **Almacén:** cuando el trayecto directo atraviesa varios obstáculos metálicos o de hormigón, Java
  encuentra rutas alrededor por reflexión o difracción hasta 33 dB más fuertes. En espacios así,
  **el estimador directo puede subestimar mucho la señal**, y su resultado no debe leerse como una
  cota garantizada en ningún sentido.
- **Enlaces no comparables (2):**
  - S3: su trayecto directo (−132 dBm) queda por debajo del umbral de descarte de Java, que no
    devuelve ninguna contribución.
  - S4: su valor está bajo el suelo de −150 dBm.

  En ellos no se declara ninguna diferencia.

## Qué cierra y qué no

- Cierra la conversión pendiente de antenas direccionales y polarizaciones (checklist técnico) y
  explica las diferencias con el motor multipath Java.
- No valida ningún motor. La precisión frente a medidas sigue pendiente de P4. La traducción de
  antenas al motor avanzado (Sionna) sigue pendiente de M3.
