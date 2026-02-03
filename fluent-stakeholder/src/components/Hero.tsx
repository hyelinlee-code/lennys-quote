import React from 'react';

interface HeroProps {
  totalQuotes: number;
  totalSpeakers: number;
}

const Hero: React.FC<HeroProps> = ({ totalQuotes, totalSpeakers }) => {
  return (
    <section className="w-full max-w-4xl mx-auto pt-12 pb-16 px-4 text-center">
      <h1 className="font-serif text-5xl md:text-7xl leading-[1.1] text-ink mb-6">
        Speak the language <br />
        <span className="italic text-stone-500">of silicon valley.</span>
      </h1>
      <p className="font-sans text-lg md:text-xl text-stone-600 max-w-2xl mx-auto leading-relaxed">
        Don't just learn English. Learn how to align stakeholders, drive
        velocity, and close the loop. {totalQuotes.toLocaleString()} curated
        quotes from {totalSpeakers}+ leaders on{' '}
        <span className="font-semibold text-ink">Lenny's Podcast</span>.
      </p>
    </section>
  );
};

export default Hero;
