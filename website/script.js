// ===== State =====
var allQuotes = [];
var currentLang = 'text_ko';

// ===== DOM References =====
var grid = document.getElementById('quotes-grid');
var loading = document.getElementById('loading');
var emptyState = document.getElementById('empty-state');
var quoteCount = document.getElementById('quote-count');
var filterSelect = document.getElementById('filter-function');
var modalOverlay = document.getElementById('modal-overlay');
var modalClose = document.getElementById('modal-close');
var contextToggle = document.getElementById('context-toggle');
var contextText = document.getElementById('modal-context');
var flipCard = document.getElementById('flip-card');
var flipCardInner = document.getElementById('flip-card-inner');

// New filter elements
var searchInput = document.getElementById('search-input');
var searchClear = document.getElementById('search-clear');
var expertiseToggle = document.getElementById('expertise-toggle');
var expertiseList = document.getElementById('expertise-list');
var expertiseCount = document.getElementById('expertise-count');
var clearAllBtn = document.getElementById('clear-all-btn');
var filterStatus = document.getElementById('filter-status');
var filterStatusMobile = document.getElementById('filter-status-mobile');
var mobileFilterToggle = document.getElementById('mobile-filter-toggle');
var sidebar = document.getElementById('sidebar');
var toggleArrow = document.getElementById('toggle-arrow');

// Topics filter elements
var topicsToggle = document.getElementById('topics-toggle');
var topicsList = document.getElementById('topics-list');
var topicsCount = document.getElementById('topics-count');

// Checkbox collections
var expertiseCheckboxes = expertiseList.querySelectorAll('input[type="checkbox"]');
var difficultyCheckboxes = document.querySelectorAll('input[name="difficulty"]');
var topicCheckboxes = topicsList.querySelectorAll('input[type="checkbox"]');

// ===== Load CSV =====
function loadCSV() {
  Papa.parse('quotes_complete.csv', {
    download: true,
    header: true,
    skipEmptyLines: true,
    complete: function (results) {
      allQuotes = results.data.filter(function (row) {
        return row.text && row.text.trim() !== '';
      });
      loading.style.display = 'none';
      renderCards();
    },
    error: function () {
      loading.textContent = 'Failed to load quotes. Make sure quotes_complete.csv is in the same folder.';
    }
  });
}

// ===== Filter Logic =====
function getFilteredQuotes() {
  var roleValue = filterSelect.value;
  var searchTerm = searchInput.value.trim().toLowerCase();

  // Gather selected expertise values
  var selectedExpertise = [];
  expertiseCheckboxes.forEach(function (cb) {
    if (cb.checked) selectedExpertise.push(cb.value);
  });

  // Gather selected difficulty values
  var selectedDifficulty = [];
  difficultyCheckboxes.forEach(function (cb) {
    if (cb.checked) selectedDifficulty.push(cb.value);
  });

  // Gather selected topic values
  var selectedTopics = [];
  topicCheckboxes.forEach(function (cb) {
    if (cb.checked) selectedTopics.push(cb.value);
  });

  return allQuotes.filter(function (q) {
    // Role filter (AND)
    if (roleValue !== 'All' && q.speaker_function !== roleValue) return false;

    // Search filter (AND) — searches English text + selected language translation
    if (searchTerm) {
      var en = (q.text || '').toLowerCase();
      var trans = (q[currentLang] || '').toLowerCase();
      if (en.indexOf(searchTerm) === -1 && trans.indexOf(searchTerm) === -1) return false;
    }

    // Expertise filter (OR within, AND with others)
    if (selectedExpertise.length > 0) {
      var quoteExpertise = (q.speaker_expertise || '').toLowerCase();
      var matchesAny = selectedExpertise.some(function (exp) {
        return quoteExpertise.indexOf(exp.toLowerCase()) !== -1;
      });
      if (!matchesAny) return false;
    }

    // Difficulty filter (OR within, AND with others)
    if (selectedDifficulty.length > 0) {
      if (selectedDifficulty.indexOf(q.difficulty_level) === -1) return false;
    }

    // Topic filter (OR within, AND with others)
    if (selectedTopics.length > 0) {
      var quoteTopics = (q.topics || '').toLowerCase();
      var matchesAnyTopic = selectedTopics.some(function (topic) {
        return quoteTopics.indexOf(topic.toLowerCase()) !== -1;
      });
      if (!matchesAnyTopic) return false;
    }

    return true;
  });
}

