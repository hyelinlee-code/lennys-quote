import React, { useState, useMemo } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import FilterBar from './components/FilterBar';
import QuoteCard from './components/QuoteCard';
import DetailView from './components/DetailView';
import { useQuotes } from './hooks/useQuotes';
import { Quote } from './types';
import { Mail, Loader2 } from 'lucide-react';

const QUOTES_PER_PAGE = 20;

const App: React.FC = () => {
  const {
    quotes,
    loading,
    error,
    language,
    setLanguage,
    filters,
    updateFilter,
    clearFilters,
    hasActiveFilters,
    filterOptions,
    totalCount,
    totalSpeakers,
  } = useQuotes();

  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [visibleCount, setVisibleCount] = useState(QUOTES_PER_PAGE);

  const handleCardClick = (quote: Quote) => {
    setSelectedQuote(quote);
    document.body.style.overflow = 'hidden';
  };

  const handleCloseDetail = () => {
    setSelectedQuote(null);
    document.body.style.overflow = 'auto';
  };

  const handleHome = () => {
    setSelectedQuote(null);
    clearFilters();
    setVisibleCount(QUOTES_PER_PAGE);
    document.body.style.overflow = 'auto';
  };

  // Paginated quotes
  const visibleQuotes = useMemo(
    () => quotes.slice(0, visibleCount),
    [quotes, visibleCount]
  );

  const hasMore = visibleCount < quotes.length;

  // Reset visible count when filters change
  React.useEffect(() => {
    setVisibleCount(QUOTES_PER_PAGE);
  }, [filters]);

  if (error) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <div className="text-center">
          <p className="text-stone-500 mb-2">Failed to load quotes</p>
          <p className="text-sm text-stone-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper text-ink selection:bg-yellow-200 selection:text-black">
      <Header
        onHome={handleHome}
        language={language}
        onLanguageChange={setLanguage}
      />

      <main className="container mx-auto px-4 pb-20">
        <Hero totalQuotes={totalCount} totalSpeakers={totalSpeakers} />

        <FilterBar
          filters={filters}
          onUpdateFilter={updateFilter}
          onClearFilters={clearFilters}
          hasActiveFilters={hasActiveFilters}
          filterOptions={filterOptions}
          resultCount={quotes.length}
        />

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={32} className="animate-spin text-stone-400" />
          </div>
        ) : quotes.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-stone-500 text-lg mb-2">No quotes match your filters</p>
            <button
              onClick={clearFilters}
              className="text-accent hover:text-accent/80 text-sm font-medium"
            >
              Clear all filters
            </button>
          </div>
        ) : (
          <>
            {/* Quote Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
              {visibleQuotes.map((quote) => (
                <QuoteCard
                  key={quote.id}
                  quote={quote}
                  language={language}
                  onClick={handleCardClick}
                />
              ))}
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="text-center mt-10">
                <button
                  onClick={() => setVisibleCount((c) => c + QUOTES_PER_PAGE)}
                  className="px-6 py-3 border border-stone-300 rounded-lg text-sm font-medium text-stone-600 hover:border-ink hover:text-ink transition-colors"
                >
                  Load more ({quotes.length - visibleCount} remaining)
                </button>
              </div>
            )}
          </>
        )}

        {/* Newsletter Section */}
        <div className="mt-24 max-w-2xl mx-auto text-center border-t border-stone-200 pt-16">
          <h3 className="font-serif text-3xl mb-4">Get the weekly digest</h3>
          <p className="text-stone-500 mb-8">
            One powerful business idiom, explained deeply, delivered to your
            inbox every Monday.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              placeholder="product.manager@acme.co"
              className="flex-1 bg-white border border-stone-200 px-4 py-3 rounded-lg focus:outline-none focus:border-ink focus:ring-1 focus:ring-ink transition-all"
            />
            <button className="bg-ink text-white px-6 py-3 rounded-lg font-medium hover:bg-stone-800 transition-colors flex items-center justify-center gap-2">
              <Mail size={16} />
              <span>Subscribe</span>
            </button>
          </div>
        </div>
      </main>

      <footer className="w-full py-8 text-center text-stone-400 text-sm border-t border-stone-200 mt-12 bg-white">
        <p>
          &copy; {new Date().getFullYear()} Fluent Stakeholder. Inspired by
          Lenny&apos;s Podcast.
        </p>
      </footer>

      {/* Detail View Overlay */}
      {selectedQuote && (
        <DetailView
          quote={selectedQuote}
          language={language}
          onClose={handleCloseDetail}
        />
      )}
    </div>
  );
};

export default App;
