# Clasificación de cobertura y criterio de fallo (B-139, B-140)

Decisiones U1 y U2 del 2026-11-09. El usuario las delegó en B: «responde tu U1 y U2 con los
criterios más realistas para una aplicación del estilo». Son **provisionales**: se revisan con el
piloto y se congelan antes de recoger datos de validación ([protocolo](PILOT_PROTOCOL.md)).
Código: `smart_environment/classification.py` y `LOW_TRAFFIC_CRITERION` en `measurements.py`.

## U1 — Cuándo falla un enlace de verdad

Es la prueba que decide, al medir, si un equipo funciona en su sitio. Sirve para validar las
predicciones; la aplicación no la ejecuta.

| Elemento | Valor | Por qué |
|---|---|---|
| Perfil | Sensor o actuador Wi-Fi de bajo tráfico | Es el caso principal del producto; cámaras y caudal quedan fuera |
| Método | Eco ICMP de ida y vuelta desde un equipo cableado al router | Una sola prueba recorre los dos sentidos del enlace inalámbrico |
| Equipo en el punto | El propio equipo, o un sustituto siempre encendido con la misma radio | Muchos sensores de batería duermen y no responden al eco |
| Volumen | ≥ 300 paquetes de 64 B, uno por segundo (5 minutos) | Abarca movimientos de personas y variaciones lentas; 100 paquetes en 20 s no |
| Falla si | Se entrega **menos del 95 %**, o el equipo no se asocia (0 respuestas) | Wi-Fi ya reintenta cada trama varias veces: perder más del 5 % extremo a extremo indica un enlace que falla de forma persistente y provoca reconexiones |

El RSSI se registra para calibrar, pero **nunca sustituye** esta prueba ([formato](MEASUREMENT_FORMAT.md)).
El umbral se revisa con el piloto. Si los equipos reales se reconectan solos con pérdidas
menores, se endurece (por ejemplo, al 98 %) antes de congelarlo.

## U2 — Reserva de diseño y las cuatro clases

**Margen limitante** = el menor de los dos sentidos. Cada sentido es la potencia recibida menos la
sensibilidad de ese receptor a la tasa que necesita el perfil. La **reserva de diseño es de 10 dB**.

| Clase | Regla | Qué significa para la persona |
|---|---|---|
| **Favorable** | Margen limitante ≥ 10 dB tal como está dibujado **y** en el peor caso de las hipótesis abiertas | Previsiblemente funciona, con holgura para lo que el modelo no ve |
| **Marginal** | Entre 0 y 10 dB, o ≥ 10 dB solo si se resuelven hipótesis (puerta desconocida, material incierto) | Puede funcionar, pero sin holgura: conviene mejorar la ubicación o comprobarlo |
| **Insuficiente** | Algún sentido por debajo de 0 dB, aunque el otro sea bueno o falte | Previsiblemente no funciona en esa ubicación |
| **Sin datos** | Falta potencia o sensibilidad, radios sin verificar o incompatibles, banda no soportada, posición fuera del modelo | No se puede concluir; se indica qué falta |

Por qué 10 dB:

- El estimador solo ve el trayecto directo. Muebles, personas, reflexiones y desvanecimiento
  cambian la señal varios dB entre posiciones cercanas, y nada de eso está en el modelo.
- Hay dispersión entre unidades del mismo equipo y su orientación es desconocida.
- El error del propio estimador sin calibrar es desconocido. La reserva lo cubre hasta que el
  piloto lo mida.
- Encaja con la práctica de diseño Wi-Fi. Las guías profesionales suelen apuntar a −67/−70 dBm en
  el cliente, unos 12–15 dB por encima del mínimo del estándar en MCS0 (−82 dBm). Un sensor de
  bajo tráfico necesita algo menos que voz o vídeo, y la sensibilidad mínima del estándar ya es
  prudente (los receptores reales suelen ser mejores).

Reglas de prudencia que acompañan a la clasificación:

- **Las puertas desconocidas no empeoran la clase.** El caso nominal ya las supone cerradas.
- **Un material con rango sí puede bajarla.** El peor caso usa su pérdida máxima. El motivo queda
  en `reasons` («con las hipótesis abiertas en su peor caso el margen limitante baja a …»).
- En el escenario «mejor caso», un enlace insuficiente puede salir favorable. Eso solo informa de
  qué cambio lo arreglaría; la clase del enlace no mejora.
- En un mapa, las celdas parciales o sin calcular son «sin datos», salvo que un sentido ya falle.
  Un mapa con radios sin verificar, o con el AP o la altura fuera de las paredes, queda entero sin
  datos.
- La cobertura, la compatibilidad de radio y el funcionamiento de la aplicación siguen separados:
  una clase favorable no dice nada del caudal de una cámara ni de la aplicación del fabricante.

## Requisito de enlace por perfil (B-140)

La tasa que necesita el equipo fija la sensibilidad con la que se calcula su margen
([perfiles](RADIO_PROFILES.md)):

| Perfil genérico | Requisito | Uso |
|---|---|---|
| `wifi4-ht20-mcs0` | Tasa más robusta (BPSK 1/2) | Sensores y actuadores de bajo tráfico; es el perfil del criterio U1 |
| `wifi4-ht20-mcs3` | 16-QAM 1/2 | Datos continuos sin vídeo; la cobertura no demuestra el caudal |
| `wifi4-ht20-mcs7` | 64-QAM 5/6 | Cobertura a la tasa más alta; en cámaras, el vídeo no se evalúa |

## En la API (cambio aditivo)

| Resultado | Campos nuevos (opcionales) |
|---|---|
| `SimulationResult` | `classification` (política); en cada enlace `coverage_class`, `limiting_margin_db`, `worst_case_limiting_margin_db` |
| `ScenarioResult` | `classification`; `coverage_class` por enlace y por escenario |
| `CoverageMapResult` | `classification`; `cells.coverage_class` y `coverage_class` de cada punto exacto |
| `PlacementSearchResult` | `coverage_class` de cada equipo evaluado, bajo el escenario de la búsqueda |
| `InstallationReport` | `classification`, `coverage_class` por enlace, recuentos por clase y celdas por clase de cada mapa |

`classification` incluye la reserva, la regla, el criterio U1 y `calibrated: false`. Los
consumidores existentes no cambian. Mostrar las clases es trabajo de A (A1/A2).

## Revisión y congelación

1. **Piloto (P0/P4):** medir el residuo predicción − medida y aplicar U1 en cada punto.
2. **Ajuste:** la reserva pasa a ser el valor que deja como máximo un 5 % de falsos favorables en
   los datos de calibración, y nunca menos de 6 dB.
3. **Congelación:** antes de la validación, la campaña fija su criterio (`frozen_on`) y la reserva
   pasa a `calibrated: true` con versión nueva (`coverage-class-v2`).
4. **Validación:** falsos favorables, abstenciones y error por tipo de vivienda, en viviendas
   independientes. Si no se cumplen los objetivos congelados, se limita el ámbito ofrecido.

Nada de esto convierte la predicción en garantía. El informe y la interfaz deben seguir diciendo
que la clasificación es una predicción sin calibrar.
