import React from 'react';
import { Quote } from '../types';
import { ArrowRight, PlayCircle, Heart } from 'lucide-react';

interface QuoteCardProps {
  quote: Quote;
  onClick: (quote: Quote) => void;
  isLiked: boolean;
  onToggleLike: (quoteId: string) => void;
}

const QuoteCard: React.FC<QuoteCardProps> = ({ quote, onClick, isLiked, onToggleLike }) => {
  // Always show keySentence in English on card (translation is in the detail view)
  const displayText = quote.keySentence || quote.text.split(/[.!?]\s/)[0] + '.';

  return (
    <div
      onClick={() => onClick(quote)}
      className="group relative bg-white border border-stone-200 p-6 md:p-8 hover:border-ink transition-all duration-300 cursor-pointer flex flex-col justify-between h-full shadow-sm hover:shadow-md"
    >
      <div>
        <div className="flex justify-between items-start mb-4">
          <span className="text-xs font-bold tracking-widest uppercase text-stone-400">
            {quote.topic}
          </span>
          <PlayCircle
            size={18}
            className="text-stone-300 group-hover:text-accent transition-colors"
          />
        </div>

        <blockquote className="font-serif text-xl md:text-2xl leading-snug text-ink mb-6">
          &ldquo;{displayText}&rdquo;
        </blockquote>
      </div>

      <div className="mt-auto pt-6 border-t border-stone-100 flex justify-between items-end">
        <div>
          <p className="text-sm font-bold text-ink">{quote.speaker}</p>
          <p className="text-xs text-stone-500">
            {quote.role}
            {quote.company && <>, {quote.company}</>}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleLike(quote.id);
            }}
            className={`p-1.5 rounded-full transition-all duration-200 ${
              isLiked
                ? 'text-red-500 hover:text-red-600'
                : 'text-stone-300 hover:text-stone-500'
            }`}
            aria-label={isLiked ? 'Unlike' : 'Like'}
          >
            <Heart
              size={18}
              fill={isLiked ? 'currentColor' : 'none'}
              strokeWidth={isLiked ? 0 : 1.5}
            />
          </button>
          <div className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <ArrowRight size={16} className="text-ink" />
          </div>
        </div>
      </div>

      {/* Difficulty badge */}
      <div className="absolute top-6 right-14 md:right-16">
        <span
          className={`text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded ${
            quote.difficulty_level === 'Advanced'
              ? 'bg-red-50 text-red-600'
              : quote.difficulty_level === 'Beginner'
                ? 'bg-green-50 text-green-600'
                : 'bg-amber-50 text-amber-600'
          }`}
        >
          {quote.difficulty_level}
        </span>
      </div>
    </div>
  );
};

export default QuoteCard;
