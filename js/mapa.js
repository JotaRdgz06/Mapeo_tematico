var mapa = L.map('mapa').setView([10.011074,-84.131238], 16);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; Colaboradores de OpenStreetMap'
}).addTo(mapa);

var COLORES = {
  'Aceras': '#2980b9',
  'Cruces y tránsito': '#c0392b',
  'Seguridad': '#e67e22',
  'Espacios de permanencia': '#27ae60',
  'Transporte público': '#8e44ad',
  'Recorrido': '#34495e',
  'Otros': '#7f8c8d'
};

window.addEventListener('load', function () {
  fetch('datos.geojson?v=' + Date.now())
    .then(function (r) { return r.json(); })
    .then(function (datos) {
      document.dispatchEvent(new CustomEvent('datos-listos', { detail: datos }));
    })
    .catch(function (err) { console.error('No se pudo cargar datos.geojson', err); });
});
