# Calgary 3D Building Dashboard

A 3D visualization of Calgary's buildings using React, Three.js, and Flask.

## Overview

This project provides an interactive 3D visualization of buildings in Calgary, Alberta. It fetches building data from the Calgary Open Data API, processes it, and renders it in a 3D environment where users can explore, interact with buildings, and view detailed information.

## Features

- **3D Building Visualization**: Buildings are rendered in 3D with accurate footprints and heights
- **Interactive Controls**: Pan, zoom, and rotate the view to explore the city
- **Building Information**: Click on buildings to view detailed information including:
  - Address
  - Height
  - Assessed value
  - Land use designation
  - Year built
- **Natural Language Filtering**: Filter buildings using natural language queries
- **Multiple Map Styles**: Switch between different base map styles (Streets, Satellite, Basic, Outdoor)

## Project Structure

```
calgary-3d-dashboard/
├── backend/                # Flask backend
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── venv/               # Python virtual environment
├── frontend/               # React frontend
│   ├── public/             # Static files
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   ├── constants/      # Constants and configuration
│   │   ├── types/          # TypeScript type definitions
│   │   ├── App.js          # Main application component
│   │   └── index.js        # Entry point
│   ├── package.json        # Node.js dependencies
│   └── README.md           # Frontend documentation
└── README.md               # Project documentation
```

## Setup Instructions

### Prerequisites

- Node.js (v14 or higher)
- Python (v3.8 or higher)
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the Flask server:
   ```
   python app.py
   ```

The backend will be available at `http://localhost:5000`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

The frontend will be available at `http://localhost:3000`.

## API Endpoints

- `GET /api/buildings`: Returns all buildings within the defined bounding box
- `GET /api/filter_buildings?query=<natural_language_query>`: Returns buildings filtered based on the natural language query

## Technologies Used

- **Frontend**:
  - React
  - Three.js / React Three Fiber
  - Deck.gl
  - MapLibre GL
  - TypeScript

- **Backend**:
  - Flask
  - GeoPandas
  - Shapely
  - Hugging Face API (for natural language processing)

## Data Sources

- Building footprints: [Calgary Building Footprints](https://data.calgary.ca/Government/Building-Footprints/cchr-krqg)
- Property assessments: [Calgary Property Assessments](https://data.calgary.ca/Government/Property-Assessments/4bsw-nn7w)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Calgary Open Data Portal for providing the building and assessment data
- Hugging Face for providing the natural language processing capabilities 