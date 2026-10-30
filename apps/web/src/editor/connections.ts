import type { Device, Link, Project, Radio } from '../generated/project.ts';

export const MAX_RADIOS = 8;
export const MAX_LINKS = 512;

function identifier(id: string) {
  if (!id.length || id.length > 120) throw new Error('El identificador debe tener entre 1 y 120 caracteres.');
}
function deviceIn(project: Project, id: string) {
  const device = project.devices.find(device => device.id === id);
  if (!device) throw new Error('El equipo ya no existe en el proyecto.');
  return device;
}
function radioIn(project: Project, deviceId: string, radioId: string) {
  const device = deviceIn(project, deviceId);
  if (!device.radios.some(radio => radio.id === radioId)) throw new Error('La radio seleccionada ya no existe en ese equipo.');
  return device;
}
export function genericRadio(id: string): Radio {
  identifier(id);
  return { id, protocol: 'unknown', frequency_hz: 2.412e9, bandwidth_hz: 20e6, channel: null,
    tx_power_dbm: null, sensitivity_dbm: null, tx_gain_dbi: 0, rx_gain_dbi: 0, noise_figure_db: 7,
    antenna: 'omnidirectional', orientation_deg: 0, beamwidth_deg: 360, pattern_sharpness: 1.8,
    side_lobe_attenuation_db: 18, polarization_deg: 0 };
}
export function withAddedRadio(project: Project, deviceId: string, id: string): Project {
  const device = deviceIn(project, deviceId);
  if (device.radios.length >= MAX_RADIOS) throw new Error('Cada equipo admite como máximo 8 radios.');
  if (device.radios.some(radio => radio.id === id)) throw new Error('Ese identificador de radio ya existe en el equipo.');
  const radio = genericRadio(id);
  const next = structuredClone(project); deviceIn(next, deviceId).radios.push(radio);
  return next;
}
export function linksUsingRadio(project: Project, deviceId: string, radioId: string) {
  return project.links.filter(link => (link.source_device_id === deviceId && link.source_radio_id === radioId)
    || (link.target_device_id === deviceId && link.target_radio_id === radioId));
}
export function withRemovedRadio(project: Project, deviceId: string, radioId: string): Project {
  const device = radioIn(project, deviceId, radioId);
  if (device.radios.length <= 1) throw new Error('Conserva al menos una radio por equipo. Puedes eliminar el equipo completo si ya no lo necesitas.');
  const next = structuredClone(project);
  const target = deviceIn(next, deviceId);
  // The existence/minimum/maximum guards preserve the generated 1..8 tuple constraint.
  target.radios = target.radios.filter(radio => radio.id !== radioId) as Device['radios'];
  const ids = new Set(linksUsingRadio(project, deviceId, radioId).map(link => link.id));
  next.links = next.links.filter(link => !ids.has(link.id));
  return next;
}

export function hasRadioConnection(project: Project, candidate: Omit<Link, 'id'>): boolean {
  return project.links.some(link => (link.source_device_id === candidate.source_device_id && link.source_radio_id === candidate.source_radio_id
    && link.target_device_id === candidate.target_device_id && link.target_radio_id === candidate.target_radio_id)
    || (link.source_device_id === candidate.target_device_id && link.source_radio_id === candidate.target_radio_id
    && link.target_device_id === candidate.source_device_id && link.target_radio_id === candidate.source_radio_id));
}
export function withAddedConnection(project: Project, link: Link): Project {
  identifier(link.id);
  if (project.links.length >= MAX_LINKS) throw new Error('El proyecto admite como máximo 512 enlaces.');
  if (project.links.some(existing => existing.id === link.id)) throw new Error('Ese identificador de enlace ya existe.');
  if (link.source_device_id === link.target_device_id) throw new Error('Elige una radio de otro equipo; no se admiten enlaces al mismo equipo.');
  radioIn(project, link.source_device_id, link.source_radio_id);
  radioIn(project, link.target_device_id, link.target_radio_id);
  if (hasRadioConnection(project, link)) throw new Error('Estas dos radios ya están enlazadas. Cada enlace se evalúa en ambos sentidos.');
  const next = structuredClone(project); next.links.push({ ...link }); return next;
}
export function withRemovedConnection(project: Project, id: string): Project {
  if (!project.links.some(link => link.id === id)) throw new Error('El enlace ya no existe en el proyecto.');
  const next = structuredClone(project); next.links = next.links.filter(link => link.id !== id); return next;
}
