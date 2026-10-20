/* Bill items: type a product -> pick from dropdown -> HSN fills automatically.
   Line total = quantity x unit price, so the price changes when the quantity changes. */
function initLineItems({products}) {
  var tbody = document.querySelector("#items tbody"), hidden = document.getElementById("items-json");
  var addBtn = document.getElementById("add-row"), subEl = document.getElementById("sub-total"),
      discEl = document.querySelector("[name=discount]"), grandEl = document.getElementById("grand-total");
  var inr = function (n) { return "₹" + (Number(n) || 0).toLocaleString("en-IN", {minimumFractionDigits: 2, maximumFractionDigits: 2}); };
  var norm = function (s) { return String(s || "").replace(/\s+/g, " ").trim().toLowerCase(); };
  var byName = {}; products.forEach(function (p) { byName[norm(p.name)] = p; });

  function el(tag, cls, attrs) { var e = document.createElement(tag); if (cls) e.className = cls; Object.assign(e, attrs || {}); return e; }

  function addRow() {
    var tr = el("tr"), chosen = null;
    var tdP = el("td", "bill-prod"), wrap = el("div", "ac-wrap");
    var name = el("input", "form-control", {type: "text", placeholder: "Type to search product", autocomplete: "off"});
    var list = el("ul", "ac-list"); list.hidden = true;
    wrap.append(name, list); tdP.appendChild(wrap);
    var tdH = el("td"), hsn = el("input", "form-control locked", {type: "text", readOnly: true, placeholder: "Auto"}); tdH.appendChild(hsn);
    var tdQ = el("td"), qty = el("input", "form-control qty", {type: "number", min: "1", step: "1", value: "1"});
    var qWrap = el("div", "qty-box"), minus = el("button", "qty-btn", {type: "button", textContent: "−"}), plus = el("button", "qty-btn", {type: "button", textContent: "+"});
    qWrap.append(minus, qty, plus); tdQ.appendChild(qWrap);
    var tdU = el("td"), unit = el("input", "form-control price", {type: "number", min: "0", step: "0.01", placeholder: "0.00"}); tdU.appendChild(unit);
    var tdT = el("td", "num cell-strong line-total", {textContent: inr(0)});
    var tdX = el("td"), rm = el("button", "btn btn-outline-danger btn-sm", {type: "button", innerHTML: "&times;", title: "Remove"}); tdX.appendChild(rm);
    tr.append(tdP, tdH, tdQ, tdU, tdT, tdX); tbody.appendChild(tr);

    function lineTotal() { return (parseFloat(qty.value) || 0) * (parseFloat(unit.value) || 0); }
    function refresh() { tdT.textContent = inr(lineTotal()); sync(); }
    function choose(p) { chosen = p; name.value = p.name; hsn.value = p.hsn_code || ""; unit.value = p.price ? Number(p.price).toFixed(2) : ""; list.hidden = true; refresh(); qty.focus(); qty.select(); }
    function clearChoice() { chosen = null; hsn.value = ""; }

    var shown = [], act = -1;
    function render() {
      var q = norm(name.value); list.innerHTML = ""; act = -1;
      if (!q) { list.hidden = true; return; }
      shown = products.filter(function (p) { return norm(p.name).indexOf(q) !== -1 || norm(p.hsn_code).indexOf(q) !== -1; })
        .sort(function (a, b) { return (norm(a.name).indexOf(q) === 0 ? 0 : 1) - (norm(b.name).indexOf(q) === 0 ? 0 : 1); }).slice(0, 8);
      if (!shown.length) { list.hidden = true; return; }
      shown.forEach(function (p) {
        var li = el("li"); li.append(el("span", "", {textContent: p.name}), el("span", "ac-hsn", {textContent: (p.hsn_code ? "HSN " + p.hsn_code + " · " : "") + inr(p.price)}));
        li.addEventListener("mousedown", function (e) { e.preventDefault(); choose(p); });
        list.appendChild(li);
      });
      list.hidden = false;
    }
    function mark() { Array.prototype.forEach.call(list.children, function (li, i) { li.classList.toggle("active", i === act); }); }
    name.addEventListener("input", function () { clearChoice(); render(); refresh(); });
    name.addEventListener("keydown", function (e) {
      if (list.hidden) return;
      if (e.key === "ArrowDown") { e.preventDefault(); act = (act + 1) % shown.length; mark(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); act = (act <= 0 ? shown.length : act) - 1; mark(); }
      else if (e.key === "Enter") { e.preventDefault(); choose(shown[act >= 0 ? act : 0]); }
      else if (e.key === "Escape") { list.hidden = true; }
    });
    name.addEventListener("blur", function () { list.hidden = true; var p = byName[norm(name.value)]; if (p && p !== chosen) choose(p); });
    minus.onclick = function () { qty.value = Math.max(1, (parseFloat(qty.value) || 1) - 1); refresh(); };
    plus.onclick = function () { qty.value = (parseFloat(qty.value) || 0) + 1; refresh(); };
    qty.oninput = refresh; unit.oninput = refresh;
    rm.onclick = function () { tr.remove(); sync(); if (!tbody.children.length) addRow(); };
    tr._get = function () { return chosen ? {product_id: chosen.id, quantity: qty.value, unit_price: unit.value || "0"} : null; };
    tr._total = lineTotal;
    name.focus();
  }

  function sync() {
    var rows = [], sub = 0;
    Array.prototype.forEach.call(tbody.children, function (tr) { var r = tr._get && tr._get(); if (r) { rows.push(r); sub += tr._total(); } });
    hidden.value = JSON.stringify(rows);
    var d = parseFloat(discEl && discEl.value) || 0;
    subEl.textContent = inr(sub); grandEl.textContent = inr(Math.max(sub - d, 0));
  }
  if (discEl) discEl.addEventListener("input", sync);
  addBtn.addEventListener("click", addRow); addRow();
  document.getElementById("bill-form").addEventListener("submit", function (e) {
    sync(); if (!JSON.parse(hidden.value || "[]").length) { e.preventDefault(); alert("Please pick at least one product from the list."); }
  });
}
