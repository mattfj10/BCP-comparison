const meta = document.getElementById("meta");
const unitList = document.getElementById("unitList");
const comparisonGrid = document.getElementById("comparisonGrid");
const template = document.getElementById("unitCardTemplate");
const toggleDiff = document.getElementById("toggleDiff");
const searchUnits = document.getElementById("searchUnits");
const fontSize = document.getElementById("fontSize");
const compactMode = document.getElementById("compactMode");
const resultsCount = document.getElementById("resultsCount");

const SETTINGS_KEY = "bcpComparerSettings";

const settings = {
  search: "",
  fontSize: 17,
  compactMode: false,
  showDiff: true,
  ...loadSettings()
};

applySettings();
const data = await loadData();
render(data);

searchUnits.addEventListener("input", () => {
  settings.search = searchUnits.value.trim();
  saveSettings();
  rerenderCards(data);
});

toggleDiff.addEventListener("change", () => {
  settings.showDiff = toggleDiff.checked;
  saveSettings();
  rerenderCards(data);
});

fontSize.addEventListener("input", () => {
  settings.fontSize = Number(fontSize.value);
  applySettings();
  saveSettings();
});

compactMode.addEventListener("change", () => {
  settings.compactMode = compactMode.checked;
  applySettings();
  saveSettings();
});

async function loadData() {
  try {
    const response = await fetch("/api/morning-prayer", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to load comparison data: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    meta.innerHTML = `<h2>Unable to load data</h2><p class="small">${escapeHtml(error.message)}</p>`;
    return { metadata: { title: "No data", notes: [], source_attempts: [] }, units: [] };
  }
}

function render(dataset) {
  meta.innerHTML = `
    <h2>${escapeHtml(dataset.metadata.title)}</h2>
    <p class="small">${dataset.metadata.notes.map(escapeHtml).join(" ")}</p>
    <p class="small"><strong>Source attempts:</strong> ${dataset.metadata.source_attempts
      .map((url) => `<code>${escapeHtml(url)}</code>`)
      .join(" · ")}</p>
  `;

  dataset.units.forEach((unit, index) => {
    const item = document.createElement("li");
    item.dataset.unitId = unit.id;
    item.innerHTML = `<strong>${escapeHtml(unit.label)}</strong> <code>${escapeHtml(unit.id)}</code>`;
    unitList.appendChild(item);

    const fragment = template.content.cloneNode(true);
    const card = fragment.querySelector(".unit-card");
    card.dataset.unitId = unit.id;

    fragment.querySelector("h3").textContent = `${index + 1}. ${unit.label}`;
    fragment.querySelector(".unit-id").textContent = unit.id;
    comparisonGrid.appendChild(fragment);
  });

  rerenderCards(dataset);
}

function rerenderCards(dataset) {
  const query = settings.search.toLowerCase();
  let visibleCount = 0;

  document.querySelectorAll(".unit-card").forEach((card) => {
    const unit = dataset.units.find((entry) => entry.id === card.dataset.unitId);
    if (!unit) return;

    const matches = matchesQuery(unit, query);
    card.hidden = !matches;

    const listItem = unitList.querySelector(`[data-unit-id="${card.dataset.unitId}"]`);
    if (listItem) listItem.hidden = !matches;

    if (!matches) return;
    visibleCount++;

    const left = card.querySelector(".text1662");
    const right = card.querySelector(".text1928");

    if (settings.showDiff) {
      left.innerHTML = renderDiff(unit.text1662, unit.text1928, "left");
      right.innerHTML = renderDiff(unit.text1662, unit.text1928, "right");
      return;
    }

    left.textContent = unit.text1662;
    right.textContent = unit.text1928;
  });

  resultsCount.textContent = `${visibleCount} of ${dataset.units.length} units shown`;
}

function matchesQuery(unit, query) {
  if (!query) return true;
  const haystack = `${unit.id} ${unit.label} ${unit.text1662} ${unit.text1928}`.toLowerCase();
  return haystack.includes(query);
}

function applySettings() {
  document.documentElement.style.setProperty("--base-font-size", `${settings.fontSize}px`);
  document.body.classList.toggle("compact", Boolean(settings.compactMode));

  searchUnits.value = settings.search;
  toggleDiff.checked = Boolean(settings.showDiff);
  fontSize.value = String(settings.fontSize);
  compactMode.checked = Boolean(settings.compactMode);
}

function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function renderDiff(text1662, text1928, side) {
  const a = tokenize(text1662);
  const b = tokenize(text1928);
  const lcs = buildLcsTable(a, b);

  const leftOutput = [];
  const rightOutput = [];

  let i = 0;
  let j = 0;

  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      leftOutput.push(escapeHtml(a[i]));
      rightOutput.push(escapeHtml(b[j]));
      i++;
      j++;
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      leftOutput.push(`<span class="diff-removed">${escapeHtml(a[i])}</span>`);
      i++;
    } else {
      rightOutput.push(`<span class="diff-added">${escapeHtml(b[j])}</span>`);
      j++;
    }
  }

  while (i < a.length) {
    leftOutput.push(`<span class="diff-removed">${escapeHtml(a[i])}</span>`);
    i++;
  }

  while (j < b.length) {
    rightOutput.push(`<span class="diff-added">${escapeHtml(b[j])}</span>`);
    j++;
  }

  return side === "left" ? leftOutput.join(" ") : rightOutput.join(" ");
}

function tokenize(text) {
  return text.split(/\s+/).filter(Boolean);
}

function buildLcsTable(a, b) {
  const table = Array(a.length + 1)
    .fill(null)
    .map(() => Array(b.length + 1).fill(0));

  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      table[i][j] = a[i] === b[j] ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }

  return table;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
