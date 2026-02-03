import React from 'react';
import { Search, Scan, Repeat } from 'lucide-react';

const steps = [
  {
    icon: Search,
    step: '1',
    title: 'Find Your Context',
    description:
      'Search by topic (e.g., "Strategy," "Hiring") or difficulty. Don\'t just learn random words — find the language relevant to your next big meeting or presentation.',
  },
  {
    icon: Scan,
    step: '2',
    title: 'Decode the Nuance',
    description:
      'Click highlighted keywords to see the "Business Context." Our AI coach explains why a leader chose that specific word over a simpler alternative.',
  },
  {
    icon: Repeat,
    step: '3',
    title: 'Steal & Internalize',
    description:
      'Copy the phrase. Practice saying it out loud. Use the roleplay scenarios to imagine yourself saying it. Treat these sentences like a script for your future success.',
  },
];

const HowToUseIt: React.FC = () => {
  return (
    <section className="w-full max-w-5xl mx-auto py-16 px-4">
      <div className="border-t border-stone-200 pt-16">
        <div className="text-center mb-14">
          <h2 className="font-serif text-3xl md:text-4xl text-ink mb-4">
            How to Use LennyLingo
          </h2>
          <p className="text-stone-500 max-w-lg mx-auto">
            Three steps from browsing to fluency.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map(({ icon: Icon, step, title, description }) => (
            <div
              key={step}
              className="bg-white border border-stone-200 p-6 rounded-lg text-center"
            >
              <div className="inline-flex w-12 h-12 rounded-full bg-accent/10 items-center justify-center mb-4">
                <Icon size={22} className="text-accent" />
              </div>
              <div className="text-xs font-bold tracking-wider uppercase text-stone-400 mb-2">
                Step {step}
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

export default HowToUseIt;
