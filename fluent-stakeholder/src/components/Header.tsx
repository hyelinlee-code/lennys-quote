import React from 'react';
import { Search, Heart, Menu, X } from 'lucide-react';

interface HeaderProps {
  onHome: () => void;
  onBrowse: () => void;
  onAbout: () => void;
  onFavorites: () => void;
  searchOpen: boolean;
  onSearchToggle: () => void;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  likeCount: number;
}

const Header: React.FC<HeaderProps> = ({
  onHome,
  onBrowse,
  onAbout,
  onFavorites,
  searchOpen,
  onSearchToggle,
  searchTerm,
  onSearchChange,
  likeCount,
}) => {
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
          <button
            onClick={onAbout}
            className="text-sm font-semibold text-stone-600 hover:text-ink transition-colors"
          >
            About
          </button>
          <button
            onClick={onBrowse}
            className="text-sm font-semibold text-stone-600 hover:text-ink transition-colors"
          >
            Browse
          </button>
          <button
            onClick={onSearchToggle}
            className="p-2 text-stone-500 hover:text-ink transition-colors"
            aria-label="Toggle search"
          >
            <Search size={18} />
          </button>
          <button
            onClick={onFavorites}
            className="relative p-2 text-stone-500 hover:text-ink transition-colors"
            aria-label="Favorites"
          >
            <Heart size={18} />
            {likeCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                {likeCount}
              </span>
            )}
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

      {/* Search bar */}
      {searchOpen && (
        <div className="max-w-7xl mx-auto mt-3 animate-fade-in">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search quotes, speakers, topics..."
              className="w-full pl-10 pr-10 py-2.5 bg-white border border-stone-200 rounded-lg text-sm focus:outline-none focus:border-ink focus:ring-1 focus:ring-ink transition-all"
              autoFocus
            />
            {searchTerm && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-ink"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-4 pb-4 border-t border-stone-200 pt-4 animate-fade-in">
          <div className="flex flex-col items-center space-y-3">
            <button
              onClick={() => {
                onAbout();
                setMobileMenuOpen(false);
              }}
              className="text-sm font-semibold text-stone-600"
            >
              About
            </button>
            <button
              onClick={() => {
                onBrowse();
                setMobileMenuOpen(false);
              }}
              className="text-sm font-semibold text-stone-600"
            >
              Browse
            </button>
            <button
              onClick={() => {
                onSearchToggle();
                setMobileMenuOpen(false);
              }}
              className="flex items-center gap-2 text-sm font-semibold text-stone-600"
            >
              <Search size={16} />
              Search
            </button>
            <button
              onClick={() => {
                onFavorites();
                setMobileMenuOpen(false);
              }}
              className="flex items-center gap-2 text-sm font-semibold text-stone-600"
            >
              <Heart size={16} />
              Favorites
              {likeCount > 0 && (
                <span className="bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                  {likeCount}
                </span>
              )}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Header;
