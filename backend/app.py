# backend/app.py - Updated with LLM Filtering
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from flask import Flask, jsonify, Response, request # Added request
import json
from flask_cors import CORS
import os

# --- API Endpoints ---
BUILDINGS_API_URL = "https://data.calgary.ca/resource/cchr-krqg.json"
ASSESSMENTS_API_URL = "https://data.calgary.ca/resource/4bsw-nn7w.json"
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1" # Example model

# Bounding Box (WGS84: North, East, South, West) for downtown area
BBOX_NORTH = 51.0575
BBOX_EAST = -114.040
BBOX_SOUTH = 51.0375
BBOX_WEST = -114.080


def fetch_data(api_url, bbox, limit=None):
    """Fetches data from a Socrata API endpoint within a bounding box using pagination.
    
    Args:
        api_url: The SODA API endpoint URL
        bbox: Tuple of (north, east, south, west) coordinates
        limit: Optional total number of records to fetch (None means all)
    """
    north, east, south, west = bbox
    if "cchr-krqg" in api_url:
        geom_col = "polygon"
        select_fields = "struct_id,grd_elev_min_z,rooftop_elev_z,polygon"
    elif "4bsw-nn7w" in api_url:
        geom_col = "multipolygon"
        select_fields = "roll_number,address,assessed_value,land_use_designation,year_of_construction,multipolygon"
    elif "qe6k-p9nh" in api_url: # currently unused
        geom_col = "multipolygon"
        select_fields = "lu_code,label,description,major,multipolygon"
    else:
        print(f"Warning: Unknown API structure for {api_url}. Using default geometry column 'geometry'.")
        geom_col = "geometry"
        select_fields = "*" # Fetch all fields if unsure

    where_clause = f"within_box({geom_col},{north},{east},{south},{west})"

    BATCH_SIZE = 1000
    offset = 0
    all_data = []

    while True:
        params = {
            "$limit": BATCH_SIZE,
            "$offset": offset,
            "$where": where_clause,
            "$select": select_fields
        }

        try:
            print(f"Fetching batch from {api_url} with offset {offset}")
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            batch_data = response.json()
            
            if not batch_data:
                break
                
            all_data.extend(batch_data)
            print(f"Fetched {len(batch_data)} records, total: {len(all_data)}")
            
            if len(batch_data) < BATCH_SIZE:
                break
                
            if limit is not None and len(all_data) >= limit:
                all_data = all_data[:limit]
                print(f"Reached requested limit of {limit} records.")
                break
                
            offset += BATCH_SIZE
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {api_url}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {api_url}: {e}")
            print(f"Response text: {response.text}")
            return None

    print(f"Successfully fetched total of {len(all_data)} records from {api_url}")
    return all_data


def create_gdf(data, geom_col_name):
    """Converts JSON data with geometry into a GeoDataFrame."""
    if not data:
        if geom_col_name == 'polygon':
             cols = ['struct_id', 'grd_elev_min_z', 'rooftop_elev_z', 'geometry']

        elif geom_col_name == 'multipolygon':
             cols = ['roll_number', 'address', 'assessed_value', 'land_use_designation', 'year_of_construction', 'geometry']
       
        else:
            cols = ['geometry'] # Minimal fallback
        return gpd.GeoDataFrame([], columns=cols, crs="EPSG:4326")

    # Ensure geometry data exists and is valid before creating shapes
    valid_data = []
    required_id_col = 'struct_id' if geom_col_name == 'polygon' else 'roll_number'

    createShapeForRecords(data, geom_col_name, valid_data, required_id_col)

    if not valid_data:
         if geom_col_name == 'polygon':
             cols = ['struct_id', 'grd_elev_min_z', 'rooftop_elev_z', 'geometry']

         elif geom_col_name == 'multipolygon':
             cols = ['roll_number', 'address', 'assessed_value', 'land_use_designation', 'year_of_construction', 'geometry']

         else:
            cols = ['geometry']

         return gpd.GeoDataFrame([], columns=cols, crs="EPSG:4326")

    gdf = gpd.GeoDataFrame(valid_data, crs="EPSG:4326") # Assuming WGS84

    if geom_col_name != 'geometry' and geom_col_name in gdf.columns:
        gdf = gdf.drop(columns=[geom_col_name])

    return gdf

def createShapeForRecords(data, geom_col_name, valid_data, required_id_col):
    for record in data:
        if geom_col_name in record and record[geom_col_name]:
             try:
                 record['geometry'] = shape(record[geom_col_name])
                 valid_data.append(record)

             except Exception as e:
                 print(f"Error creating shape for record {record.get(required_id_col)}: {e}")
        else:
            print(f"Missing or empty geometry in record: {record.get(required_id_col)}")

