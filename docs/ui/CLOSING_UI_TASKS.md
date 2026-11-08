# Interfaz para cerrar la migración (A-114…A-119)

2026-11-08. Hechas por la sesión de B en el papel de A, por instrucción del usuario, de forma secuencial y
documentada ([AGENT_A](../process/AGENT_A.md)). Verificadas en el navegador integrado sobre la web compilada
servida por `python -m smart_environment.serve` (B-128), con el apartamento de ejemplo.

| Tarea | Qué hace | Verificación |
|---|---|---|
| A-114 · Mapas guardables | **Guardar mapa** descarga el resultado como JSON local. **Abrir mapa guardado** lo valida (`editor/savedMap.ts`) y pide la huella del proyecto (`/api/projects/fingerprint`, B-132). Solo se dibuja si coinciden la huella y la versión del motor; si no, lo indica como obsoleto. Editar el proyecto lo retira, como un mapa calculado | Mapa de 88 × 62 celdas guardado (383 KB). Al reabrirlo: «Mapa guardado vigente» y capa dibujada. Con la huella alterada: «Mapa guardado obsoleto… No se dibuja». `savedMap.test.ts` |
| A-115 · Informe | **Descargar informe** pide `/api/reports/markdown` con el mapa visible, si lo hay, y lo guarda como `informe-instalacion.md` | Informe de 7.5 KB con «Mapas de cobertura», «no un porcentaje de cobertura» y «Nivel de evidencia» (B-135); sin mapa visible, sin esa sección |
| A-116 · Zoom y desplazamiento | Botones «＋», «－» y «Ver todo»; Ctrl+rueda acerca alrededor del puntero; con el plano enfocado, `+`, `-` y `0` y las flechas desplazan. Arrastrar el fondo con Seleccionar, o el botón central, desplaza. La vista nunca sale del plano (`editor/viewport.ts`) | Zoom ×1.5: ancho visible de 47.6 a 31.7 m. Flecha → desplaza 3.17 m. Arrastre del fondo hasta el borde, sin modificar el proyecto. Con zoom, arrastrar un equipo lo mueve (deshacer correcto). `viewport.test.ts` |
| A-117 · Exportar imagen | **Exportar imagen** dibuja el plano completo en PNG (lado largo 1600 px), con fondo, mapa visible, imagen de referencia incrustada y una leyenda «estimación de trayecto directo sin calibrar» | PNG de 1600 × 1163 px y 159 KB, con píxeles de paredes, equipos, enlaces y etiquetas |
| A-118 · Accesibilidad y recorrido | «Recorrido para describir tu vivienda»: seis pasos derivados del proyecto (paredes, equipos, radios completas, enlaces, estimación, guardado), con su estado y una acción por paso (`editor/onboarding.ts`). Foco visible en el propio plano, nombres e instrucciones de teclado en los controles nuevos | Revisión en el navegador: ningún botón sin nombre, todos los campos con etiqueta, ninguna imagen sin texto alternativo, sin tabulación positiva, 8 regiones de avisos y `lang="es"`. «Ejecutar» desde el recorrido calcula y marca el paso. `onboarding.test.ts` |
| A-119 · Predicción frente a compra | Texto bajo los resultados: «Sobre umbral» es un margen positivo sin calibrar, no garantiza la conexión ni es una recomendación de compra. Pie de página y avisos del informe en la misma línea | Revisión de todos los textos de la interfaz: ninguno recomienda comprar; las menciones existentes lo niegan |

## Fallo de integración corregido

Al calcular un mapa apareció «El mapa recibido pertenece a otros parámetros», y la búsqueda de ubicación tenía
el mismo problema. B-113, B-114, B-119 y B-134 añadieron campos opcionales al contrato con valor `null` por
defecto, y la API los devuelve en los parámetros. La interfaz comparaba esos parámetros exactamente con su
petición, que no los incluye. Las validaciones usan ahora `editor/echo.ts`: una clave ausente equivale a `null`
y cualquier valor real distinto se sigue rechazando. Hay pruebas de regresión en `coverage.test.ts` y
`placement.test.ts`. Después del arreglo, el mapa (88 × 62 celdas) y la búsqueda funcionan en el navegador.

Ni las pruebas de B ni las de la web podían detectarlo, porque ninguna cubre la interfaz frente a la API real.
Los recorridos E2E de B-127 e I-007 no calcularon mapas.

## Comandos

`npm test` (131), `npm run build` (`tsc --noEmit` + vite), `npm run contracts` sin deriva (incluye
`project-fingerprint.ts`), `pytest` (444).
