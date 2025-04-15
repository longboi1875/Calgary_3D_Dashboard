import React, { useState, useEffect, useCallback } from 'react';
import DeckGL from '@deck.gl/react';
import { Map } from 'react-map-gl/maplibre';
import { GeoJsonLayer } from '@deck.gl/layers';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './App.css'; // Import App.css for panel styling

// --- Constants ---
const MAPTILER_API_KEY = 'xNucgqob58FS7cn7XeAy'; 

// Define Map Style Options
const mapStyles = {
  streets: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_API_KEY}`,
  satellite: `https://api.maptiler.com/maps/satellite/style.json?key=${MAPTILER_API_KEY}`,
  basic: `https://api.maptiler.com/maps/basic-v2/style.json?key=${MAPTILER_API_KEY}`,
  outdoor: `https://api.maptiler.com/maps/outdoor-v2/style.json?key=${MAPTILER_API_KEY}`,

};
const DEFAULT_MAP_STYLE_KEY = 'streets';

const BACKEND_URL = 'http://127.0.0.1:5000/api/buildings'; 
const FILTER_BACKEND_URL = 'http://127.0.0.1:5000/api/filter_buildings'; 

// Downtown Calgary Coordinates
const INITIAL_VIEW_STATE = {
  longitude: -114.065, // Centered within the backend bbox
  latitude: 51.0475,   // Centered within the backend bbox
  zoom: 15.5,          // Zoom level to see a few blocks
  pitch: 60,           // Angle for 3D view
  bearing: 0
};

// Helper function to format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
};