# --- Data Fetching and Processing Logic (Extracted for direct execution) ---
def fetch_and_process_data(bbox):
    """Fetches, processes, and joins building and assessment data."""
    # Fetch data (passing limit=None to fetch all)
    print("Fetching building data...")
    buildings_data = fetch_data(BUILDINGS_API_URL, bbox, limit=None)
    print("Fetching assessment data...")
    assessments_data = fetch_data(ASSESSMENTS_API_URL, bbox, limit=None)

    if buildings_data is None or assessments_data is None:
        print("Error: Failed to fetch data from one or more APIs.")
        return None

    if not buildings_data:
        print("No buildings found in the specified area.")
        return gpd.GeoDataFrame([]) # Return empty GDF

    # Create GeoDataFrames
    print("Creating GeoDataFrames...")
    buildings_gdf = create_gdf(buildings_data, 'polygon')
    assessments_gdf = create_gdf(assessments_data, 'multipolygon')

    # --- Data Processing ---
    print("Processing data...")
    
    convertColumnsToNumeric(buildings_gdf)
    convertNumeric(assessments_gdf)

    # Calculate height
    if 'grd_elev_min_z' in buildings_gdf.columns and 'rooftop_elev_z' in buildings_gdf.columns:
        buildings_gdf['height'] = buildings_gdf['rooftop_elev_z'] - buildings_gdf['grd_elev_min_z']
    else:
        print("Warning: Elevation columns missing, cannot calculate height.")
        buildings_gdf['height'] = None

    # --- Joining Data ---
    if 'geometry' not in buildings_gdf.columns:
         print("ERROR: Geometry column missing in building dataset. Cannot perform join.")
         return None

    if buildings_gdf.empty:
         print("No valid building geometries found.")
         return gpd.GeoDataFrame([]) # Return empty GDF

    final_gdf = None 

    if assessments_gdf.empty or 'geometry' not in assessments_gdf.columns or assessments_gdf['geometry'].isnull().all():
         print("Warning: No valid assessment data/geometry found. Proceeding with building data only.")

         final_gdf = buildings_gdf[['struct_id', 'height', 'geometry']].copy()
         for col in ['roll_number', 'address', 'assessed_value', 'land_use_designation', 'year_of_construction']:
             final_gdf[col] = None
    else:
        print("Performing spatial join...")
        try:
            if buildings_gdf.crs != assessments_gdf.crs:
                 print(f"Warning: CRS mismatch. Buildings: {buildings_gdf.crs}, Assessments: {assessments_gdf.crs}. Attempting to align to buildings CRS.")
                 assessments_gdf = assessments_gdf.to_crs(buildings_gdf.crs)

            # Use 'predicate' instead of 'op' for newer geopandas versions
            joined_gdf = gpd.sjoin(buildings_gdf, assessments_gdf, how='left', predicate='intersects')

            # Handle potential duplicate buildings if they intersect multiple parcels (take first match)
            joined_gdf = joined_gdf.drop_duplicates(subset=['struct_id'], keep='first')

            # Select and rename columns for the final output
            final_cols_mapping = {
                'struct_id': 'struct_id',
                'height': 'height',
                'roll_number': 'roll_number',
                'address': 'address',
                'assessed_value': 'assessed_value',
                'land_use_designation': 'land_use_designation',
                'year_of_construction': 'year_of_construction',
                'geometry': 'geometry'
            }

            existing_cols = [col for col in final_cols_mapping.keys() if col in joined_gdf.columns]

            final_gdf = joined_gdf[existing_cols].copy()
            for col_name in final_cols_mapping.keys():
                if col_name not in final_gdf.columns:
                    final_gdf[col_name] = None

            if 'geometry' not in final_gdf.columns:
                print("ERROR: Geometry column lost during join or processing.")
                return None

            final_gdf = final_gdf[list(final_cols_mapping.keys())].rename(columns=final_cols_mapping)


        except Exception as e:
            print(f"Error during spatial join or processing: {e}")
            final_gdf = buildings_gdf[['struct_id', 'height', 'geometry']].copy()
            for col in ['roll_number', 'address', 'assessed_value', 'land_use_designation', 'year_of_construction']:
                 final_gdf[col] = None

    # Final cleanup and return
    if final_gdf is not None:
        # Ensure NaN/None values are handled correctly for JSON conversion
        # Use pandas NA which converts better to null in GeoJSON
        final_gdf = final_gdf.fillna(value=pd.NA)
        print(f"Final processed data has {len(final_gdf)} records.")
        print(f"Columns: {final_gdf.columns.tolist()}")
    else:
        print("Error: final_gdf was not created.")

    return final_gdf

