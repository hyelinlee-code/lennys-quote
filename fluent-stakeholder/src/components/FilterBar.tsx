import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X, ArrowUpDown } from 'lucide-react';
import { Filters, SortBy } from '../types';

interface FilterBarProps {
  filters: Filters;
  onUpdateFilter: (key: keyof Filters, value: Filters[keyof Filters]) => void;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
  filterOptions: {
    functions: string[];
    topics: string[];
    difficulties: string[];
  };
  resultCount: number;
  sortBy: SortBy;
  onSortChange: (sort: SortBy) => void;
}

interface DropdownProps {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}

const SORT_OPTIONS: { value: SortBy; label: string }[] = [
  { value: 'recent', label: 'Episode Recency' },
  { value: 'popular', label: 'My Favorites' },
  { value: 'speaker', label: 'Guest Name' },
];

const Dropdown: React.FC<DropdownProps> = ({ label, options, selected, onToggle }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors ${
          selected.length > 0
            ? 'border-ink bg-ink text-white'
            : 'border-stone-200 text-stone-600 hover:border-stone-400 bg-white'
        }`}
      >
        <span>{label}</span>
        {selected.length > 0 && (
          <span className="bg-white text-ink text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
            {selected.length}
          </span>
        )}
        <ChevronDown size={14} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-56 max-h-64 overflow-y-auto bg-white border border-stone-200 rounded-lg shadow-lg z-30 animate-fade-in">
          {options.map((option) => (
            <label
              key={option}
              className="flex items-center gap-2 px-3 py-2 hover:bg-stone-50 cursor-pointer text-sm"
            >
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={() => onToggle(option)}
                className="rounded border-stone-300 text-ink focus:ring-ink"
              />
              <span className="text-stone-700">{option}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
};

const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onUpdateFilter,
  onClearFilters,
  hasActiveFilters,
  filterOptions,
  resultCount,
  sortBy,
  onSortChange,
}) => {
  const [sortOpen, setSortOpen] = useState(false);
  const sortRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (sortRef.current && !sortRef.current.contains(e.target as Node)) {
        setSortOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleArrayFilter = (key: 'functions' | 'topics' | 'difficulties', value: string) => {
    const current = filters[key];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    onUpdateFilter(key, next);
  };

  // Collect all active filter chips
  const activeChips: { label: string; onRemove: () => void }[] = [];
  for (const fn of filters.functions) {
    activeChips.push({
      label: fn,
      onRemove: () => toggleArrayFilter('functions', fn),
    });
  }
  for (const t of filters.topics) {
    activeChips.push({
      label: t,
      onRemove: () => toggleArrayFilter('topics', t),
    });
  }
  for (const d of filters.difficulties) {
    activeChips.push({
      label: d,
      onRemove: () => toggleArrayFilter('difficulties', d),
    });
  }

  const currentSortLabel = SORT_OPTIONS.find((o) => o.value === sortBy)?.label ?? 'Sort';

  return (
    <div className="max-w-5xl mx-auto mb-8 px-4">
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        {/* Sort By */}
        <div className="relative" ref={sortRef}>
          <button
            onClick={() => setSortOpen(!sortOpen)}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-stone-200 text-stone-600 hover:border-stone-400 bg-white transition-colors"
          >
            <ArrowUpDown size={14} />
            <span>Sort: {currentSortLabel}</span>
            <ChevronDown size={14} className={`transition-transform ${sortOpen ? 'rotate-180' : ''}`} />
          </button>

          {sortOpen && (
            <div className="absolute top-full left-0 mt-1 w-48 bg-white border border-stone-200 rounded-lg shadow-lg z-30 animate-fade-in">
              {SORT_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    onSortChange(option.value);
                    setSortOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-stone-50 transition-colors ${
                    sortBy === option.value
                      ? 'text-ink font-medium bg-stone-50'
                      : 'text-stone-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap gap-2">
          <Dropdown
            label="Role"
            options={filterOptions.functions}
            selected={filters.functions}
            onToggle={(v) => toggleArrayFilter('functions', v)}
          />
          <Dropdown
            label="Topic"
            options={filterOptions.topics}
            selected={filters.topics}
            onToggle={(v) => toggleArrayFilter('topics', v)}
          />
          <Dropdown
            label="Difficulty"
            options={filterOptions.difficulties}
            selected={filters.difficulties}
            onToggle={(v) => toggleArrayFilter('difficulties', v)}
          />
        </div>
      </div>

      {/* Active filters + result count */}
      {(hasActiveFilters || activeChips.length > 0) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-stone-500">
            {resultCount.toLocaleString()} result{resultCount !== 1 ? 's' : ''}
          </span>
          {activeChips.map((chip) => (
            <span
              key={chip.label}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-stone-100 text-stone-700 text-xs rounded-full"
            >
              {chip.label}
              <button onClick={chip.onRemove} className="hover:text-ink">
                <X size={12} />
              </button>
            </span>
          ))}
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="text-xs text-accent hover:text-accent/80 font-medium"
            >
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default FilterBar;
