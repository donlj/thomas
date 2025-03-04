/********************************************
 * app.js – Predictive + Real-Time Traffic
 ********************************************/

// Replace with your actual tokens/endpoints
mapboxgl.accessToken = "p1In0.IDbRSRluguViXa6h1_18qA";  // Replace with your Mapbox API Key
const TOMTOM_API_KEY = "";  
const ML_SERVER_URL = "http://localhost:5000/predictCongestion"; // Your real ML endpoint

// Initialize the map
const map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/streets-v11',
  center: [77.5946, 12.9716], // e.g. Bangalore
  zoom: 10
});

// DOM elements
const useCurrentLocBtn = document.getElementById('use-current-loc-btn');
const findRouteBtn = document.getElementById('find-route-btn');
const originInput = document.getElementById('origin');
const destinationInput = document.getElementById('destination');
const modeSelect = document.getElementById('transport-mode');
const predictTimeInput = document.getElementById('predict-time');
const startNavBtn = document.getElementById('start-nav-btn');

// Markers
let originMarker = null;
let destinationMarker = null;
let navMarker = null; // For navigation simulation

// Route data
let routeData = [];
let selectedRouteIndex = 0;
let routeLayers = [];

// For navigation
let navInterval = null;
let navIndex = 0;
let navCoords = [];

// Track user location
let userLocation = null;
navigator.geolocation.watchPosition(
  pos => { userLocation = [pos.coords.longitude, pos.coords.latitude]; },
  err => console.warn('Geolocation error:', err),
  { enableHighAccuracy: true, maximumAge: 1000 }
);

/* ========================= EVENT LISTENERS ========================= */
useCurrentLocBtn.addEventListener('click', () => {
  if (userLocation) {
    originInput.value = "Current Location";
  } else {
    alert('Current location not available yet.');
  }
});
findRouteBtn.addEventListener('click', calculateRoute);
startNavBtn.addEventListener('click', startNavigation);

/* ========================= AUTOCOMPLETE ========================= */
originInput.addEventListener('input', () => showSuggestions(originInput, document.getElementById('origin-suggestions')));
destinationInput.addEventListener('input', () => showSuggestions(destinationInput, document.getElementById('destination-suggestions')));

