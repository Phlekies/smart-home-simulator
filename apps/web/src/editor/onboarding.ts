import type { Project } from '../generated/project.ts';

export type StepId = 'walls' | 'devices' | 'radios' | 'links' | 'estimate' | 'save';
export type CreationStep = { id: StepId; title: string; done: boolean; detail: string };

/** Progress of the guided path to describe a home, derived from the project only (A-118). */
export function creationSteps(project: Project, estimated: boolean, saved: boolean): CreationStep[] {
  const walls = project.building.walls.length;
  const devices = project.devices.length;
  const linkedRadios = project.links.flatMap(link => [[link.source_device_id, link.source_radio_id], [link.target_device_id, link.target_radio_id]]);
  const radios = [...new Set(linkedRadios.map(pair => JSON.stringify(pair)))].map(text => JSON.parse(text) as [string, string])
    .map(([deviceId, radioId]) => project.devices.find(d => d.id === deviceId)?.radios.find(r => r.id === radioId))
    .filter(radio => radio !== undefined);
  const incomplete = radios.filter(radio => radio.tx_power_dbm === null || radio.sensitivity_dbm === null || radio.protocol === 'unknown' || radio.channel === null).length;
  return [
    { id: 'walls', title: 'Dibuja las paredes', done: walls > 4,
      detail: walls > 4 ? `${walls} paredes` : 'Solo el contorno: añade tabiques y muros, con su material y grosor.' },
    { id: 'devices', title: 'Coloca los equipos', done: devices >= 2,
      detail: devices >= 2 ? `${devices} equipos` : 'Añade al menos el router o AP y un equipo, a su altura real.' },
    { id: 'radios', title: 'Completa sus radios', done: radios.length > 0 && incomplete === 0,
      detail: radios.length === 0 ? 'Primero enlaza equipos.' : incomplete === 0 ? 'Protocolo, canal, potencia y sensibilidad indicados'
        : `${incomplete} ${incomplete === 1 ? 'radio enlazada' : 'radios enlazadas'} con datos sin indicar: el resultado quedará «sin verificar».` },
    { id: 'links', title: 'Enlaza lo que quieres comprobar', done: project.links.length > 0,
      detail: project.links.length ? `${project.links.length} enlaces` : 'Cada enlace se evalúa en ambos sentidos.' },
    { id: 'estimate', title: 'Ejecuta la estimación', done: estimated,
      detail: estimated ? 'Resultados vigentes' : 'Calcula de nuevo tras cada cambio.' },
    { id: 'save', title: 'Guarda el proyecto', done: saved,
      detail: saved ? 'Guardado en JSON en esta sesión' : 'La copia local no sustituye a un archivo JSON.' },
  ];
}
