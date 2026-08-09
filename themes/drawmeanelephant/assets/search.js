(() => {
  const page = document.querySelector('[data-search-page]');
  if (!page) return;

  const form = page.querySelector('[data-search-form]');
  const input = form && form.querySelector('input[name="q"]');
  const status = page.querySelector('[data-search-status]');
  const resultsList = page.querySelector('[data-search-results]');
  const noResults = page.querySelector('[data-search-no-results]');
  if (!form || !input || !resultsList) return;

  const normalize = (value) => String(value || '')
    .toLocaleLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim();

  const compact = (value) => normalize(value).replace(/\s+/g, '');

  const tokenize = (value) => normalize(value).split(/\s+/).filter(Boolean);

  const prepareDocument = (documentRecord) => {
    const sections = Array.isArray(documentRecord.sections)
      ? documentRecord.sections
      : [];
    const sectionText = sections.map((section) => [
      section && section.heading,
      section && section.text,
      section && section.code,
    ].filter(Boolean).join(' ')).join(' ');
    const title = documentRecord.title || documentRecord.path || 'Untitled page';
    const searchable = normalize(`${title} ${sectionText} ${documentRecord.path || ''}`);

    return {
      path: documentRecord.path || '',
      title,
      sections,
      titleSearch: normalize(title),
      searchable,
      compactSearch: searchable.replace(/\s+/g, ''),
    };
  };

  const documentMatches = (documentRecord, terms) => terms.every((term) => (
    documentRecord.searchable.includes(term)
    || documentRecord.compactSearch.includes(compact(term))
  ));

  const scoreDocument = (documentRecord, query, terms) => {
    let score = 0;
    const compactQuery = compact(query);

    if (documentRecord.titleSearch.includes(query)) score += 100;
    if (documentRecord.titleSearch.includes(compactQuery)) score += 20;
    if (documentRecord.searchable.includes(query)) score += 25;

    terms.forEach((term) => {
      if (documentRecord.titleSearch.includes(term)) score += 35;
      else if (documentRecord.searchable.includes(term)) score += 8;
      else if (documentRecord.compactSearch.includes(compact(term))) score += 5;
    });

    return score;
  };

  const makeSnippet = (documentRecord, terms) => {
    const source = documentRecord.sections.map((section) => [
      section && section.text,
      section && section.code,
    ].filter(Boolean).join(' ')).filter(Boolean).join(' ').replace(/\s+/g, ' ');
    if (!source) return '';

    const sourceSearch = normalize(source);
    const matchPosition = terms.reduce((position, term) => {
      const nextPosition = sourceSearch.indexOf(term);
      return position === -1 ? nextPosition : Math.min(position, nextPosition === -1 ? position : nextPosition);
    }, -1);
    const start = Math.max(0, (matchPosition === -1 ? 0 : matchPosition) - 70);
    const end = Math.min(source.length, start + 190);
    const excerpt = source.slice(start, end).trim();

    return `${start > 0 ? '…' : ''}${excerpt}${end < source.length ? '…' : ''}`;
  };

  const renderResults = (documents, query) => {
    resultsList.replaceChildren();
    if (noResults) noResults.hidden = true;

    const normalizedQuery = normalize(query);
    const terms = tokenize(query);
    if (!normalizedQuery || !terms.length) {
      if (status) status.textContent = 'Enter a word or phrase to search the archive.';
      return;
    }

    const matches = documents
      .filter((documentRecord) => documentMatches(documentRecord, terms))
      .map((documentRecord) => ({
        documentRecord,
        score: scoreDocument(documentRecord, normalizedQuery, terms),
      }))
      .sort((left, right) => (
        right.score - left.score
        || left.documentRecord.title.localeCompare(right.documentRecord.title)
        || left.documentRecord.path.localeCompare(right.documentRecord.path)
      ));

    if (!matches.length) {
      if (status) status.textContent = `No results for “${query.trim()}”.`;
      if (noResults) noResults.hidden = false;
      return;
    }

    const visibleMatches = matches.slice(0, 60);
    if (status) {
      status.textContent = matches.length > visibleMatches.length
        ? `Showing ${visibleMatches.length} of ${matches.length} results.`
        : `${matches.length} ${matches.length === 1 ? 'result' : 'results'} found.`;
    }

    visibleMatches.forEach(({ documentRecord }) => {
      const item = document.createElement('li');
      item.className = 'search-result';

      const title = document.createElement('h2');
      title.className = 'search-result-title';
      const link = document.createElement('a');
      link.href = `/${documentRecord.path.replace(/^\/+/, '')}`;
      link.textContent = documentRecord.title;
      title.append(link);
      item.append(title);

      const path = document.createElement('p');
      path.className = 'search-result-path';
      path.textContent = `/${documentRecord.path.replace(/^\/+/, '')}`;
      item.append(path);

      const snippet = makeSnippet(documentRecord, terms);
      if (snippet) {
        const excerpt = document.createElement('p');
        excerpt.className = 'search-result-snippet';
        excerpt.textContent = snippet;
        item.append(excerpt);
      }

      resultsList.append(item);
    });
  };

  const query = new URLSearchParams(window.location.search).get('q') || '';
  input.value = query;
  let documents = [];
  let indexReady = false;

  const update = () => {
    if (!indexReady) {
      if (status) status.textContent = 'Loading the archive…';
      return;
    }
    renderResults(documents, input.value);
  };

  input.addEventListener('input', update);

  fetch(new URL('_boris/search/search-index.json', document.baseURI), {
    credentials: 'same-origin',
  })
    .then((response) => {
      if (!response.ok) throw new Error(`Search index returned ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      if (!payload || !Array.isArray(payload.documents)) {
        throw new Error('Search index has no documents');
      }
      documents = payload.documents.map(prepareDocument);
      indexReady = true;
      update();
    })
    .catch(() => {
      if (status) status.textContent = 'Search is temporarily unavailable. Please try again later.';
    });
})();
