/**
 * Map-related constants used throughout the application
 */

// MapTiler API key for map styles
export const MAPTILER_API_KEY = 'xNucgqob58FS7cn7XeAy';

// Map style options
export const MAP_STYLES = {
  streets: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_API_KEY}`,
  satellite: `https://api.maptiler.com/maps/satellite/style.json?key=${MAPTILER_API_KEY}`,
  basic: `https://api.maptiler.com/maps/basic-v2/style.json?key=${MAPTILER_API_KEY}`,
  outdoor: `https://api.maptiler.com/maps/outdoor-v2/style.json?key=${MAPTILER_API_KEY}`,
} as const;

export const DEFAULT_MAP_STYLE_KEY = 'streets';

// Initial view state for the map centered on downtown Calgary
export const INITIAL_VIEW_STATE = {
  longitude: -114.065,
  latitude: 51.0475,
  zoom: 15.5,
  pitch: 60,
  bearing: 0
} as const;

// API endpoints
export const API_ENDPOINTS = {
  BUILDINGS: 'http://127.0.0.1:5000/api/buildings',
  FILTER_BUILDINGS: 'http://127.0.0.1:5000/api/filter_buildings'
} as const; 