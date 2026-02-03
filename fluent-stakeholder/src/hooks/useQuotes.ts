import { useState, useEffect, useMemo } from 'react';
import { Quote, Filters, SortBy } from '../types';

const DATA_URL = '/data/quotes.json';

export function useQuotes(likes: Set<string>) {
  const [allQuotes, setAllQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortBy>('recent');
  const [filters, setFilters] = useState<Filters>({
    search: '',
    functions: [],
    topics: [],
    difficulties: [],
  });

  // Load data
  useEffect(() => {
    fetch(DATA_URL)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load quotes');
        return res.json();
      })
      .then((data: Quote[]) => {
        setAllQuotes(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Extract unique filter options from data
  const filterOptions = useMemo(() => {
    const functions = new Set<string>();
    const topics = new Set<string>();
    const difficulties = new Set<string>();

    for (const q of allQuotes) {
      if (q.speaker_function) functions.add(q.speaker_function);
      for (const t of q.topics) topics.add(t);
      if (q.difficulty_level) difficulties.add(q.difficulty_level);
    }

    return {
      functions: Array.from(functions).filter(Boolean).sort(),
      topics: Array.from(topics).sort(),
      difficulties: ['Beginner', 'Intermediate', 'Advanced'].filter((d) =>
        difficulties.has(d)
      ),
    };
  }, [allQuotes]);

  // Filter quotes
  const filteredQuotes = useMemo(() => {
    return allQuotes.filter((q) => {
      // Search filter (kept for programmatic use, just not in UI)
      if (filters.search) {
        const term = filters.search.toLowerCase();
        const matchText =
          q.text.toLowerCase().includes(term) ||
          q.speaker.toLowerCase().includes(term) ||
          q.topic.toLowerCase().includes(term) ||
          q.role.toLowerCase().includes(term) ||
          q.company.toLowerCase().includes(term);
        if (!matchText) return false;
      }

      // Function filter
      if (
        filters.functions.length > 0 &&
        !filters.functions.includes(q.speaker_function)
      ) {
        return false;
      }

      // Topic filter
      if (
        filters.topics.length > 0 &&
        !q.topics.some((t) => filters.topics.includes(t))
      ) {
        return false;
      }

      // Difficulty filter
      if (
        filters.difficulties.length > 0 &&
        !filters.difficulties.includes(q.difficulty_level)
      ) {
        return false;
      }

      return true;
    });
  }, [allQuotes, filters]);

  // Sort quotes
  const sortedQuotes = useMemo(() => {
    const sorted = [...filteredQuotes];

    switch (sortBy) {
      case 'recent':
        // Sort by episodeOrder descending (newest first)
        // Quotes without episodeOrder go to the end
        sorted.sort((a, b) => {
          const aOrder = a.episodeOrder ?? 0;
          const bOrder = b.episodeOrder ?? 0;
          return bOrder - aOrder;
        });
        break;

      case 'popular':
        // Liked quotes first, then rest in default order
        sorted.sort((a, b) => {
          const aLiked = likes.has(a.id) ? 1 : 0;
          const bLiked = likes.has(b.id) ? 1 : 0;
          if (bLiked !== aLiked) return bLiked - aLiked;
          return 0; // preserve relative order among equally liked/unliked
        });
        break;

      case 'speaker':
        sorted.sort((a, b) => a.speaker.localeCompare(b.speaker));
        break;
    }

    return sorted;
  }, [filteredQuotes, sortBy, likes]);

  const updateFilter = (key: keyof Filters, value: Filters[keyof Filters]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({ search: '', functions: [], topics: [], difficulties: [] });
  };

  const hasActiveFilters =
    filters.search !== '' ||
    filters.functions.length > 0 ||
    filters.topics.length > 0 ||
    filters.difficulties.length > 0;

  const totalSpeakers = useMemo(() => {
    return new Set(allQuotes.map((q) => q.speaker)).size;
  }, [allQuotes]);

  return {
    quotes: sortedQuotes,
    allQuotes,
    loading,
    error,
    sortBy,
    setSortBy,
    filters,
    updateFilter,
    clearFilters,
    hasActiveFilters,
    filterOptions,
    totalCount: allQuotes.length,
    totalSpeakers,
  };
}
