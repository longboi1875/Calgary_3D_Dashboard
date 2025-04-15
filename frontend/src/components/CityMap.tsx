import React, { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import Buildings from './Buildings';
import BuildingInfo from './BuildingInfo';
import { Building } from '../types/buildings';

const CityMap: React.FC = () => {
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [hoveredBuilding, setHoveredBuilding] = useState<Building | null>(null);

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative' }}>
      <Canvas
        camera={{
          position: [0, 1000, 1000],
          fov: 60,
          near: 1,
          far: 10000
        }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        
        <Buildings
          onBuildingClick={setSelectedBuilding}
          onBuildingHover={setHoveredBuilding}
        />
        
        <Grid
          args={[1000, 1000]}
          cellSize={50}
          cellThickness={1}
          cellColor="#6f6f6f"
          sectionSize={100}
          fadeDistance={1000}
          fadeStrength={1}
          followCamera={false}
        />
        
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          target={[0, 0, 0]}
        />
      </Canvas>

      {hoveredBuilding && !selectedBuilding && (
        <div
          style={{
            position: 'absolute',
            left: '16px',
            bottom: '16px',
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '8px',
            borderRadius: '4px',
            pointerEvents: 'none'
          }}
        >
          {hoveredBuilding.address}
        </div>
      )}

      {selectedBuilding && (
        <BuildingInfo
          building={selectedBuilding}
          onClose={() => setSelectedBuilding(null)}
        />
      )}
    </div>
  );
};

export default CityMap; 