// ===== Active Filter Count =====
function getActiveFilterCount() {
  var count = 0;
  if (filterSelect.value !== 'All') count++;
  if (searchInput.value.trim() !== '') count++;

  expertiseCheckboxes.forEach(function (cb) {
    if (cb.checked) count++;
  });
  difficultyCheckboxes.forEach(function (cb) {
    if (cb.checked) count++;
  });
  topicCheckboxes.forEach(function (cb) {
    if (cb.checked) count++;
  });

  return count;
}

function updateFilterUI() {
  var count = getActiveFilterCount();

  // Status text
  var statusText = count > 0 ? count + ' filter' + (count !== 1 ? 's' : '') + ' active' : '';
  filterStatus.textContent = statusText;
  filterStatusMobile.textContent = statusText;

  // Clear all button
  if (count > 0) {
    clearAllBtn.classList.add('visible');
  } else {
    clearAllBtn.classList.remove('visible');
  }

  // Expertise checked count badge
  var expChecked = 0;
  expertiseCheckboxes.forEach(function (cb) {
    if (cb.checked) expChecked++;
  });
  if (expChecked > 0) {
    expertiseCount.textContent = expChecked;
    expertiseCount.classList.add('visible');
  } else {
    expertiseCount.textContent = '';
    expertiseCount.classList.remove('visible');
  }

  // Topics checked count badge
  var topChecked = 0;
  topicCheckboxes.forEach(function (cb) {
    if (cb.checked) topChecked++;
  });
  if (topChecked > 0) {
    topicsCount.textContent = topChecked;
    topicsCount.classList.add('visible');
  } else {
    topicsCount.textContent = '';
    topicsCount.classList.remove('visible');
  }

  // Search clear button
  if (searchInput.value.length > 0) {
    searchClear.classList.add('visible');
  } else {
    searchClear.classList.remove('visible');
  }
}

// ===== Render Cards =====
function renderCards() {
  var filtered = getFilteredQuotes();
  updateFilterUI();

  grid.innerHTML = '';

  if (filtered.length === 0) {
    emptyState.style.display = 'block';
    quoteCount.textContent = '0 quotes';
    return;
  }

  emptyState.style.display = 'none';
  quoteCount.textContent = filtered.length + ' quote' + (filtered.length !== 1 ? 's' : '');

  filtered.forEach(function (quote) {
    var card = document.createElement('div');
    card.className = 'quote-card';

    card.innerHTML =
      '<div class="card-text">' + escapeHTML(quote.text) + '</div>' +
      '<div class="card-footer">' +
        '<span class="card-speaker">' + escapeHTML(quote.speaker || '') + '</span>' +
        '<span class="card-function">' + escapeHTML(quote.speaker_function || '') + '</span>' +
      '</div>';

    card.addEventListener('click', function () {
      openModal(quote);
    });

    grid.appendChild(card);
  });
}

// ===== Clear All Filters =====
function clearAllFilters() {
  searchInput.value = '';
  filterSelect.value = 'All';

  expertiseCheckboxes.forEach(function (cb) { cb.checked = false; });
  difficultyCheckboxes.forEach(function (cb) { cb.checked = false; });
  topicCheckboxes.forEach(function (cb) { cb.checked = false; });

  renderCards();
}

// ===== Modal =====
function openModal(quote) {
  document.getElementById('modal-text-en').textContent = quote.text || '';

  var langLabels = {
    text_ko: '한국어 번역',
    text_zh: '中文翻译',
    text_es: 'Traducción al Español'
  };
  document.getElementById('modal-trans-label').textContent = langLabels[currentLang] || 'Translation';
  document.getElementById('modal-text-trans').textContent = quote[currentLang] || '—';

  document.getElementById('modal-speaker').textContent = quote.speaker || '';
  document.getElementById('modal-function').textContent = quote.speaker_function || '';

  renderTags('modal-expertise', quote.speaker_expertise);
  toggleRow('modal-expertise-row', quote.speaker_expertise);

  renderTags('modal-topics', quote.topics);
  toggleRow('modal-topics-row', quote.topics);

  renderTags('modal-vocab', quote.vocabulary_highlights);
  toggleRow('modal-vocab-row', quote.vocabulary_highlights);

  var diffEl = document.getElementById('modal-difficulty');
  diffEl.textContent = quote.difficulty_level || '';
  diffEl.style.display = quote.difficulty_level ? '' : 'none';

  document.getElementById('modal-timestamp').textContent = quote.timestamp ? '⏱ ' + quote.timestamp : '';

  var ctx = (quote.context || '').trim();
  document.getElementById('modal-context').textContent = ctx;
  document.getElementById('modal-context-wrapper').style.display = ctx ? '' : 'none';
  contextText.classList.remove('open');
  contextToggle.textContent = 'Show context ▾';

  flipCardInner.classList.remove('flipped');

  modalOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  requestAnimationFrame(function () {
    syncFlipCardHeight();
  });
}

