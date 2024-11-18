// Initialise la carte avec le fond de carte Stamen Toner pour un thème gris détaillé
const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner-background/{z}/{x}/{y}.png', {
    maxZoom: 20,
    attribution: 'Cartes fournies par <a href="http://stamen.com">Stamen Design</a>, ' +
                 '<a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; ' +
                 'Données cartographiques &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributeurs'
}).addTo(map);

let currentZoneLayer = null;
let currentPointsLayer = null;

/**
 * Fonction pour charger des données FlatGeobuf et les ajouter à la carte
 * 
 * @param {string} url - URL du fichier FlatGeobuf à charger
 * @param {string} layerType - Type de couche à ajouter ('zone' ou 'points')
 */
async function loadFlatGeobuf(url, layerType) {
    try {
        // Effectue une requête pour obtenir les données FlatGeobuf
        const response = await fetch(url);
        if (!response.ok) {
            console.error(`Échec de la récupération de ${url} : ${response.statusText}`);
            return;
        }

        // Utilise flatgeobuf.deserialize qui retourne un itérateur asynchrone
        const asyncIterator = flatgeobuf.deserialize(response.body);

        // Crée une collection de caractéristiques GeoJSON
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

        // Ajoute la couche appropriée en fonction du type
        if (layerType === 'zone') {
            currentZoneLayer = L.geoJSON(geojson, {
                style: {
                    color: '#4a4a4a', // Contour gris foncé
                    weight: 2,
                    fill: false
                },
                onEachFeature: function (feature, layer) {
                    if (feature.properties && feature.properties.name) {
                        layer.bindPopup(`<strong>Zone :</strong> ${feature.properties.name}`);
                    }
                }
            }).addTo(map);
            // Ajuste la vue de la carte pour inclure toute la couche de zone
            map.fitBounds(currentZoneLayer.getBounds());
        } else if (layerType === 'points') {
            currentPointsLayer = L.geoJSON(geojson, {
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, {
                        radius: 5,
                        fillColor: '#808080', // Couleur grise
                        color: '#808080',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                },
                onEachFeature: function (feature, layer) {
                    if (feature.properties && feature.properties.name) {
                        layer.bindPopup(`<strong>Point :</strong> ${feature.properties.name}`);
                    }
                }
            }).addTo(map);
        }
    } catch (error) {
        console.error(`Erreur lors du chargement des données FlatGeobuf depuis ${url} :`, error);
    }
}

// Charge les données initialement sélectionnées
const dropdown = document.getElementById("dropdown");
loadSelectedData();

// Ajoute un écouteur d'événements pour les changements dans le menu déroulant
dropdown.addEventListener("change", loadSelectedData);

/**
 * Fonction pour charger les données sélectionnées dans le menu déroulant
 */
async function loadSelectedData() {
    // Obtient l'option sélectionnée
    const selectedOption = dropdown.options[dropdown.selectedIndex];
    const zonePath = selectedOption.dataset.zone;
    const pointsPath = selectedOption.dataset.points;

    if (!zonePath && !pointsPath) {
        console.log("Aucun ensemble de données sélectionné.");
        // Optionnellement, vide la carte ou affiche un message
        return;
    }

    console.log("Chemin de la zone :", zonePath);
    console.log("Chemin des points :", pointsPath);

    // Supprime les couches existantes de la carte
    if (currentZoneLayer) {
        map.removeLayer(currentZoneLayer);
        currentZoneLayer = null;
    }
    if (currentPointsLayer) {
        map.removeLayer(currentPointsLayer);
        currentPointsLayer = null;
    }

    // Charge les nouvelles couches FlatGeobuf
    if (zonePath) {
        await loadFlatGeobuf(zonePath, 'zone');
    }
    if (pointsPath) {
        await loadFlatGeobuf(pointsPath, 'points');
    }
}