function showSuggestions(inputElem, suggestionsElem) {
  const query = inputElem.value.trim();
  if (query.length < 2) {
    suggestionsElem.style.display = 'none';
    return;
  }
  const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${mapboxgl.accessToken}`;
  fetch(url)
    .then(res => res.json())
    .then(data => {
      suggestionsElem.innerHTML = '';
      if (data.features && data.features.length > 0) {
        data.features.forEach(feature => {
          const div = document.createElement('div');
          div.className = 'suggestion-item';
          div.innerText = feature.place_name;
          div.onclick = () => {
            inputElem.value = feature.place_name;
            suggestionsElem.style.display = 'none';
          };
          suggestionsElem.appendChild(div);
        });
        // Position suggestions below input
        const rect = inputElem.getBoundingClientRect();
        suggestionsElem.style.left = rect.left + 'px';
        suggestionsElem.style.top = (rect.bottom + window.scrollY) + 'px';
        suggestionsElem.style.width = rect.width + 'px';
        suggestionsElem.style.display = 'block';
      } else {
        suggestionsElem.style.display = 'none';
      }
    })
    .catch(err => console.error('Autocomplete error:', err));
}

/* ========================= ROUTE CALCULATION ========================= */
async function calculateRoute() {
  // Clear old routes and stop any nav simulation
  clearExistingRoutes();
  stopNavigation();

  const origVal = originInput.value.trim();
  const destVal = destinationInput.value.trim();
  let mode = modeSelect.value;
  const futureTime = predictTimeInput.value; // user-chosen future time

  if (!origVal || !destVal) {
    alert('Please enter both Origin and Destination.');
    return;
  }
  // Convert "bus" => "driving" for Mapbox
  if (mode === 'bus') mode = 'driving';

  const originCoords = await geocodeOrCurrentLocation(origVal);
  if (!originCoords) {
    alert('Invalid origin location.');
    return;
  }
  const destCoords = await geocodeOrCurrentLocation(destVal);
  if (!destCoords) {
    alert('Invalid destination location.');
    return;
  }

  // Place markers
  if (originMarker) originMarker.remove();
  originMarker = new mapboxgl.Marker({ color: 'green' })
    .setLngLat(originCoords)
    .addTo(map);

  if (destinationMarker) destinationMarker.remove();
  destinationMarker = new mapboxgl.Marker({ color: 'red' })
    .setLngLat(destCoords)
    .addTo(map);

  // Fetch route geometry from Mapbox
  const directionsURL = `https://api.mapbox.com/directions/v5/mapbox/${mode}/${originCoords[0]},${originCoords[1]};${destCoords[0]},${destCoords[1]}?geometries=geojson&steps=true&alternatives=true&overview=full&access_token=${mapboxgl.accessToken}`;
  try {
    const res = await fetch(directionsURL);
    const data = await res.json();
    if (!data.routes || data.routes.length === 0) {
      alert('No routes found from Mapbox.');
      return;
    }
    routeData = data.routes;
    selectedRouteIndex = 0;

    // If the user specified a future time => predictive approach
    // Otherwise => real-time partial coloring from route.legs[0].annotation.congestion
    const isPredictive = !!futureTime;
    for (let i = 0; i < routeData.length; i++) {
      if (isPredictive) {
        // Call your real ML backend to get predicted congestion
        // store it in routeData[i].predictedCongestion
        routeData[i].predictedCongestion = await fetchMLPredictions(routeData[i], futureTime);
      }
    }

    // Draw routes
    routeData.forEach((route, idx) => {
      if (isPredictive) {
        drawPredictiveRoute(route, idx);
      } else {
        drawRealTimeRoute(route, idx);
      }
    });
    fillAlternativeRoutes(routeData);

    // Zoom to the first route
    const coords = routeData[0].geometry.coordinates;
    const bounds = coords.reduce((b, c) => b.extend(c), new mapboxgl.LngLatBounds(coords[0], coords[0]));
    map.fitBounds(bounds, { padding: 40 });

    // Update side panel
    updateRoutePanel(routeData[0], mode);
    document.getElementById('origin-text').textContent = origVal;
    document.getElementById('destination-text').textContent = destVal;

    // Store main route coords for "Start Navigation"
    navCoords = routeData[0].geometry.coordinates.slice();

    // For the traffic overview, we fetch real-time from TomTom for the midpoint
    const mid = computeMidpoint(originCoords, destCoords);
    const flow = await fetchTomTomTraffic(mid[1], mid[0]);
    updateTrafficStatus(flow);

    const incidents = await fetchTomTomIncidents(mid[1], mid[0]);
    updateIncidents(incidents);

    // Enable "Start Navigation"
    startNavBtn.disabled = false;

  } catch (err) {
    console.error('Directions error:', err);
    alert('Error fetching route data.');
  }
}

/* ========================= DRAW REAL-TIME PARTIAL (from annotation.congestion) ========================= */
async function drawRealTimeRoute(route, routeIndex) {
  // Fetch real-time traffic data for the full route
  const trafficData = await fetchTomTomTrafficForRoute(route.geometry.coordinates);

  if (!trafficData) {
    console.warn("No traffic data available.");
    return;
  }

  // Loop through each road segment and color it based on congestion
  for (let i = 0; i < route.geometry.coordinates.length - 1; i++) {
    let color = getTrafficColor(trafficData[i]);

    const segmentId = `traffic-segment-${routeIndex}-${i}`;
    map.addSource(segmentId, {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [route.geometry.coordinates[i], route.geometry.coordinates[i + 1]],
        },
      },
    });

    map.addLayer({
      id: segmentId,
      type: "line",
      source: segmentId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": color, "line-width": 6 },
    });

    routeLayers.push(segmentId);
  }
}

// Fetch traffic data for each segment of the route
async function fetchTomTomTrafficForRoute(coordinates) {
  let trafficResults = [];
  for (let coord of coordinates) {
    const trafficInfo = await fetchTomTomTraffic(coord[1], coord[0]); // lat, lon
    trafficResults.push(trafficInfo ? trafficInfo.status : "unknown");
  }
  return trafficResults;
}

// Helper function to assign colors based on congestion level
function getTrafficColor(status) {
  switch (status) {
    case "Heavy Traffic":
      return "#ff0000"; // Red
    case "Moderate Traffic":
      return "#ffa500"; // Orange
    case "Light Traffic":
      return "#00cc66"; // Green
    default:
      return "#808080"; // Gray for unknown
  }
}


