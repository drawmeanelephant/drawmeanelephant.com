(() => {
  const form = document.querySelector('[data-instagram-search]');
  if (!form) return;

  const input = form.querySelector('input');
  const status = form.querySelector('[data-instagram-status]');
  const empty = document.querySelector('[data-instagram-empty]');
  const cards = Array.from(document.querySelectorAll('.instagram-feed__item'));

  const updateResults = () => {
    const query = input.value.trim().toLocaleLowerCase();
    let visible = 0;

    cards.forEach((card) => {
      const matches = query === '' || card.textContent.toLocaleLowerCase().includes(query);
      card.hidden = !matches;
      if (matches) visible += 1;
    });

    if (status) {
      status.textContent = query === ''
        ? `${cards.length} records, newest first`
        : `${visible} ${visible === 1 ? 'record' : 'records'} found`;
    }
    if (empty) empty.hidden = visible !== 0;
  };

  form.addEventListener('submit', (event) => event.preventDefault());
  input.addEventListener('input', updateResults);
  updateResults();
})();