// --- App Component ---
function App() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [buildingData, setBuildingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filtering, setFiltering] = useState(false);
  const [error, setError] = useState(null);
  const [selectedBuildingInfo, setSelectedBuildingInfo] = useState(null);
  const [filterQuery, setFilterQuery] = useState('');
  const [currentMapStyle, setCurrentMapStyle] = useState(mapStyles[DEFAULT_MAP_STYLE_KEY]); // State for map style

  // --- Data Fetching Functions ---
  const fetchBuildingData = useCallback((url, queryParams = null) => {
    const isFiltering = url === FILTER_BACKEND_URL;
    if (isFiltering) {
      setFiltering(true);
    } else {
      setLoading(true);
    }
    setError(null);

    let fetchUrl = url;
    if (queryParams) {
      fetchUrl += `?${new URLSearchParams(queryParams).toString()}`;
    }

    console.log(`Fetching from: ${fetchUrl}`);

    fetch(fetchUrl)
      .then(response => {
        if (!response.ok) {
          return response.json().then(errData => {
            throw new Error(errData.error || `HTTP error! status: ${response.status}`);
          }).catch(() => {
             throw new Error(`HTTP error! status: ${response.status}`);
          });
        }
        return response.json();
      })
      .then(data => {
        console.log("Data fetched successfully:", data);
        if (data && data.type === 'FeatureCollection') {
          setBuildingData(data);
          if (data.features.length === 0) {
             console.warn("Received empty FeatureCollection.");
          }
        } else if (data && data.message && data.data && data.data.length === 0) {
          console.warn("No buildings matched the filter criteria.");
          setBuildingData({ type: "FeatureCollection", features: [] });
        } else {
          console.warn("Received non-GeoJSON data or unexpected format, setting to empty:", data);
          setBuildingData({ type: "FeatureCollection", features: [] });
        }
      })
      .catch(fetchError => {
        console.error("Error fetching building data:", fetchError);
        setError(fetchError.message);
        setBuildingData(null);
      })
      .finally(() => {
        if (isFiltering) {
          setFiltering(false);
        } else {
          setLoading(false);
        }
      });
  }, []);

  useEffect(() => {
    fetchBuildingData(BACKEND_URL);
  }, [fetchBuildingData]);

  // --- Event Handlers ---
  const handleCloseInfoPanel = () => {
    setSelectedBuildingInfo(null);
  };

  const handleDeckClick = (info, event) => {
    if (info.object) {
      console.log('Clicked on building:', info.object.properties);
      setSelectedBuildingInfo(info.object.properties);
    } else {
      handleCloseInfoPanel();
    }
  };

  const handleFilterInputChange = (event) => {
    setFilterQuery(event.target.value);
  };

  const handleFilterSubmit = (event) => {
    event.preventDefault();
    if (!filterQuery.trim()) return;
    fetchBuildingData(FILTER_BACKEND_URL, { query: filterQuery });
  };

  const handleResetFilter = () => {
    setFilterQuery('');
    fetchBuildingData(BACKEND_URL);
  };

  const handleMapStyleChange = (event) => {
    const styleKey = event.target.value;
    setCurrentMapStyle(mapStyles[styleKey]);
  };

  // --- Layers ---
  const layers = [
    buildingData && new GeoJsonLayer({
      id: 'buildings-layer',
      data: buildingData,
      filled: true,
      wireframe: true,
      extruded: true,
      getPolygon: feature => feature.geometry.coordinates,
      getFillColor: [160, 160, 180, 200],
      getLineColor: [80, 80, 80],
      getElevation: feature => feature.properties.height || 0,
      pickable: true,
      autoHighlight: true,
      highlightColor: [255, 255, 0, 200],
    })
  ].filter(Boolean);

  // --- Render ---
  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>Error fetching data: {error}</div>;
  }

  return (
    <div className="app-container">
      <div className="controls">
        <input
          type="text"
          placeholder="Filter buildings (e.g., height > 150m)"
          value={filterQuery}
          onChange={handleFilterInputChange}
          disabled={loading || filtering}
        />
        <button onClick={handleFilterSubmit} disabled={loading || filtering || !filterQuery.trim()}>
          {filtering ? 'Filtering...' : 'Filter'}
        </button>
        <button onClick={handleResetFilter} disabled={loading || filtering}>
          Reset Filter
        </button>
        <select 
          className="map-style-select"
          onChange={handleMapStyleChange} 
          defaultValue={DEFAULT_MAP_STYLE_KEY}
          disabled={loading || filtering}
        >
          <option value="streets">Streets</option>
          <option value="satellite">Satellite</option>
          <option value="basic">Basic</option>
          <option value="outdoor">Outdoor</option>
          {/* <option value="toner">Toner</option> */}
        </select>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      <DeckGL
        layers={layers}
        initialViewState={viewState}
        controller={true}
        onViewStateChange={e => setViewState(e.viewState)}
        getTooltip={({object}) => object && (
          `Building ID: ${object.properties.struct_id || 'N/A'}
` +
          `Height: ${object.properties.height ? object.properties.height.toFixed(2) + 'm' : 'N/A'}`
        )}
        onClick={handleDeckClick}
      >
        <Map
          mapLib={maplibregl}
          mapStyle={currentMapStyle}
          preventStyleDiffing={true}
        />

        {(loading || filtering) && (
          <div className="loading-indicator">
            {loading ? 'Loading Building Data...' : 'Applying Filter...'}
          </div>
        )}

        {selectedBuildingInfo && (
          <div className="info-panel">
            <button className="close-button" onClick={handleCloseInfoPanel}>×</button>
            <h3>Building Information</h3>
            <p><strong>Address:</strong> {selectedBuildingInfo.address || 'N/A'}</p>
            <p><strong>Height:</strong> {selectedBuildingInfo.height ? `${selectedBuildingInfo.height.toFixed(2)} m` : 'N/A'}</p>
            <p><strong>Assessed Value:</strong> {formatCurrency(selectedBuildingInfo.assessed_value)}</p>
            <p><strong>Land Use:</strong> {selectedBuildingInfo.land_use_designation || 'N/A'}</p>
            <p><strong>Year Built:</strong> {selectedBuildingInfo.year_of_construction || 'N/A'}</p>
            <p><strong>Roll Number:</strong> {selectedBuildingInfo.roll_number || 'N/A'}</p>
            <p><strong>Structure ID:</strong> {selectedBuildingInfo.struct_id || 'N/A'}</p>
          </div>
        )}
      </DeckGL>
    </div>
  );
}

export default App;
