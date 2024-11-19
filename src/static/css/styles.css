// Initialise la carte avec le fond de carte Carto Dark sans labels pour un thème gris détaillé
const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png', {
    attribution: 'Erwan Vinot 2024',
    maxZoom: 20
}).addTo(map);

// Panneau d'information pour afficher les temps de trajet et les noms des points avec bullet points colorés
const info = L.control({ position: 'topright' });
info.onAdd = function () {
    this._div = L.DomUtil.create('div', 'info');
    this.update();
    return this._div;
};

// Fonction pour mettre à jour le panneau d'information avec les temps de trajet et les noms des points
info.update = function (travelTimes) {
    if (!travelTimes || travelTimes.length === 0) {
        this._div.innerHTML = '<h4>Temps de Trajet</h4><p>Cliquez sur la carte pour voir les temps de trajet.</p>';
        return;
    }
    let html = '<h4>Temps de Trajet</h4><ul>';
    travelTimes.forEach(pt => {
        html += `
            <li>
                <span style="color: ${pt.color};">&#9679;</span>
                <strong>${pt.mode}</strong>: <em>${pt.name}</em> - ${pt.time !== Infinity ? pt.formattedTime : 'N/A'}
            </li>
        `;
    });
    html += '</ul>';
    this._div.innerHTML = html;
};
info.addTo(map);

let currentZoneLayer = null;
let currentPointsLayer = null;

// Groupes de couches pour gérer les routes, les points colorés et le marqueur d'intervention
const routesLayer = L.layerGroup().addTo(map);
const fastestPointsLayer = L.layerGroup().addTo(map);
const interventionLayer = L.layerGroup().addTo(map);

// Clé API pour OpenRouteService
const apiKey = "5b3ce3597851110001cf624873a9f82e7dce4b46a1e049860a2c461d"; // Remplacez par votre clé API ORS

// Mise en cache des temps de trajet pour éviter les appels redondants
const travelTimeCache = new Map();

// Mapping des modes de transport aux couleurs
const modeColorMap = {
    'Voiture': 'pink',
    'Marche': 'cyan',
    'Camion': 'orange'
};

// Mapping des modes de transport aux noms ORS
const displayModeToORS = {
    'Voiture': 'driving-car',
    'Marche': 'foot-walking',
    'Camion': 'driving-hgv'
};

// Mapping des modes ORS aux noms affichés
const orsToDisplayMode = {
    'driving-car': 'Voiture',
    'foot-walking': 'Marche',
    'driving-hgv': 'Camion'
};

/**
 * Charge des données FlatGeobuf et les ajoute à la carte.
 * @param {string} url - URL du fichier FlatGeobuf à charger.
 * @param {string} layerType - Type de couche à ajouter ('zone' ou 'points').
 */
async function loadFlatGeobuf(url, layerType) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            console.error(`Échec de la récupération de ${url} : ${response.statusText}`);
            return;
        }

        const asyncIterator = flatgeobuf.deserialize(response.body);
        const features = [];
        for await (const feature of asyncIterator) {
            features.push(feature);
        }

        if (features.length === 0) {
            console.warn(`Aucune caractéristique trouvée dans ${url}`);
            return;
        }

        const geojson = {
            type: "FeatureCollection",
            features: features
        };

        const options = {
            style: layerType === 'zone' ? {
                color: '#4a4a4a',
                weight: 2,
                fill: false
            } : undefined,
            pointToLayer: layerType === 'points' ? (feature, latlng) => L.circleMarker(latlng, {
                radius: 3,
                fillColor: '#808080',
                color: '#808080',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }) : undefined,
            onEachFeature: function (feature, layer) {
                if (feature.properties && feature.properties.name) {
                    layer.bindPopup(`<strong>${layerType === 'zone' ? 'Zone' : 'Point'} :</strong> ${feature.properties.name}`);
                }
            }
        };

        if (layerType === 'zone') {
            currentZoneLayer = L.geoJSON(geojson, options).addTo(map);
            map.fitBounds(currentZoneLayer.getBounds());
        } else if (layerType === 'points') {
            currentPointsLayer = L.geoJSON(geojson, options).addTo(map);
        }
    } catch (error) {
        console.error(`Erreur lors du chargement des données FlatGeobuf depuis ${url} :`, error);
    }
}

/**
 * Trouve les 10 points les plus proches d'une localisation donnée.
 * @param {number} lat - Latitude de la localisation.
 * @param {number} lng - Longitude de la localisation.
 * @returns {Array} Tableau des couches des points les plus proches.
 */
function getClosestPoints(lat, lng) {
    if (!currentPointsLayer) return [];

    const points = currentPointsLayer.getLayers()
        .map(layer => ({
            layer,
            distance: map.distance([lat, lng], layer.getLatLng())
        }))
        .sort((a, b) => a.distance - b.distance)
        .slice(0, 10)
        .map(p => p.layer);

    return points;
}