# Helpers
# Convert columns to numeric
def convertNumeric(assessments_gdf):
    for col in ['assessed_value', 'year_of_construction']:
        if col in assessments_gdf.columns:
            assessments_gdf[col] = pd.to_numeric(assessments_gdf[col], errors='coerce')

# Convert columns to numeric
def convertColumnsToNumeric(buildings_gdf):
    for col in ['grd_elev_min_z', 'rooftop_elev_z']:
         if col in buildings_gdf.columns:
              buildings_gdf[col] = pd.to_numeric(buildings_gdf[col], errors='coerce')

# --- LLM and Filtering Logic ---
def get_filter_from_llm(query):
    api_key = "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"

    headers = {"Authorization": f"Bearer {api_key}"}
    prompt = f"""
    Extract filter parameters from the following user query about building data.
    The available filterable attributes are: 'height' (numeric, in meters), 'assessed_value' (numeric), 'land_use_designation' (text), 'year_of_construction' (numeric year).
    Return ONLY a JSON object with the keys 'attribute', 'operator', and 'value'.
    - 'attribute' must be one of the available attributes.
    - 'operator' must be one of: '>', '<', '=', 'contains'. Use '=' for exact matches on text or numbers, and 'contains' for partial text matches.
    - 'value' should be the numeric or string value to filter by.

    User Query: "{query}"

    JSON:
    """

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 50, # Limit token generation
            "return_full_text": False # Only return the generated part
        }
    }

    try:
        print(f"Sending query to Hugging Face: {query}")
        response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"LLM Raw Response: {result}")

        if isinstance(result, list) and result and 'generated_text' in result[0]:
            generated_json_str = result[0]['generated_text'].strip()
        else:
             print("Error: Unexpected LLM response format.")
             print(f"Full Response: {result}")
             return None, "Unexpected LLM response format"

        if generated_json_str.startswith('```json'):
            generated_json_str = generated_json_str.removeprefix('```json').removesuffix('```')
        generated_json_str = generated_json_str.strip()

        try:
            filter_params = json.loads(generated_json_str)
            print(f"Parsed Filter Params: {filter_params}")
            if not all(k in filter_params for k in ['attribute', 'operator', 'value']):
                print("Error: LLM JSON missing required keys.")
                return None, "LLM did not return required filter keys"
            if filter_params['attribute'] not in ['height', 'assessed_value', 'land_use_designation', 'year_of_construction']:
                print("Error: LLM returned an invalid attribute.")
                return None, "LLM returned an invalid attribute"
            if filter_params['operator'] not in ['>', '<', '=', 'contains']:
                print("Error: LLM returned an invalid operator.")
                return None, "LLM returned an invalid operator"
            return filter_params, None
        except json.JSONDecodeError as json_err:
            print(f"Error parsing LLM JSON response: {json_err}")
            print(f"LLM Generated String: {generated_json_str}")
            return None, "Failed to parse LLM response as JSON"

    except requests.exceptions.RequestException as e:
        print(f"Error calling Hugging Face API: {e}")
        return None, f"Hugging Face API request failed: {e}"
    except Exception as e:
        print(f"An unexpected error occurred during LLM interaction: {e}")
        return None, f"Unexpected error during LLM processing: {e}"

def apply_filter(gdf, attribute, operator, value):
    """Applies the filter criteria to the GeoDataFrame."""
    if attribute not in gdf.columns:
        print(f"Warning: Attribute '{attribute}' not found in data. Skipping filter.")
        return gdf

    gdf_filtered = gdf.dropna(subset=[attribute]).copy()
    if gdf_filtered.empty:
        print(f"Warning: No data left after removing nulls for attribute '{attribute}'.")
        return gdf_filtered

    try:
        if attribute in ['height', 'assessed_value', 'year_of_construction']:
            filter_value = pd.to_numeric(value, errors='coerce')
            if pd.isna(filter_value):
                raise ValueError("Invalid numeric value for filter")

            if operator == '>':
                return gdf_filtered[gdf_filtered[attribute] > filter_value]
            elif operator == '<':
                return gdf_filtered[gdf_filtered[attribute] < filter_value]
            elif operator == '=':
                return gdf_filtered[gdf_filtered[attribute] == filter_value]
            else:
                raise ValueError(f"Unsupported operator '{operator}' for numeric attribute '{attribute}'")

        elif attribute == 'land_use_designation':
            filter_value = str(value)
            if operator == '=':
                # Case-insensitive exact match
                return gdf_filtered[gdf_filtered[attribute].str.lower() == filter_value.lower()]
            elif operator == 'contains':
                # Case-insensitive partial match
                return gdf_filtered[gdf_filtered[attribute].str.contains(filter_value, case=False, na=False)]
            else:
                raise ValueError(f"Unsupported operator '{operator}' for text attribute '{attribute}'")
        else:
             raise ValueError(f"Filtering not implemented for attribute '{attribute}'")

    except Exception as e:
        print(f"Error applying filter ({attribute} {operator} {value}): {e}")
        # Return the original (null-dropped) gdf if filtering fails
        return gdf_filtered

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) 

