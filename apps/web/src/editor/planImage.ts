import { mapColor, metricNames } from './coverage';
import type { CoverageLayer } from './coverage';
import { exportSize, scaleBar } from './viewport';
import type { Bounds } from './viewport';

const format = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });
const number = (value: number) => format.format(value);

async function embedImage(image: SVGImageElement) {
  const href = image.getAttribute('href') ?? '';
  if (href.startsWith('data:image/')) return;
  if (!href.startsWith('blob:')) throw new Error('La imagen de referencia debe ser un archivo local.');
  const response = await fetch(href);
  if (!response.ok) throw new Error('La imagen local de referencia ya no está disponible.');
  const blob = await response.blob();
  const data = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('No se pudo leer la imagen local de referencia.'));
    reader.readAsDataURL(blob);
  });
  image.setAttribute('href', data);
}

export async function createPlanImage(svg: SVGSVGElement, bounds: Bounds, projectName: string, map: CoverageLayer | null, apName?: string) {
  const worldWidth = bounds.maxX - bounds.minX;
  const worldHeight = bounds.maxY - bounds.minY;
  const plot = exportSize(bounds);
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.removeAttribute('class');
  clone.setAttribute('viewBox', `${bounds.minX} ${bounds.minY} ${worldWidth} ${worldHeight}`);
  clone.setAttribute('width', String(plot.width));
  clone.setAttribute('height', String(plot.height));
  clone.querySelector('[data-plan-draft]')?.remove();
  const grid = clone.querySelector('.plan-background');
  for (const [key, value] of Object.entries({ x: bounds.minX, y: bounds.minY, width: worldWidth, height: worldHeight })) {
    grid?.setAttribute(key, String(value));
  }
  await Promise.all(Array.from(clone.querySelectorAll('image'), embedImage));

  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml;charset=utf-8' }));
  const picture = new Image();
  const margin = 32;
  const plotTop = 90;
  const legendTop = plotTop + plot.height;
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(960, plot.width) + margin * 2;
  canvas.height = legendTop + (map ? 232 : 68);
  const ctx = canvas.getContext('2d');
  if (!ctx) { URL.revokeObjectURL(url); throw new Error('El navegador no pudo dibujar la imagen.'); }
  try {
    picture.src = url;
    await picture.decode();
    const plotLeft = (canvas.width - plot.width) / 2;
    ctx.fillStyle = '#fafaf4';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#142221';
    ctx.fillRect(plotLeft, plotTop, plot.width, plot.height);
    ctx.drawImage(picture, plotLeft, plotTop, plot.width, plot.height);
  } finally {
    URL.revokeObjectURL(url);
  }

  const text = (line: string, x: number, y: number, font = '17px sans-serif') => {
    ctx.font = font;
    ctx.fillStyle = '#263a31';
    ctx.fillText(line, x, y, canvas.width - margin - x);
  };
  text(projectName, margin, 36, 'bold 26px sans-serif');
  text(`Plano en metros · X ${number(bounds.minX)} a ${number(bounds.maxX)} · Y ${number(bounds.minY)} a ${number(bounds.maxY)}`, margin, 67);

  const { metres, pixels } = scaleBar(bounds, plot);
  ctx.strokeStyle = '#263a31';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(margin, legendTop + 26);
  ctx.lineTo(margin + pixels, legendTop + 26);
  for (const x of [margin, margin + pixels]) {
    ctx.moveTo(x, legendTop + 19);
    ctx.lineTo(x, legendTop + 33);
  }
  ctx.stroke();
  text(`${number(metres)} m`, margin + pixels + 12, legendTop + 32);
  text('Y crece hacia abajo · cuadrícula de 1 m', margin + 270, legendTop + 32);

  if (map) {
    const { result, metric } = map;
    const { profile, grid, scenario, access_point_device_id, access_point_radio_id } = result.parameters;
    const isMargin = metric.includes('margin');
    const min = isMargin ? -30 : -100;
    const max = isMargin ? 40 : -30;
    const unit = isMargin ? 'dB' : 'dBm';
    text(`${metricNames[metric]} · ${unit}`, margin, legendTop + 62, 'bold 19px sans-serif');
    text(`AP ${apName ?? access_point_device_id} / ${access_point_radio_id} · perfil ${profile.name} / ${profile.radio.id}`, margin, legendTop + 87);
    text(`${number(result.frequency_hz / 1e6)} MHz · altura ${number(grid.height_m)} m · celdas de ${number(grid.resolution_m)} m · origen X ${number(grid.origin_x_m)}, Y ${number(grid.origin_y_m)} m`, margin, legendTop + 112);
    const gradient = ctx.createLinearGradient(margin, 0, margin + 220, 0);
    gradient.addColorStop(0, mapColor(min, metric));
    gradient.addColorStop(1, mapColor(max, metric));
    ctx.fillStyle = gradient;
    ctx.fillRect(margin, legendTop + 129, 220, 16);
    text(`≤ ${min} a ≥ ${max} ${unit} · escala fija`, margin + 234, legendTop + 143);
    text('Rayado: dato parcial · gris: métrica sin valor · gris oscuro: celda sin calcular', margin, legendTop + 174);
    text(`Estimación de trayecto directo sin calibración experimental${scenario ? ` · escenario ${scenario.name}` : ''}.`, margin, legendTop + 204);
  }
  const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/png'));
  if (!blob) throw new Error('El navegador no pudo generar el PNG.');
  return { blob, width: canvas.width, height: canvas.height };
}