function syncFlipCardHeight() {
  var front = flipCardInner.querySelector('.flip-card-front');
  var back = flipCardInner.querySelector('.flip-card-back');
  flipCardInner.style.minHeight = '';
  front.style.minHeight = '';
  back.style.minHeight = '';
  var h = Math.max(front.scrollHeight, back.scrollHeight);
  flipCardInner.style.minHeight = h + 'px';
  front.style.minHeight = h + 'px';
  back.style.minHeight = h + 'px';
}

function closeModal() {
  modalOverlay.classList.remove('open');
  document.body.style.overflow = '';
}

function renderTags(containerId, rawString) {
  var container = document.getElementById(containerId);
  container.innerHTML = '';
  if (!rawString || rawString.trim() === '') return;

  rawString.split(',').forEach(function (item) {
    var text = item.trim();
    if (!text) return;
    var span = document.createElement('span');
    span.className = 'tag';
    span.textContent = text;
    container.appendChild(span);
  });
}

function toggleRow(rowId, value) {
  document.getElementById(rowId).style.display = (value && value.trim()) ? 'flex' : 'none';
}

// ===== Utility =====
function escapeHTML(str) {
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ===== Debounce for search =====
var searchTimer = null;
function onSearchInput() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(renderCards, 180);
}

// ===== Event Listeners =====

// Language buttons
document.querySelectorAll('.lang-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.lang-btn').forEach(function (b) {
      b.classList.remove('active');
    });
    btn.classList.add('active');
    currentLang = btn.getAttribute('data-lang');
    renderCards();
  });
});

// Search
searchInput.addEventListener('input', onSearchInput);
searchClear.addEventListener('click', function () {
  searchInput.value = '';
  searchInput.focus();
  renderCards();
});

// Role dropdown
filterSelect.addEventListener('change', renderCards);

// Expertise checkboxes
expertiseCheckboxes.forEach(function (cb) {
  cb.addEventListener('change', renderCards);
});

// Difficulty checkboxes
difficultyCheckboxes.forEach(function (cb) {
  cb.addEventListener('change', renderCards);
});

// Topic checkboxes
topicCheckboxes.forEach(function (cb) {
  cb.addEventListener('change', renderCards);
});

// Topics section toggle
topicsToggle.addEventListener('click', function () {
  var expanded = topicsToggle.getAttribute('aria-expanded') === 'true';
  topicsToggle.setAttribute('aria-expanded', String(!expanded));
  if (expanded) {
    topicsList.classList.add('collapsed');
  } else {
    topicsList.classList.remove('collapsed');
  }
});

// Expertise section toggle
expertiseToggle.addEventListener('click', function () {
  var expanded = expertiseToggle.getAttribute('aria-expanded') === 'true';
  expertiseToggle.setAttribute('aria-expanded', String(!expanded));
  if (expanded) {
    expertiseList.classList.add('collapsed');
  } else {
    expertiseList.classList.remove('collapsed');
  }
});

// Clear all
clearAllBtn.addEventListener('click', clearAllFilters);

// Mobile filter toggle
mobileFilterToggle.addEventListener('click', function () {
  sidebar.classList.toggle('open');
  toggleArrow.classList.toggle('open');
});

// Modal close
modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', function (e) {
  if (e.target === modalOverlay) closeModal();
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeModal();
});

// Flip card toggle
flipCard.addEventListener('click', function () {
  flipCardInner.classList.toggle('flipped');
});

// Context toggle
contextToggle.addEventListener('click', function () {
  var isOpen = contextText.classList.toggle('open');
  contextToggle.textContent = isOpen ? 'Hide context ▴' : 'Show context ▾';
});

// ===== Init =====
loadCSV();
