import React, { useEffect, useState } from 'react';
import { Shape, ExtrudeGeometry } from 'three';
import { Building, BuildingsProps } from '../types/buildings';

const Buildings: React.FC<BuildingsProps> = ({ onBuildingClick, onBuildingHover }) => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBuildings = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/buildings');
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
          return;
        }
        
        setBuildings(data.buildings);
      } catch (err) {
        setError('Failed to fetch building data');
        console.error('Error fetching buildings:', err);
      }
    };

    fetchBuildings();
  }, []);

  const createBuildingShape = (coordinates: number[][]): Shape | null => {
    try {
      const shape = new Shape();
      
      // Convert coordinates to local space
      const centerLat = 51.0475;
      const centerLng = -114.06;
      const scale = 100000;
      
      const localCoords = coordinates.map(([lng, lat]) => [
        (lng - centerLng) * scale,
        (lat - centerLat) * scale
      ]);
      
      if (localCoords.length < 3) return null;
      
      shape.moveTo(localCoords[0][0], localCoords[0][1]);
      for (let i = 1; i < localCoords.length; i++) {
        shape.lineTo(localCoords[i][0], localCoords[i][1]);
      }
      shape.lineTo(localCoords[0][0], localCoords[0][1]);
      
      return shape;
    } catch (err) {
      console.error('Error creating building shape:', err);
      return null;
    }
  };

  if (error) {
    console.error('Error in Buildings component:', error);
    return null;
  }

  return (
    <group>
      {buildings.map((building) => {
        const shape = createBuildingShape(building.coordinates);
        if (!shape) return null;

        const geometry = new ExtrudeGeometry(shape, {
          depth: building.height || 10,
          bevelEnabled: false
        });

        return (
          <mesh
            key={building.id}
            geometry={geometry}
            onPointerOver={() => onBuildingHover(building)}
            onPointerOut={() => onBuildingHover(null)}
            onClick={() => onBuildingClick(building)}
          >
            <meshStandardMaterial 
              color="#4a90e2"
              transparent
              opacity={0.8}
            />
          </mesh>
        );
      })}
    </group>
  );
};

export default Buildings; 