import React from 'react';
import { BookOpen, Briefcase, Lightbulb } from 'lucide-react';

const pillars = [
  {
    icon: BookOpen,
    title: 'High-Quality Input',
    description:
      'You can\'t output professional business English if you aren\'t consuming it. We curate transcripts from top-tier tech leaders to provide the highest quality linguistic input available.',
  },
  {
    icon: Briefcase,
    title: 'Business Ready',
    description:
      'Non-native professionals often know the grammar but miss the nuance. Learn the specific idioms, phrasal verbs, and buzzwords that drive Silicon Valley conversations today.',
  },
  {
    icon: Lightbulb,
    title: 'Leadership Mindset',
    description:
      'Language is a vehicle for thought. By learning how admirable leaders articulate strategy and culture, you internalize their mental models and elevate your own leadership presence.',
  },
];

const WhatIsLennyLingo: React.FC = () => {
  return (
    <section className="w-full max-w-5xl mx-auto py-16 px-4">
      <div className="border-t border-stone-200 pt-16">
        <div className="text-center mb-14">
          <h2 className="font-serif text-3xl md:text-4xl text-ink mb-6">
            What is LennyLingo?
          </h2>
          <p className="text-stone-500 max-w-2xl mx-auto text-lg leading-relaxed">
            LennyLingo turns real conversations from top tech leaders into practical business English. We curate high-impact expressions from{' '}
            <a href="https://www.lennysnewsletter.com/podcast" target="_blank" rel="noopener noreferrer" className="font-semibold text-stone-700 underline hover:text-accent">Lenny's Podcast</a>{' '}
            and transform them into learnable units you can confidently use at work.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pillars.map(({ icon: Icon, title, description }) => (
            <div key={title} className="text-center">
              <div className="inline-flex w-12 h-12 rounded-lg bg-stone-100 items-center justify-center mb-4">
                <Icon size={24} className="text-accent" />
              </div>
              <h3 className="font-semibold text-ink mb-2 text-lg">{title}</h3>
              <p className="text-stone-500 text-sm leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WhatIsLennyLingo;
