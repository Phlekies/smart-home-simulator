import type { DataConnection, Device, Link, Project } from '../generated/project.ts';

export type DataConnectionKind = DataConnection['kind'] | '';

export const dataConnectionNames: Record<DataConnection['kind'] | 'undefined', string> = {
  gateway: 'Pasarela (router principal)',
  wired: 'Por cable (declarada)',
  wireless: 'Inalámbrica',
  unknown: 'Desconocida',
  undefined: 'Sin definir',
};

export function showDataConnection(device: Device): boolean {
  return device.data_connection != null || ['access-point', 'controller', 'router', 'bridge'].includes(device.role);
}

function touchesDevice(link: Link, deviceId: string) {
  return link.source_device_id === deviceId || link.target_device_id === deviceId;
}

export function attachedDataLinks(project: Project, deviceId: string): Link[] {
  return project.links.filter(link => touchesDevice(link, deviceId));
}

export function validatedDataConnection(project: Project, deviceId: string, kind: DataConnectionKind,
  linkId: string, note: string): DataConnection | null {
  if (!kind) return null;
  if (kind === 'wireless' && !project.links.some(link => link.id === linkId && touchesDevice(link, deviceId))) {
    throw new Error('Selecciona un enlace inalámbrico que toque este equipo.');
  }
  const trimmed = note.trim();
  if (trimmed.length > 500) throw new Error('La nota admite hasta 500 caracteres.');
  return { kind, link_id: kind === 'wireless' ? linkId : null, note: trimmed || null };
}

export function clearDanglingDataConnections(draft: Project): void {
  const links = new Map(draft.links.map(link => [link.id, link]));
  for (const device of draft.devices) {
    const connection = device.data_connection;
    if (connection?.kind !== 'wireless') continue;
    const link = connection.link_id === null ? undefined : links.get(connection.link_id);
    if (!link || !touchesDevice(link, device.id)) {
      // The selection was removed by the same edit. Keep any note for the replacement path.
      device.data_connection = { kind: 'unknown', link_id: null, note: connection.note };
    }
  }
}
