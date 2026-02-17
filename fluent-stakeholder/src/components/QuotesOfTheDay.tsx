import React, { useMemo } from 'react';
import { Quote } from '../types';
import { ArrowRight, PlayCircle } from 'lucide-react';

interface QuotesOfTheDayProps {
  quotes: Quote[];
  onQuoteClick: (quote: Quote) => void;
  onBrowseAll: () => void;
}

function getDailyQuotes(quotes: Quote[], count: number): Quote[] {
  if (quotes.length === 0) return [];

  const today = new Date();
  const seed = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate();

  // Seeded random for deterministic daily selection
  const seededRandom = (s: number): number => {
    const x = Math.sin(s) * 10000;
    return x - Math.floor(x);
  };

  const hashString = (str: string, s: number): number => {
    let hash = s;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
    }
    return seededRandom(hash);
  };

  // Shuffle deterministically
  const shuffled = [...quotes].sort((a, b) =>
    hashString(a.id, seed) - hashString(b.id, seed)
  );

  // Select with diversity: different speakers, different first letters
  const selected: Quote[] = [];
  const usedFirstLetters = new Set<string>();
  const usedSpeakers = new Set<string>();

  // First pass: prioritize diverse first letters
  for (const quote of shuffled) {
    if (selected.length >= count) break;
    const firstLetter = quote.speaker.charAt(0).toUpperCase();
    if (usedFirstLetters.has(firstLetter) || usedSpeakers.has(quote.speaker)) continue;

    selected.push(quote);
    usedFirstLetters.add(firstLetter);
    usedSpeakers.add(quote.speaker);
  }

  // Second pass: fill remaining with different speakers (allow same first letter)
  if (selected.length < count) {
    for (const quote of shuffled) {
      if (selected.length >= count) break;
      if (usedSpeakers.has(quote.speaker)) continue;
      selected.push(quote);
      usedSpeakers.add(quote.speaker);
    }
  }

  return selected;
}

const QuotesOfTheDay: React.FC<QuotesOfTheDayProps> = ({ quotes, onQuoteClick, onBrowseAll }) => {
  const dailyQuotes = useMemo(() => getDailyQuotes(quotes, 4), [quotes]);

  if (dailyQuotes.length === 0) return null;

  return (
    <section className="w-full max-w-5xl mx-auto py-16 px-4">
      <div className="text-center mb-12">
        <h2 className="font-serif text-3xl md:text-4xl text-ink mb-3">
          Featured Expressions
        </h2>
        <p className="text-stone-500 max-w-lg mx-auto">
          See how real tech leaders communicate.
          Tap a card to reveal definitions, business context, and translations.
          Learn not just what the phrase means, but why it works in high-stakes conversations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {dailyQuotes.map((quote) => (
          <div
            key={quote.id}
            onClick={() => onQuoteClick(quote)}
            className="group relative bg-white border border-stone-200 p-6 md:p-8 hover:border-ink transition-all duration-300 cursor-pointer flex flex-col justify-between shadow-sm hover:shadow-md"
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
                &ldquo;{quote.keySentence || quote.text.split(/[.!?]\s/)[0] + '.'}&rdquo;
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
        ))}
      </div>

      <div className="text-center mt-10">
        <button
          onClick={onBrowseAll}
          className="inline-flex items-center gap-2 px-6 py-3 border border-stone-300 rounded-lg text-sm font-semibold text-stone-600 hover:border-ink hover:text-ink transition-colors"
        >
          Browse All Expressions
          <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
};

export default QuotesOfTheDay;