/* ========================= DRAW PREDICTIVE PARTIAL (from ML server) ========================= */
function drawPredictiveRoute(route, routeIndex) {
  // Base line
  const baseId = `base-route-${routeIndex}`;
  map.addSource(baseId, {
    type: 'geojson',
    data: { type: 'Feature', geometry: route.geometry }
  });
  const baseColor = (routeIndex === 0) ? '#007bff' : '#808080';
  map.addLayer({
    id: baseId,
    type: 'line',
    source: baseId,
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: { 'line-color': baseColor, 'line-width': 8 }
  });
  routeLayers.push(baseId);

  if (!route.predictedCongestion || route.predictedCongestion.length === 0) return;
  const coords = route.geometry.coordinates;
  const predicted = route.predictedCongestion;

  for (let i = 0; i < coords.length - 1; i++) {
    let color = '#00cc66'; // default green
    if (predicted[i] === 'heavy') color = '#ff0000';
    else if (predicted[i] === 'moderate') color = '#ffa500';
    else if (predicted[i] === 'unknown') color = '#808080';

    const segId = `overlay-pred-${routeIndex}-seg-${i}`;
    map.addSource(segId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [coords[i], coords[i+1]]
        }
      }
    });
    map.addLayer({
      id: segId,
      type: 'line',
      source: segId,
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: { 'line-color': color, 'line-width': 4 }
    });
    routeLayers.push(segId);
  }
}

/* ========================= CALL THE REAL ML SERVER FOR FUTURE TIME ========================= */
async function fetchMLPredictions(route, futureTime) {
  // Build the request items. Typically you must match your segment_id with your ML dataset.
  // For demonstration, we pass i as "segment_id", timestamp = futureTime, speed = 30, etc.
  const coords = route.geometry.coordinates;
  let items = [];
  for (let i = 0; i < coords.length - 1; i++) {
    items.push({
      "segment_id": i,        // Replace with your real ID logic
      "timestamp": futureTime,
      "speed": 30            // or from real-time data
    });
  }

  // Call your real ML endpoint
  const resp = await fetch(ML_SERVER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items })
  });
  const data = await resp.json();
  // data.predictions => array of "heavy","moderate","light"
  return data.predictions;
}

/* ========================= START NAVIGATION SIMULATION ========================= */
function startNavigation() {
  stopNavigation();
  if (!navCoords || navCoords.length < 2) {
    alert('No route found. Please find routes first.');
    return;
  }
  navIndex = 0;

  // Create a marker for the simulation
  if (navMarker) navMarker.remove();
  const iconUrl = getIconUrl(modeSelect.value);
  navMarker = new mapboxgl.Marker({ element: createMarkerElement(iconUrl) })
    .setLngLat(navCoords[0])
    .addTo(map);

  // Move every 1 second
  navInterval = setInterval(() => {
    if (navIndex < navCoords.length) {
      navMarker.setLngLat(navCoords[navIndex]);
      navIndex++;
    } else {
      stopNavigation();
      alert('Navigation complete!');
    }
  }, 1000);
}
function stopNavigation() {
  if (navInterval) {
    clearInterval(navInterval);
    navInterval = null;
  }
  if (navMarker) {
    navMarker.remove();
    navMarker = null;
  }
  navIndex = 0;
}

/* ========================= TOMTOM (REAL-TIME) ========================= */
async function fetchTomTomTraffic(lat, lon) {
  const url = `https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key=${TOMTOM_API_KEY}&point=${lat},${lon}`;
  try {
    const resp = await fetch(url);
    const data = await resp.json();
    if (!data.flowSegmentData) return null;
    const { currentSpeed, freeFlowSpeed } = data.flowSegmentData;
    const ratio = currentSpeed / freeFlowSpeed;
    let status = 'Light Traffic';
    if (ratio < 0.4) status = 'Heavy Traffic';
    else if (ratio < 0.7) status = 'Moderate Traffic';
    return { status, currentSpeed, freeFlowSpeed };
  } catch (err) {
    console.error('TomTom flow error:', err);
    return null;
  }
}
function updateTrafficStatus(flow) {
  if (!flow) {
    document.getElementById('congestion-level').textContent = 'N/A';
    document.getElementById('average-speed').textContent = 'N/A';
    document.getElementById('active-incidents').textContent = '0';
    document.getElementById('traffic-status').textContent = 'No data';
    return;
  }
  document.getElementById('congestion-level').textContent = flow.status;
  document.getElementById('average-speed').textContent = `${flow.currentSpeed} mph`;
  document.getElementById('active-incidents').textContent = 'N/A';
  document.getElementById('traffic-status').textContent = flow.status;
}

