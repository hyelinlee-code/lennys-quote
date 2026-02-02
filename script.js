// ===== State =====
let allQuotes = [];
let currentLang = 'text_ko';

// ===== DOM References =====
const grid = document.getElementById('quotes-grid');
const loading = document.getElementById('loading');
const emptyState = document.getElementById('empty-state');
const quoteCount = document.getElementById('quote-count');
const filterSelect = document.getElementById('filter-function');
const modalOverlay = document.getElementById('modal-overlay');
const modalClose = document.getElementById('modal-close');
const contextToggle = document.getElementById('context-toggle');
const contextText = document.getElementById('modal-context');
const flipCard = document.getElementById('flip-card');
const flipCardInner = document.getElementById('flip-card-inner');

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

// ===== Render Cards =====
function renderCards() {
  var filterValue = filterSelect.value;
  var filtered = allQuotes;

  if (filterValue !== 'All') {
    filtered = allQuotes.filter(function (q) {
      return q.speaker_function === filterValue;
    });
  }

  grid.innerHTML = '';

  if (filtered.length === 0) {
    emptyState.style.display = 'block';
    quoteCount.textContent = '0 quotes';
    return;
  }

  emptyState.style.display = 'none';
  quoteCount.textContent = filtered.length + ' quote' + (filtered.length !== 1 ? 's' : '');

  filtered.forEach(function (quote, index) {
    var card = document.createElement('div');
    card.className = 'quote-card';

    var truncated = quote.text;

    card.innerHTML =
      '<div class="card-text">' + escapeHTML(truncated) + '</div>' +
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

// ===== Modal =====
function openModal(quote) {
  // English original
  document.getElementById('modal-text-en').textContent = quote.text || '';

  // Translation
  var langLabels = {
    text_ko: '한국어 번역',
    text_zh: '中文翻译',
    text_es: 'Traducción al Español'
  };
  document.getElementById('modal-trans-label').textContent = langLabels[currentLang] || 'Translation';
  document.getElementById('modal-text-trans').textContent = quote[currentLang] || '—';

  // Speaker & function
  document.getElementById('modal-speaker').textContent = quote.speaker || '';
  document.getElementById('modal-function').textContent = quote.speaker_function || '';

  // Expertise tags
  renderTags('modal-expertise', quote.speaker_expertise);
  toggleRow('modal-expertise-row', quote.speaker_expertise);

  // Topics tags
  renderTags('modal-topics', quote.topics);
  toggleRow('modal-topics-row', quote.topics);

  // Vocabulary tags
  renderTags('modal-vocab', quote.vocabulary_highlights);
  toggleRow('modal-vocab-row', quote.vocabulary_highlights);

  // Difficulty
  var diffEl = document.getElementById('modal-difficulty');
  diffEl.textContent = quote.difficulty_level || '';
  diffEl.style.display = quote.difficulty_level ? '' : 'none';

  // Timestamp
  document.getElementById('modal-timestamp').textContent = quote.timestamp ? '⏱ ' + quote.timestamp : '';

  // Context
  var ctx = (quote.context || '').trim();
  document.getElementById('modal-context').textContent = ctx;
  document.getElementById('modal-context-wrapper').style.display = ctx ? '' : 'none';
  contextText.classList.remove('open');
  contextToggle.textContent = 'Show context ▾';

  // Reset flip to English side
  flipCardInner.classList.remove('flipped');

  // Show
  modalOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  // Match flip card height to whichever side is taller
  requestAnimationFrame(function () {
    syncFlipCardHeight();
  });
}

function syncFlipCardHeight() {
  var front = flipCardInner.querySelector('.flip-card-front');
  var back = flipCardInner.querySelector('.flip-card-back');
  // Reset so we can measure natural heights
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

  var items = rawString.split(',');
  items.forEach(function (item) {
    var text = item.trim();
    if (!text) return;
    var span = document.createElement('span');
    span.className = 'tag';
    span.textContent = text;
    container.appendChild(span);
  });
}

function toggleRow(rowId, value) {
  var row = document.getElementById(rowId);
  row.style.display = (value && value.trim()) ? 'flex' : 'none';
}

// ===== Utility =====
function escapeHTML(str) {
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
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

// Filter dropdown
filterSelect.addEventListener('change', renderCards);

// Modal close
modalClose.addEventListener('click', closeModal);

modalOverlay.addEventListener('click', function (e) {
  if (e.target === modalOverlay) {
    closeModal();
  }
});

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    closeModal();
  }
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
