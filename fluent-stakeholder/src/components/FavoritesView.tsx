import React, { useMemo } from 'react';
import { Quote } from '../types';
import QuoteCard from './QuoteCard';
import { Heart } from 'lucide-react';

interface FavoritesViewProps {
  allQuotes: Quote[];
  likes: Set<string>;
  onQuoteClick: (quote: Quote) => void;
  isLiked: (id: string) => boolean;
  onToggleLike: (id: string) => void;
}

const FavoritesView: React.FC<FavoritesViewProps> = ({
  allQuotes,
  likes,
  onQuoteClick,
  isLiked,
  onToggleLike,
}) => {
  const favoriteQuotes = useMemo(
    () => allQuotes.filter((q) => likes.has(q.id)),
    [allQuotes, likes]
  );

  return (
    <main className="container mx-auto px-4 pb-20">
      <div className="max-w-5xl mx-auto pt-8 pb-4">
        <h1 className="font-serif text-3xl md:text-4xl text-ink mb-2">
          Your Favorites
        </h1>
        <p className="text-stone-500">
          {favoriteQuotes.length === 0
            ? 'Save expressions you want to revisit.'
            : `${favoriteQuotes.length} saved expression${favoriteQuotes.length === 1 ? '' : 's'}.`}
        </p>
      </div>

      {favoriteQuotes.length === 0 ? (
        <div className="max-w-5xl mx-auto text-center py-20">
          <Heart size={48} className="mx-auto text-stone-300 mb-4" />
          <p className="text-stone-500 text-lg mb-2">No favorites yet</p>
          <p className="text-stone-400 text-sm">
            Tap the heart icon on any expression to save it here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {favoriteQuotes.map((quote) => (
            <QuoteCard
              key={quote.id}
              quote={quote}
              onClick={onQuoteClick}
              isLiked={isLiked(quote.id)}
              onToggleLike={onToggleLike}
            />
          ))}
        </div>
      )}
    </main>
  );
};

export default FavoritesView;
