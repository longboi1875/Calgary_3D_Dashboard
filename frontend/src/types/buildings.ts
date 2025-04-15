/**
 * Building-related TypeScript types
 */

export interface Building {
  id: string;
  address: string;
  coordinates: number[][];
  height: number;
  assessedValue: number;
  landUse: string;
  yearBuilt: number;
}

export interface BuildingData {
  buildings: Building[];
  error?: string;
}

export interface BuildingsProps {
  onBuildingClick: (building: Building | null) => void;
  onBuildingHover: (building: Building | null) => void;
}

export interface BuildingGeometry {
  type: 'Polygon';
  coordinates: [number, number][];
}

export interface BuildingProperties {
  id: string;
  address: string;
  height: number;
  assessedValue: number;
  landUse: string;
  yearBuilt: number;
}

export interface BuildingFeature {
  type: 'Feature';
  geometry: {
    type: 'Polygon';
    coordinates: [number, number][][];
  };
  properties: {
    address: string;
    height?: number;
    assessed_value?: number;
    land_use?: string;
    year_built?: number;
  };
}

export interface BuildingCollection {
  type: 'FeatureCollection';
  features: BuildingFeature[];
} 