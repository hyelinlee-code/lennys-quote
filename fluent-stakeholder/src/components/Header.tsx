import React from 'react';
import { Mic, Menu, X } from 'lucide-react';
import { Language } from '../types';

interface HeaderProps {
  onHome: () => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
}

const LANGUAGES: { code: Language; label: string }[] = [
  { code: 'en', label: 'EN' },
  { code: 'ko', label: 'KO' },
  { code: 'zh', label: 'ZH' },
  { code: 'es', label: 'ES' },
];

const Header: React.FC<HeaderProps> = ({ onHome, language, onLanguageChange }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <nav className="w-full py-4 px-4 md:px-8 bg-transparent relative z-20">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Logo */}
        <div
          onClick={onHome}
          className="flex items-center cursor-pointer group"
        >
          <img
            src="/lennylingo.png"
            alt="LennyLingo"
            className="h-10 group-hover:scale-105 transition-transform duration-300"
          />
        </div>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center space-x-6">
          {/* Language pills */}
          <div className="flex items-center bg-stone-100 rounded-full p-0.5">
            {LANGUAGES.map(({ code, label }) => (
              <button
                key={code}
                onClick={() => onLanguageChange(code)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                  language === code
                    ? 'bg-ink text-white'
                    : 'text-stone-500 hover:text-ink'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <a href="#" className="text-sm font-medium text-stone-600 hover:text-ink transition-colors">
            Methodology
          </a>
          <a href="#" className="text-sm font-medium text-stone-600 hover:text-ink transition-colors">
            The Podcast
          </a>
          <a href="#" className="text-sm font-medium text-stone-600 hover:text-ink transition-colors">
            Sign In
          </a>
          <button className="bg-ink text-white px-4 py-2 rounded-full hover:bg-stone-800 transition-colors flex items-center space-x-2 text-sm font-medium">
            <Mic size={14} />
            <span>Subscribe</span>
          </button>
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 text-stone-600"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-4 pb-4 border-t border-stone-200 pt-4 animate-fade-in">
          <div className="flex items-center justify-center mb-4 bg-stone-100 rounded-full p-0.5 mx-auto w-fit">
            {LANGUAGES.map(({ code, label }) => (
              <button
                key={code}
                onClick={() => {
                  onLanguageChange(code);
                  setMobileMenuOpen(false);
                }}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                  language === code
                    ? 'bg-ink text-white'
                    : 'text-stone-500 hover:text-ink'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex flex-col items-center space-y-3">
            <a href="#" className="text-sm font-medium text-stone-600">Methodology</a>
            <a href="#" className="text-sm font-medium text-stone-600">The Podcast</a>
            <a href="#" className="text-sm font-medium text-stone-600">Sign In</a>
            <button className="bg-ink text-white px-6 py-2 rounded-full text-sm font-medium flex items-center space-x-2">
              <Mic size={14} />
              <span>Subscribe</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Header;
