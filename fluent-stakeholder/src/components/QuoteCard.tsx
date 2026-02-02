import React from 'react';
import { Quote, Language } from '../types';
import { ArrowRight, PlayCircle } from 'lucide-react';

interface QuoteCardProps {
  quote: Quote;
  language: Language;
  onClick: (quote: Quote) => void;
}

const QuoteCard: React.FC<QuoteCardProps> = ({ quote, language, onClick }) => {
  const displayText = () => {
    if (language === 'en') return quote.text;
    const translationKey = `text_${language}` as keyof Quote;
    const translation = quote[translationKey] as string;
    return translation || quote.text;
  };

  // Truncate long quotes for card display
  const text = displayText();
  const truncated = text.length > 200 ? text.slice(0, 200) + '...' : text;

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
          &ldquo;{truncated}&rdquo;
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

        <div className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <ArrowRight size={16} className="text-ink" />
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
