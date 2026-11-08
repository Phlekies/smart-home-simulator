import { Canvas } from '@react-three/fiber';
import { Bounds, OrbitControls } from '@react-three/drei';
import type { Project } from './generated/project';

export default function Scene3D({ project, selected, onSelect, selectedWallId, onSelectWall }: {
  project: Project; selected: string; onSelect: (id: string) => void;
  selectedWallId: string | null; onSelectWall: (id: string) => void;
}) {
  return <Canvas camera={{ position: [35, 38, 45], fov: 42 }} dpr={[1, 1.5]}>
    <color attach="background" args={['#142221']} />
    <ambientLight intensity={1.5} />
    <directionalLight position={[15, 30, 8]} intensity={2} />
    <Bounds fit clip observe margin={1.15}>
      <group>
        <mesh rotation-x={-Math.PI / 2} position={[project.building.width_m / 2, -.04, project.building.depth_m / 2]}>
          <planeGeometry args={[project.building.width_m, project.building.depth_m]} />
          <meshStandardMaterial color="#203c37" />
        </mesh>
        {project.building.walls.map(w => {
          const dx = w.end.x - w.start.x, dy = w.end.y - w.start.y;
          return <mesh key={w.id} position={[(w.start.x + w.end.x) / 2, w.start.z + w.height_m / 2,
            (w.start.y + w.end.y) / 2]} rotation-y={-Math.atan2(dy, dx)}
            onClick={event => { event.stopPropagation(); onSelectWall(w.id); }}>
            <boxGeometry args={[Math.hypot(dx, dy), w.height_m, w.thickness_m]} />
            <meshStandardMaterial color={selectedWallId === w.id ? '#f3b26f' : w.door === 'unknown' ? '#ceaeef' : w.door === 'open' ? '#82d6c8' : '#92a69a'}
              transparent opacity={w.door === 'open' ? .12 : .7} roughness={.8} />
          </mesh>;
        })}
        {project.devices.map(d => <mesh key={d.id} position={[d.position.x, d.position.z, d.position.y]}
          onClick={event => { event.stopPropagation(); onSelect(d.id); }}>
          {d.role === 'controller' || d.role === 'access-point'
            ? <boxGeometry args={[.6, .6, .6]} /> : <sphereGeometry args={[.32, 20, 20]} />}
          <meshStandardMaterial color={selected === d.id ? '#ffffff' : d.role === 'controller' ? '#f3b26f' : '#79d9b2'}
            emissive={selected === d.id ? '#79d9b2' : '#000000'} emissiveIntensity={.4} />
        </mesh>)}
      </group>
    </Bounds>
    <OrbitControls makeDefault maxPolarAngle={Math.PI / 2.05} />
  </Canvas>;
}
