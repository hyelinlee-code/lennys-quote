import React, { useState, useEffect, useRef } from 'react';
import { Quote, Vocabulary, TranslationLanguage } from '../types';
import { X, ArrowLeft, Sparkles, RotateCcw } from 'lucide-react';

interface DetailViewProps {
  quote: Quote;
  translationLang: TranslationLanguage;
  onTranslationLangChange: (lang: TranslationLanguage) => void;
  onClose: () => void;
}

const TRANSLATION_LANGUAGES: { code: TranslationLanguage; label: string }[] = [
  { code: 'ko', label: '한국어' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
];

const DetailView: React.FC<DetailViewProps> = ({ quote, translationLang, onTranslationLangChange, onClose }) => {
  const [selectedWord, setSelectedWord] = useState<Vocabulary | null>(null);
  const [isFlipped, setIsFlipped] = useState(false);
  const frontRef = useRef<HTMLDivElement>(null);
  const backRef = useRef<HTMLDivElement>(null);
  const [cardHeight, setCardHeight] = useState<number | undefined>(undefined);

  // Auto-select the first vocab word on load
  useEffect(() => {
    if (quote.vocabulary.length > 0) {
      setSelectedWord(quote.vocabulary[0]);
    } else {
      setSelectedWord(null);
    }
    setIsFlipped(false);
  }, [quote]);

  // Measure both faces so the container keeps a stable height during flip
  useEffect(() => {
    const frontH = frontRef.current?.offsetHeight ?? 0;
    const backH = backRef.current?.offsetHeight ?? 0;
    setCardHeight(Math.max(frontH, backH));
  }, [quote, translationLang]);

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // Get translation text
  const getTranslation = (): string | null => {
    const key = `text_${translationLang}` as keyof Quote;
    const translation = quote[key] as string;
    return translation || null;
  };

  const translation = getTranslation();
  const canFlip = translation !== null;

  // Highlight vocabulary words in the QUOTE text (not the context)
  const renderHighlightedQuote = () => {
    const quoteText = quote.text;
    if (!quote.vocabulary.length) {
      return <span>{quoteText}</span>;
    }

    const vocabWords = quote.vocabulary.map((v) => v.word);
    vocabWords.sort((a, b) => b.length - a.length);

    const escaped = vocabWords.map((w) =>
      w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    );
    const pattern = new RegExp(`(${escaped.join('|')})`, 'gi');
    const parts = quoteText.split(pattern);

    return parts.map((part, i) => {
      const matchingVocab = quote.vocabulary.find(
        (v) => v.word.toLowerCase() === part.toLowerCase()
      );

      if (matchingVocab) {
        const isSelected = selectedWord?.word === matchingVocab.word;
        return (
          <span
            key={i}
            onClick={() => setSelectedWord(matchingVocab)}
            className={`cursor-pointer px-0.5 rounded transition-colors duration-200 ${
              isSelected
                ? 'bg-highlight text-black underline decoration-2 decoration-black/20'
                : 'bg-highlight/30 hover:bg-highlight/60'
            }`}
          >
            {part}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-paper overflow-y-auto animate-fade-in">
      {/* Sticky Header */}
      <div className="sticky top-0 bg-paper/90 backdrop-blur-md border-b border-stone-200 px-4 md:px-6 py-3 flex justify-between items-center z-10">
        <button
          onClick={onClose}
          className="flex items-center space-x-2 text-stone-500 hover:text-ink transition-colors"
        >
          <ArrowLeft size={20} />
          <span className="text-sm font-medium">Back to collection</span>
        </button>
        <button onClick={onClose} className="p-2 text-stone-400 hover:text-ink">
          <X size={24} />
        </button>
      </div>

      {/* Vertical layout: quote on top, learning below */}
      <div className="max-w-3xl mx-auto px-4 md:px-8 py-8 md:py-12">

        {/* ===== TOP: Quote Section ===== */}
        <section className="mb-10">
          <span className="text-accent text-sm font-bold tracking-wider uppercase mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent"></span>
            {quote.topic}
          </span>

          {/* Flip Card for quote text */}
          <div className="flip-card mb-4" style={cardHeight ? { minHeight: cardHeight } : undefined}>
            <div className={`flip-card-inner ${isFlipped ? 'flipped' : ''}`}>
              {/* Front — English quote with highlighted vocab */}
              <div ref={frontRef} className="flip-card-front">
                <blockquote className="font-serif text-2xl md:text-3xl lg:text-4xl text-ink leading-snug">
                  {renderHighlightedQuote()}
                </blockquote>
              </div>

              {/* Back — Language selector + Translation */}
              <div ref={backRef} className="flip-card-back flex flex-col items-start">
                {/* Language pills */}
                <div className="flex items-center gap-1.5 mb-4">
                  {TRANSLATION_LANGUAGES.map(({ code, label }) => (
                    <button
                      key={code}
                      onClick={(e) => {
                        e.stopPropagation();
                        onTranslationLangChange(code);
                      }}
                      className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                        translationLang === code
                          ? 'bg-ink text-white'
                          : 'bg-stone-100 text-stone-500 hover:text-ink'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <blockquote className="font-serif text-xl md:text-2xl lg:text-3xl text-ink leading-snug">
                  {translation}
                </blockquote>
              </div>
            </div>
          </div>

          {/* Flip button */}
          {canFlip && (
            <button
              onClick={() => setIsFlipped((f) => !f)}
              className="group flex items-center gap-2 px-4 py-2 rounded-full border border-stone-300 text-sm text-stone-500 hover:border-ink hover:text-ink transition-colors mb-6"
            >
              <RotateCcw
                size={14}
                className="transition-transform group-hover:-rotate-45"
              />
              {isFlipped ? 'Flip back to English' : 'Flip for translation'}
            </button>
          )}

          {/* Speaker info + meta */}
          <div className="flex items-center justify-between flex-wrap gap-4 mt-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-stone-200 flex items-center justify-center text-stone-500 font-serif font-bold text-base shrink-0">
                {quote.speaker.charAt(0)}
              </div>
              <div>
                <p className="font-bold text-ink text-sm">{quote.speaker}</p>
                <p className="text-xs text-stone-500">
                  {quote.role}
                  {quote.company && <> at {quote.company}</>}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {quote.topics.map((t) => (
                <span
                  key={t}
                  className="px-2 py-0.5 bg-stone-100 text-stone-600 text-xs rounded-full"
                >
                  {t}
                </span>
              ))}
              <span
                className={`px-2 py-0.5 text-xs rounded-full ${
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

          {/* Conversation context (the editorial summary) */}
          {quote.fullContext && (
            <div className="mt-6 p-4 bg-stone-50 rounded-lg border border-stone-200">
              <p className="text-xs font-bold text-stone-400 uppercase tracking-widest mb-2">
                Conversation Context
              </p>
              <p className="text-sm text-stone-600 leading-relaxed">
                {quote.fullContext}
              </p>
            </div>
          )}
        </section>

        <hr className="border-stone-200 mb-10" />

        {/* ===== BOTTOM: Learning Section ===== */}
        <section>
          {quote.vocabulary.length > 0 ? (
            <>
              {/* Vocabulary word pills */}
              <div className="mb-6">
                <span className="text-xs font-bold text-stone-400 uppercase tracking-widest">
                  Vocabulary ({quote.vocabulary.length})
                </span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {quote.vocabulary.map((v) => (
                    <button
                      key={v.word}
                      onClick={() => setSelectedWord(v)}
                      className={`px-3 py-1.5 text-sm rounded-full border transition-all ${
                        selectedWord?.word === v.word
                          ? 'border-ink bg-ink text-white'
                          : 'border-stone-200 text-stone-600 hover:border-stone-400'
                      }`}
                    >
                      {v.word}
                    </button>
                  ))}
                </div>
              </div>

              {/* Selected word detail */}
              {selectedWord && (
                <div className="animate-slide-in-right" key={selectedWord.word}>
                  <h3 className="text-3xl font-serif text-ink mt-2 mb-4">
                    {selectedWord.word}
                  </h3>

                  {selectedWord.definition && (
                    <p className="text-lg text-stone-700 italic border-l-4 border-accent pl-4 py-1 mb-6">
                      &ldquo;{selectedWord.definition}&rdquo;
                    </p>
                  )}

                  <div className="space-y-6">
                    {selectedWord.businessContext && (
                      <div>
                        <h4 className="font-bold text-sm text-ink mb-2">
                          Business Context
                        </h4>
                        <p className="text-stone-600 leading-relaxed">
                          {selectedWord.businessContext}
                        </p>
                      </div>
                    )}
                    {selectedWord.exampleUsage && (
                      <div>
                        <h4 className="font-bold text-sm text-ink mb-2">
                          Standard Usage
                        </h4>
                        <p className="text-stone-600 bg-stone-50 p-4 rounded-lg font-mono text-sm">
                          {selectedWord.exampleUsage}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* AI Insights Section */}
                  {selectedWord.insight && selectedWord.insight.nuance && (
                    <div className="mt-8 bg-stone-900 rounded-2xl p-6 text-stone-300 relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Sparkles size={120} />
                      </div>

                      <div className="flex items-center space-x-2 mb-4 text-purple-400">
                        <Sparkles size={16} />
                        <span className="text-xs font-bold uppercase tracking-widest">
                          AI Deep Dive
                        </span>
                      </div>

                      <div className="relative z-10 space-y-4">
                        <div>
                          <span className="text-xs font-bold text-stone-500 uppercase">
                            The Nuance
                          </span>
                          <p className="text-stone-100 text-sm leading-relaxed mt-1">
                            {selectedWord.insight.nuance}
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          {selectedWord.insight.synonyms.length > 0 && (
                            <div>
                              <span className="text-xs font-bold text-stone-500 uppercase">
                                Synonyms
                              </span>
                              <ul className="text-sm mt-1 list-disc list-inside text-stone-300">
                                {selectedWord.insight.synonyms.map((s) => (
                                  <li key={s}>{s}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {selectedWord.insight.antonyms.length > 0 && (
                            <div>
                              <span className="text-xs font-bold text-stone-500 uppercase">
                                Avoid
                              </span>
                              <ul className="text-sm mt-1 list-disc list-inside text-stone-300">
                                {selectedWord.insight.antonyms.map((a) => (
                                  <li key={a}>{a}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Placeholder if no enriched data */}
                  {!selectedWord.definition && !selectedWord.insight && (
                    <div className="mt-8 bg-stone-50 rounded-2xl p-6 text-center">
                      <Sparkles size={24} className="mx-auto text-stone-300 mb-2" />
                      <p className="text-stone-400 text-sm">
                        Vocabulary insights will appear here once the data is enriched.
                      </p>
                      <p className="text-stone-400 text-xs mt-1">
                        Run the enrichment pipeline to generate definitions and AI insights.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="py-12 text-center text-stone-400">
              <p className="text-lg">No vocabulary highlights for this quote.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default DetailView;
