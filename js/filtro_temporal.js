document.addEventListener('datos-listos', function () {
  if (!window.capaTrazas) {
    console.warn('filtro-temporal: no existe capaTrazas, no se crea el filtro');
    return;
  }

  // Lista completa: hay que guardarla ANTES de ocultar nada,
  // porque las capas ocultas dejan de aparecer en getLayers().
  var todas = capaTrazas.getLayers();
  if (todas.length === 0) return;

  var fechas = todas.map(function (capa) {
    return capa.feature.properties.fecha;
  }).sort();
  var fechaMin = fechas[0];
  var fechaMax = fechas[fechas.length - 1];

  // Utilidades de fecha 

  // Resta n días a un texto 'AAAA-MM-DD' y devuelve otro texto 'AAAA-MM-DD'.
  // Se trabaja en hora local (T00:00:00) para que no se corra un día por UTC.
  function restarDias(texto, n) {
    var d = new Date(texto + 'T00:00:00');
    d.setDate(d.getDate() - n);
    var mes = String(d.getMonth() + 1).padStart(2, '0');
    var dia = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + mes + '-' + dia;
  }

  // Lógica del filtro 

  // Muestra solo las trazas con fecha >= desde. Si desde es vacío, muestra todas.
  function filtrar(desde) {
    var visibles = 0;
    todas.forEach(function (capa) {
      var mostrar = !desde || capa.feature.properties.fecha >= desde;
      var estaEnMapa = capaTrazas.hasLayer(capa);
      if (mostrar && !estaEnMapa) capaTrazas.addLayer(capa);
      if (!mostrar && estaEnMapa) capaTrazas.removeLayer(capa);
      if (mostrar) visibles++;
    });
    estado.textContent = 'Mostrando ' + visibles + ' de ' + todas.length + ' trazas';
  }

  // Control de Leaflet

  var campoFecha, selectorDias, estado;

  var control = L.control({ position: 'topright' });

  control.onAdd = function () {
    var div = L.DomUtil.create('div', 'leaflet-bar filtro-temporal');
    div.style.background = 'white';
    div.style.padding = '8px 10px';
    div.style.font = '13px/1.4 sans-serif';
    div.style.minWidth = '180px';

    div.innerHTML =
      '<strong>Filtro temporal</strong><br>' +
      '<label>Desde: <input type="date" id="ft-fecha"></label><br>' +
      '<label>Últimos: <select id="ft-dias">' +
      '  <option value="">—</option>' +
      '  <option value="7">7 días</option>' +
      '  <option value="30">30 días</option>' +
      '  <option value="90">90 días</option>' +
      '</select></label><br>' +
      '<button type="button" id="ft-todas" style="margin-top:4px;width:100%">Mostrar todas</button>' +
      '<div id="ft-estado" style="margin-top:4px;color:#555;font-size:12px"></div>';

    // Evita que hacer clic o arrastrar dentro del control mueva el mapa.
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);
    return div;
  };

  control.addTo(mapa);

  campoFecha = document.getElementById('ft-fecha');
  selectorDias = document.getElementById('ft-dias');
  estado = document.getElementById('ft-estado');
  var botonTodas = document.getElementById('ft-todas');

  campoFecha.min = fechaMin;
  campoFecha.max = fechaMax;

  campoFecha.addEventListener('change', function () {
    selectorDias.value = '';          // la fecha manual reemplaza al atajo
    filtrar(campoFecha.value);
  });

  selectorDias.addEventListener('change', function () {
    if (!selectorDias.value) {
      campoFecha.value = '';
      filtrar('');
      return;
    }
    // Ventana de N días que incluye el día de la traza más reciente.
    var desde = restarDias(fechaMax, Number(selectorDias.value) - 1);
    campoFecha.value = desde;
    filtrar(desde);
  });

  botonTodas.addEventListener('click', function () {
    campoFecha.value = '';
    selectorDias.value = '';
    filtrar('');
  });

  filtrar('');  // estado inicial: todas visibles
});