/**
 * Calcule les temps de trajet pour les points les plus proches en utilisant des requêtes par mode.
 * @param {number} markerLat - Latitude de l'intervention.
 * @param {number} markerLng - Longitude de l'intervention.
 * @param {Array} points - Tableau des couches des points les plus proches.
 * @returns {Array} Tableau des résultats des temps de trajet.
 */
async function calculateTravelTimes(markerLat, markerLng, points) {
    const travelModes = ['foot-walking', 'driving-car', 'driving-hgv'];
    const results = [];

    for (const mode of travelModes) {
        const modeDisplay = orsToDisplayMode[mode];
        if (!modeDisplay) {
            console.warn(`Mode de transport inconnu: ${mode}`);
            continue;
        }

        const destinations = points.map(layer => {
            const { lat, lng } = layer.getLatLng();
            return [lng, lat];
        });

        const cacheKey = `${mode}_${markerLat}_${markerLng}_${destinations.map(coord => coord.join(',')).join(';')}`;

        let travelTimes;
        if (travelTimeCache.has(cacheKey)) {
            travelTimes = travelTimeCache.get(cacheKey);
        } else {
            travelTimes = await getTravelTime(mode, [markerLng, markerLat], destinations);
            travelTimeCache.set(cacheKey, travelTimes);
        }

        if (!travelTimes) {
            console.warn(`Aucune durée disponible pour le mode ${modeDisplay}`);
            continue;
        }

        // Trouver le point avec le temps de trajet le plus court pour ce mode
        let minTime = Infinity;
        let fastestPoint = null;

        travelTimes.forEach((time, index) => {
            if (time < minTime) {
                minTime = time;
                fastestPoint = points[index];
            }
        });

        if (fastestPoint) {
            results.push({
                mode: modeDisplay,
                name: fastestPoint.feature.properties.name,
                time: minTime,
                formattedTime: formatTravelTime(minTime),
                color: modeColorMap[modeDisplay],
                layer: fastestPoint
            });
        }
    }

    return results;
}

/**
 * Formate le temps de trajet en une chaîne lisible.
 * @param {number} seconds - Temps de trajet en secondes.
 * @returns {string} Temps formaté.
 */
function formatTravelTime(seconds) {
    if (seconds === Infinity || seconds === undefined) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return hrs > 0 ? `${hrs}h ${remainingMins}m` : `${remainingMins}m`;
}

/**
 * Dessine les routes vers les points les plus rapides pour chaque mode de transport.
 * @param {number} lat - Latitude de l'intervention.
 * @param {number} lng - Longitude de l'intervention.
 * @param {Array} fastestPoints - Tableau des points les plus rapides.
 */
async function drawFastestRoutes(lat, lng, fastestPoints) {
    // Efface les routes et les points colorés précédents
    routesLayer.clearLayers();
    fastestPointsLayer.clearLayers();

    const routePromises = fastestPoints.map(fp => {
        if (!fp.layer) {
            console.warn(`Layer non trouvé pour le point ${fp.name}`);
            return Promise.resolve(null);
        }

        const orsMode = displayModeToORS[fp.mode];
        if (!orsMode) {
            console.warn(`Mode de transport inconnu: ${fp.mode}`);
            return Promise.resolve(null);
        }

        const [lng1, lat1] = [lng, lat];
        const [lng2, lat2] = [fp.layer.getLatLng().lng, fp.layer.getLatLng().lat];
        return getRoute(orsMode, [[lng1, lat1], [lng2, lat2]])
            .then(coords => ({
                coords: coords.map(coord => [coord[1], coord[0]]),
                mode: fp.mode
            }))
            .catch(error => {
                console.error(`Échec de la récupération de la route pour ${fp.mode}:`, error);
                return null;
            });
    });

    const routes = await Promise.all(routePromises);

    // Dessine les routes sur la carte avec les classes CSS appropriées
    routes.forEach(route => {
        if (route) {
            L.polyline(route.coords, { className: `route-${route.mode.toLowerCase()}` }).addTo(routesLayer);
        }
    });

    // Colorer les points trouvés selon le mode de transport
    fastestPoints.forEach(fp => {
        if (fp.layer) {
            const { lat, lng } = fp.layer.getLatLng();
            // Ne pas supprimer les points de base
            // Ajoute un nouveau marqueur coloré au-dessus des points de base
            const coloredPoint = L.circleMarker([lat, lng], {
                radius: 6,
                className: `point-${fp.mode.toLowerCase()}`,
                fillOpacity: 1,
                stroke: true,
                weight: 2
            }).addTo(fastestPointsLayer);

            coloredPoint.bindPopup(`<strong>${fp.mode} :</strong> ${fp.name}`);
        }
    });

    // Met à jour le panneau d'information
    const displayTimes = fastestPoints.map(fp => ({
        mode: fp.mode,
        name: fp.name,
        time: fp.time,
        formattedTime: fp.formattedTime,
        color: fp.color
    }));
    info.update(displayTimes);
}

