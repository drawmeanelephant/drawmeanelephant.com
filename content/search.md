---
id: search
title: "Search"
status: published
---

<div class="search-page" data-search-page data-boris-search-exclude="true">
<p>Search the archive for a brewery, a place, an Instagram caption, or one of the project updates.</p>

<form class="search-page-form" action="/search.html" method="get" role="search" data-search-form novalidate>
<label class="search-label" for="search-page-input">Search the archive</label>
<div class="search-page-form-row">
<input id="search-page-input" name="q" type="search" placeholder="Try “brewery” or “pizzahut”" autocomplete="off">
<button type="submit">Search</button>
</div>
</form>

<p class="search-status" data-search-status aria-live="polite">Loading the archive…</p>
<ol class="search-results" data-search-results aria-label="Search results"></ol>
<p class="search-no-results" data-search-no-results hidden>No pages matched that search. Try a shorter phrase.</p>
<noscript><p>Search requires JavaScript to read the site index.</p></noscript>
</div>
