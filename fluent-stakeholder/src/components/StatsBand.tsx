import React from 'react';

const stats = [
  { value: '1,987+', label: 'curated quotes' },
  { value: '200+', label: 'tech leaders' },
  { value: '3,000+', label: 'vocabs' },
];

const StatsBand: React.FC = () => {
  return (
    <div className="w-full max-w-3xl mx-auto flex items-center justify-center gap-8 md:gap-12 py-6">
      {stats.map((stat, i) => (
        <React.Fragment key={stat.label}>
          {i > 0 && <div className="h-8 w-px bg-stone-200" />}
          <div className="text-center">
            <p className="font-serif text-2xl md:text-3xl text-ink">{stat.value}</p>
            <p className="text-sm text-stone-500">{stat.label}</p>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};

export default StatsBand;
