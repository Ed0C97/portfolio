// Portfolio excerpt, adapted.
// Fuzzy-search hook over static pages plus fetched articles, indexed by Fuse.js.

import { useState, useEffect, useMemo } from 'react';

import Fuse from 'fuse.js';
import { apiFetch } from '../config/api';
// directLinks: { keyword: routePath }, multiple aliases per page
import directLinks from '../data/directLinks.json';

const pageDisplayTitles = {
  '/': 'Home',
  '/archive': 'Archive',
  '/about': 'About',
  '/contact': 'Contact',
};

// titles/keywords outweigh body so a title hit beats a passing mention in content
const fuseOptions = {
  includeScore: true,
  includeMatches: true,
  minMatchCharLength: 2,
  threshold: 0.4,
  ignoreLocation: true,
  keys: [
    { name: 'title', weight: 0.7 },
    { name: 'searchKeywords', weight: 0.7 },
    { name: 'category', weight: 0.5 },
    { name: 'content_snippet', weight: 0.2 },
  ],
};

export const useSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searchIndex, setSearchIndex] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSearchData = async () => {
      try {
        // invert directLinks to one entry per page, folding every alias into
        // one keyword string Fuse can match against
        const pagesBySlug = {};
        for (const [keyword, slug] of Object.entries(directLinks)) {
          if (!pagesBySlug[slug]) {
            pagesBySlug[slug] = {
              type: 'page',
              title: pageDisplayTitles[slug] || slug,
              slug,
              searchKeywords: [],
            };
          }
          pagesBySlug[slug].searchKeywords.push(keyword);
        }

        const staticPages = Object.values(pagesBySlug).map((page) => ({
          ...page,
          searchKeywords: page.searchKeywords.join(' '),
        }));

        const response = await apiFetch('/api/search-data');
        if (!response.ok) throw new Error('Failed to fetch articles');
        const articles = await response.json();

        setSearchIndex([...staticPages, ...articles]);
      } catch (error) {
        console.error('Failed to fetch search data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSearchData();
  }, []);

  // rebuilding the index is O(n); only do it when the data actually changes
  const fuse = useMemo(() => new Fuse(searchIndex, fuseOptions), [searchIndex]);

  // skip single-char queries (too noisy) and queries before the index loads
  useEffect(() => {
    if (searchQuery.length > 1 && !isLoading) {
      setResults(fuse.search(searchQuery).slice(0, 5));
    } else {
      setResults([]);
    }
  }, [searchQuery, fuse, isLoading]);

  return { searchQuery, setSearchQuery, results, isLoading };
};
