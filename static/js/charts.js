/* Stock vs Sales zig-zag line chart (Chart.js). X axis = date, Y axis = quantity. */
function renderStockSalesChart(canvasId, dataId) {
  var canvas = document.getElementById(canvasId); if (!canvas) return;
  var box = canvas.parentElement, empty = box.querySelector('.chart-empty');
  var d = JSON.parse(document.getElementById(dataId).textContent);
  var hasData = d.stock.some(function (v) { return v > 0; }) || d.sales.some(function (v) { return v > 0; });
  if (typeof Chart === 'undefined') {            // CDN not reachable
    canvas.style.display = 'none';
    if (empty) { empty.style.display = 'grid'; empty.innerHTML = '<div><strong>Chart could not load</strong>Check your internet connection and refresh the page.</div>'; }
    return;
  }
  if (!hasData) { canvas.style.display = 'none'; if (empty) empty.style.display = 'grid'; return; }
  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var labels = d.labels.map(function (s) { var p = s.split('-'); return parseInt(p[2], 10) + ' ' + MON[parseInt(p[1], 10) - 1]; });
  var ctx = canvas.getContext('2d');
  function fill(c1, c2) { var g = ctx.createLinearGradient(0, 0, 0, 320); g.addColorStop(0, c1); g.addColorStop(1, c2); return g; }
  var many = labels.length > 31;
  Chart.defaults.font.family = "'Manrope','Noto Sans Tamil',system-ui,sans-serif";
  function ds(label, data, color, area) {
    return { label: label, data: data, borderColor: color, backgroundColor: fill(area, 'rgba(255,255,255,0)'), fill: true,
      tension: 0, borderWidth: 3, borderJoinStyle: 'miter',          /* tension 0 = sharp zig-zag lines */
      pointRadius: many ? 2 : 5, pointHoverRadius: 7, pointBackgroundColor: '#fff', pointBorderColor: color, pointBorderWidth: 2.5 };
  }
  new Chart(ctx, {
    type: 'line',
    data: { labels: labels, datasets: [
      ds('Stock bought', d.stock, '#0E7C7B', 'rgba(20,184,166,.28)'),
      ds('Sales', d.sales, '#F97316', 'rgba(251,146,60,.25)')
    ] },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', align: 'end', labels: { usePointStyle: true, pointStyle: 'line', boxWidth: 28, padding: 16, font: { weight: '700' } } },
        tooltip: { backgroundColor: '#14212B', padding: 12, titleFont: { weight: '800' }, bodySpacing: 6, cornerRadius: 8,
          callbacks: { footer: function (items) { var s = items[0].parsed.y, a = items[1] ? items[1].parsed.y : 0; return 'Balance: ' + (s - a).toLocaleString('en-IN'); } } }
      },
      scales: {
        x: { grid: { display: false }, title: { display: true, text: 'Date', color: '#667684', font: { weight: '700' } },
             ticks: { color: '#667684', maxRotation: many ? 60 : 0, autoSkip: true, maxTicksLimit: many ? 20 : 31 } },
        y: { beginAtZero: true, title: { display: true, text: 'Quantity (units)', color: '#667684', font: { weight: '700' } },
             grid: { color: '#EDF0F3' }, border: { display: false }, ticks: { color: '#667684', precision: 0 } }
      }
    }
  });
}