base_data_cache = None
base_data_bbox = None

@app.route('/')
def hello():
    return "Backend is running!"

@app.route('/api/buildings')
def get_buildings_data_route():
    """API endpoint to get all combined building and assessment data within the default bbox."""
    global base_data_cache, base_data_bbox
    current_bbox = (BBOX_NORTH, BBOX_EAST, BBOX_SOUTH, BBOX_WEST)

    if base_data_cache is not None and base_data_bbox == current_bbox:
        print("Returning cached base data.")
        final_gdf = base_data_cache
    else:
        print("Fetching and processing base data...")
        final_gdf = fetch_and_process_data(current_bbox)
        if final_gdf is not None:
            base_data_cache = final_gdf.copy() # Cache the data
            base_data_bbox = current_bbox
        else:
            base_data_cache = None # Reset cache on error
            base_data_bbox = None

    if final_gdf is None:
         return jsonify({"error": "Failed to fetch or process base data"}), 500
    if final_gdf.empty:
         return jsonify({"message": "No building data found for the specified area", "data": []}), 200

    # Convert to GeoJSON
    print("Converting base data to GeoJSON for API response...")
    try:
        geojson_output = final_gdf.to_json(na='null')
    except Exception as e:
        print(f"Error converting base GDF to GeoJSON: {e}")
        return jsonify({"error": "Failed to convert data to GeoJSON"}), 500

    # Return GeoJSON
    return Response(geojson_output, mimetype='application/json')

@app.route('/api/filter_buildings')
def filter_buildings_route():
    """API endpoint to filter buildings based on an LLM-interpreted query."""
    global base_data_cache, base_data_bbox
    query = request.args.get('query', default=None, type=str)

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # --- 1. Get Filter Criteria from LLM ---
    filter_params, error_msg = get_filter_from_llm(query)
    if error_msg:
        return jsonify({"error": f"LLM processing failed: {error_msg}"}), 500
    if not filter_params:
         return jsonify({"error": "Could not determine filter criteria from query."}), 400

    # --- 2. Get Base Data (from cache or fetch) ---
    current_bbox = (BBOX_NORTH, BBOX_EAST, BBOX_SOUTH, BBOX_WEST)
    # Check if cache needs to be populated
    if base_data_cache is None or base_data_bbox != current_bbox:
        print("Base data not cached or bbox changed, fetching and processing...")
        # Fetch, process, AND store the result in the cache
        fetched_data = fetch_and_process_data(current_bbox)
        if fetched_data is not None:
            base_data_cache = fetched_data.copy() # Update cache
            base_data_bbox = current_bbox
            print("Base data cache updated.")
        else:
            # If fetching failed, reset cache and return error
            base_data_cache = None
            base_data_bbox = None
            print("Error: Failed to fetch/process base data.")
            return jsonify({"error": "Failed to load base data for filtering"}), 500
    else:
        print("Using cached base data for filtering.")

    # --- 3. Apply Filter (Now we are sure base_data_cache is populated if we got here) ---
    print(f"Applying filter: {filter_params}")
    try:
        filtered_gdf = apply_filter(
            base_data_cache, # Apply filter to the cached data
            filter_params['attribute'],
            filter_params['operator'],
            filter_params['value']
        )
        print(f"Filtering complete. Found {len(filtered_gdf)} matching buildings.")
    except Exception as e:
        print(f"Error during filtering application: {e}")
        return jsonify({"error": f"Failed to apply filter: {e}"}), 500

    # --- 4. Return Filtered Data ---
    if filtered_gdf.empty:
         return jsonify({"message": "No buildings matched the filter criteria", "data": []}), 200

    print("Converting filtered data to GeoJSON...")
    try:
        geojson_output = filtered_gdf.to_json(na='null')
    except Exception as e:
        print(f"Error converting filtered GDF to GeoJSON: {e}")
        return jsonify({"error": "Failed to convert filtered data to GeoJSON"}), 500

    return Response(geojson_output, mimetype='application/json')


# Only runs when script is executed directly
if __name__ == '__main__':
    print("--- Starting Flask Development Server ---")
    print("Endpoints available:")
    print("  /api/buildings - Get all processed building data")
    print("  /api/filter_buildings?query=<your_query> - Get filtered building data")
    print("Note: Ensure HUGGING_FACE_API_KEY is set in backend/.env")
    app.run(debug=True, use_reloader=False) # Disable reloader for stability