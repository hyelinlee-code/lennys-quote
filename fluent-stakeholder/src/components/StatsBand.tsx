import React from 'react';

const stats = [
  { value: '1,987+', label: 'curated quotes' },
  { value: '200+', label: 'tech leaders' },
  { value: '3,000+', label: 'vocabs' },
];

const StatsBand: React.FC = () => {
  return (
    <div className="w-full bg-ink py-8">
      <div className="max-w-3xl mx-auto flex items-center justify-center gap-8 md:gap-12">
        {stats.map((stat, i) => (
          <React.Fragment key={stat.label}>
            {i > 0 && <div className="h-8 w-px bg-stone-600" />}
            <div className="text-center">
              <p className="font-serif text-2xl md:text-3xl text-paper">{stat.value}</p>
              <p className="text-sm text-stone-400">{stat.label}</p>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default StatsBand;