/**
 * Récupère le temps de trajet à partir de l'API Matrix d'OpenRouteService.
 * @param {string} mode - Mode de transport.
 * @param {Array} origin - Coordonnées [lng, lat] de départ.
 * @param {Array} destinations - Tableau de coordonnées [lng, lat] d'arrivée.
 * @returns {Promise<Array|null>} Tableau des temps de trajet en secondes ou null en cas d'erreur.
 */
async function getTravelTime(mode, origin, destinations) {
    const url = `https://api.openrouteservice.org/v2/matrix/${mode}`;
    const body = {
        locations: [origin, ...destinations],
        metrics: ['duration'],
        units: 'm' // Assure que les unités sont en mètres
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': apiKey,
                'Content-Type': 'application/json',
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8'
            },
            body: JSON.stringify(body)
        });

        console.log(`ORS Matrix API response status for mode ${mode}:`, response.status);

        if (!response.ok) {
            console.error(`Erreur lors de l'appel Matrix API pour le mode ${mode}:`, response.status, response.statusText);
            return null;
        }

        const data = await response.json();
        console.log(`ORS Matrix API response data for mode ${mode}:`, data);

        if (data.durations && data.durations.length > 0) {
            // Le premier élément est l'origine, les suivants sont les destinations
            return data.durations[0].slice(1); // Exclure l'origine
        } else {
            console.warn(`Durée non disponible pour le mode ${mode}`);
            return null;
        }
    } catch (error) {
        console.error(`Erreur lors de l'appel Matrix API pour le mode ${mode}:`, error);
        return null;
    }
}

/**
 * Récupère les coordonnées de la route à partir de l'API Directions d'OpenRouteService.
 * @param {string} mode - Mode de transport.
 * @param {Array} coordinates - Tableau de coordonnées [[lng1, lat1], [lng2, lat2]].
 * @returns {Promise<Array>} Tableau des coordonnées de la route.
 */
async function getRoute(mode, coordinates) {
    const url = `https://api.openrouteservice.org/v2/directions/${mode}/geojson`;
    const body = {
        coordinates: coordinates
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': apiKey,
                'Content-Type': 'application/json',
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8'
            },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            throw new Error(`Directions API request failed with status ${response.status}`);
        }

        const data = await response.json();
        if (data.features && data.features[0] && data.features[0].geometry) {
            return data.features[0].geometry.coordinates;
        } else {
            throw new Error('Invalid route geometry');
        }
    } catch (error) {
        console.error(`Erreur lors de l'appel Directions API pour le mode ${mode}:`, error);
        throw error;
    }
}

/**
 * Ajoute un écouteur d'événement au clic sur la carte pour définir le site d'intervention et calculer les routes.
 */
map.on('click', async function (event) {
    const { lat, lng } = event.latlng;

    // Efface le marqueur d'intervention précédent et les routes/points colorés existants
    interventionLayer.clearLayers();
    routesLayer.clearLayers();
    fastestPointsLayer.clearLayers();

    // Ajoute un nouveau marqueur d'intervention (cercle blanc simple)
    const intervention = L.circleMarker([lat, lng], {
        radius: 10,
        className: 'intervention-marker',
        fillOpacity: 1,
        stroke: true,
        weight: 2
    }).addTo(interventionLayer);

    // Pas de tooltip pour le marqueur d'intervention
    // Si vous souhaitez ajouter une popup, décommentez la ligne suivante
    // intervention.bindPopup("<strong>Intervention Site</strong>").openPopup();

    const closestPoints = getClosestPoints(lat, lng);
    const travelTimes = await calculateTravelTimes(lat, lng, closestPoints);

    await drawFastestRoutes(lat, lng, travelTimes);
});

/**
 * Charge les données sélectionnées dans le menu déroulant.
 */
async function loadSelectedData() {
    const dropdown = document.getElementById("dropdown");
    const selectedOption = dropdown.options[dropdown.selectedIndex];
    const zonePath = selectedOption.dataset.zone;
    const pointsPath = selectedOption.dataset.points;

    if (!zonePath && !pointsPath) {
        console.log("Aucun ensemble de données sélectionné.");
        return;
    }

    // Supprime les couches existantes sauf les points de base
    if (currentZoneLayer) {
        map.removeLayer(currentZoneLayer);
        currentZoneLayer = null;
    }
    if (currentPointsLayer) {
        map.removeLayer(currentPointsLayer);
        currentPointsLayer = null;
    }
    if (fastestPointsLayer) {
        fastestPointsLayer.clearLayers();
    }
    if (routesLayer) {
        routesLayer.clearLayers();
    }
    if (interventionLayer) {
        interventionLayer.clearLayers();
    }

    // Charge les nouvelles données
    if (zonePath) await loadFlatGeobuf(zonePath, 'zone');
    if (pointsPath) await loadFlatGeobuf(pointsPath, 'points');
}

// Charge les données initialement sélectionnées
loadSelectedData();

// Ajoute un écouteur d'événements pour les changements dans le menu déroulant
document.getElementById("dropdown").addEventListener("change", loadSelectedData);
