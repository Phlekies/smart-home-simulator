import { dataConnectionNames } from './editor/dataConnections';
import { linkStatusNames } from './linkStatus';
import type { Project } from './generated/project';
import type { AccessPointConnection } from './generated/simulation-result';

const endNames: Record<AccessPointConnection['ends_at'], string> = {
  gateway: 'Pasarela declarada',
  wired: 'Cable declarado, sin evaluar',
  unknown: 'Conexión desconocida',
  undefined: 'Conexión sin definir',
  loop: 'Bucle en el camino de datos',
};
const margin = (value: number | null) => value === null ? 'Sin datos' : `${value.toFixed(1)} dB`;

export default function AccessPointDiagnostics({ project, paths }: { project: Project; paths?: AccessPointConnection[] }) {
  if (!paths?.length) return null;
  const devices = new Map(project.devices.map(device => [device.id, device]));
  const name = (id: string) => devices.get(id)?.name || id;
  return <section className="connection-editor" aria-label="Diagnóstico de los caminos de datos">
    <h3>Camino de datos hasta el router principal</h3>
    <p>El margen de cada salto es el menor de ambos sentidos. La estimación deja sin comprobar los cables, la pasarela e Internet.</p>
    {paths.map(path => <details key={path.device_id} className="limitations">
      <summary>{name(path.device_id)} · {endNames[path.ends_at]}</summary>
      <p>Conexión inicial: {dataConnectionNames[path.kind]}. Último equipo del camino: {name(path.end_device_id)}.</p>
      {devices.get(path.device_id)?.data_connection?.note && <p>Nota del equipo: {devices.get(path.device_id)?.data_connection?.note}</p>}
      {path.hops.length > 0 && <>
        <p>Margen del salto más débil: <strong>{margin(path.weakest_margin_db)}</strong>.</p>
        <div className="table-scroll"><table>
          <caption>Saltos inalámbricos desde {name(path.device_id)}</caption>
          <thead><tr><th scope="col">Salto</th><th scope="col">Estado del enlace</th><th scope="col">Margen limitante</th></tr></thead>
          <tbody>{path.hops.map((hop, index) => <tr key={`${hop.link_id}-${index}`}>
            <th scope="row">{index + 1}. {name(hop.from_device_id)} → {name(hop.to_device_id)}</th>
            <td>{linkStatusNames[hop.status as keyof typeof linkStatusNames] ?? hop.status}</td>
            <td>{margin(hop.limiting_margin_db)}</td>
          </tr>)}</tbody>
        </table></div>
      </>}
      {path.reasons.length > 0 && <ul>{path.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>}
    </details>)}
  </section>;
}
