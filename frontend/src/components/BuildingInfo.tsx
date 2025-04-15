import React from 'react';

interface Building {
  address: string;
  height?: number;
  assessedValue?: number;
  landUse?: string;
  yearBuilt?: number;
}

interface BuildingInfoProps {
  building: Building | null;
  onClose: () => void;
}

const BuildingInfo: React.FC<BuildingInfoProps> = ({ building, onClose }) => {
  if (!building) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
        maxWidth: '300px',
        zIndex: 1000,
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          border: 'none',
          background: 'none',
          cursor: 'pointer',
          fontSize: '16px',
        }}
      >
        ×
      </button>
      <h3 style={{ marginTop: 0, marginBottom: '15px' }}>Building Information</h3>
      <div style={{ marginTop: '15px' }}>
        <div style={{ marginBottom: '10px' }}>
          <strong>Address:</strong> {building.address}
        </div>
        {building.height !== undefined && (
          <div style={{ marginBottom: '10px' }}>
            <strong>Height:</strong> {building.height.toFixed(2)}m
          </div>
        )}
        {building.assessedValue !== undefined && (
          <div style={{ marginBottom: '10px' }}>
            <strong>Assessed Value:</strong> ${building.assessedValue.toLocaleString()}
          </div>
        )}
        {building.landUse && (
          <div style={{ marginBottom: '10px' }}>
            <strong>Land Use:</strong> {building.landUse}
          </div>
        )}
        {building.yearBuilt !== undefined && (
          <div style={{ marginBottom: '10px' }}>
            <strong>Year Built:</strong> {building.yearBuilt}
          </div>
        )}
      </div>
    </div>
  );
};

export default BuildingInfo; 