async function fetchTomTomIncidents(lat, lon) {
  const delta = 0.5;
  const minLat = lat - delta, maxLat = lat + delta;
  const minLon = lon - delta, maxLon = lon + delta;
  const url = `https://api.tomtom.com/traffic/services/5/incidentDetails?key=${TOMTOM_API_KEY}&bbox=${minLon}%2C${minLat}%2C${maxLon}%2C${maxLat}`;
  try {
    const resp = await fetch(url);
    const data = await resp.json();
    return data.incidents || [];
  } catch (err) {
    console.error('TomTom incidents error:', err);
    return [];
  }
}
function updateIncidents(incidents) {
  const container = document.getElementById('incidents-list');
  container.innerHTML = '';
  if (!incidents || incidents.length === 0) {
    container.innerHTML = '<p>No incidents reported</p>';
    return;
  }
  incidents.forEach(inc => {
    const li = document.createElement('li');
    let label = 'Incident';
    if (inc.iconCategory === 6) label = 'Accident';
    else if (inc.iconCategory === 4) label = 'Heavy Traffic';
    li.textContent = `${label} - ${inc.roadName || 'Unknown Road'}`;
    container.appendChild(li);
  });
}

/* ========================= PANEL & UTILS ========================= */
function updateRoutePanel(route, mode) {
  document.getElementById('route-mode').textContent = (mode === 'bus') ? 'Public Transit' : capitalize(mode);
  const dist = (route.distance / 1000).toFixed(2);
  document.getElementById('route-distance').textContent = `${dist} km`;
  const dur = (route.duration / 60).toFixed(2);
  document.getElementById('route-duration').textContent = `${dur} mins`;

  // Turn-by-turn
  const stepsEl = document.getElementById('turn-by-turn');
  stepsEl.innerHTML = '';
  if (route.legs && route.legs.length > 0) {
    route.legs[0].steps.forEach(step => {
      const li = document.createElement('li');
      li.textContent = step.maneuver.instruction;
      stepsEl.appendChild(li);
    });
  }
  document.getElementById('main-route-info').textContent = `Main route: ~${dist} km, ~${dur} mins`;
}

function fillAlternativeRoutes(routes) {
  const altList = document.getElementById('alternative-routes');
  altList.innerHTML = '';
  if (routes.length > 1) {
    for (let i = 1; i < routes.length; i++) {
      const li = document.createElement('li');
      const dist = (routes[i].distance / 1000).toFixed(2);
      const dur = (routes[i].duration / 60).toFixed(2);
      li.textContent = `Alt #${i}: ~${dist} km, ~${dur} mins`;
      altList.appendChild(li);
    }
  } else {
    altList.innerHTML = '<li>No alternatives yet</li>';
  }
}

/* Clear route layers */
function clearExistingRoutes() {
  routeLayers.forEach(id => {
    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id);
  });
  routeLayers = [];
}

/* Stop nav simulation */
function stopNavigation() {
  if (navInterval) {
    clearInterval(navInterval);
    navInterval = null;
  }
  if (navMarker) {
    navMarker.remove();
    navMarker = null;
  }
  navIndex = 0;
}

/* Utility for geocoding or "Current Location" */
async function geocodeOrCurrentLocation(place) {
  if (place.toLowerCase() === 'current location' && userLocation) {
    return userLocation;
  } else {
    return await geocodeLocation(place);
  }
}
async function geocodeLocation(place) {
  const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(place)}.json?access_token=${mapboxgl.accessToken}`;
  try {
    const resp = await fetch(url);
    const data = await resp.json();
    if (data.features && data.features.length > 0) {
      return data.features[0].center; // [lng, lat]
    }
    return null;
  } catch (err) {
    console.error('Geocode error:', err);
    return null;
  }
}

function getIconUrl(mode) {
  switch (mode) {
    case 'walking': return 'https://cdn-icons-png.flaticon.com/512/5087/5087579.png';
    case 'cycling': return 'https://cdn-icons-png.flaticon.com/512/3163/3163135.png';
    case 'bus':     return 'https://cdn-icons-png.flaticon.com/512/724/724664.png';
    default:        return 'https://cdn-icons-png.flaticon.com/512/1946/1946629.png'; // car
  }
}
function createMarkerElement(iconUrl) {
  const el = document.createElement('div');
  el.style.backgroundImage = `url(${iconUrl})`;
  el.style.backgroundSize = 'cover';
  el.style.width = '32px';
  el.style.height = '32px';
  el.style.borderRadius = '50%';
  return el;
}

function computeMidpoint(a, b) {
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
}
function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}
