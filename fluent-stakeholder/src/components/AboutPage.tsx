import React from 'react';

const AboutPage: React.FC = () => {
  return (
    <main className="container mx-auto px-4 pb-20">
      <div className="max-w-3xl mx-auto pt-12 md:pt-16">
        <h1 className="font-serif text-4xl md:text-5xl text-ink mb-6">
          About LennyLingo
        </h1>
        <p className="text-lg text-stone-600 leading-relaxed mb-12">
          LennyLingo curates the most impactful expressions from top tech
          leaders featured on Lenny&apos;s Podcast, turning real conversations
          into a vocabulary-building experience for non-native English speakers
          in business.
        </p>

        <section className="mb-12">
          <h2 className="font-serif text-2xl text-ink mb-4">Our Mission</h2>
          <p className="text-stone-600 leading-relaxed">
            Business English isn&apos;t learned from textbooks — it&apos;s
            learned from the people who shape industries. We extract key phrases
            and idioms from real podcast conversations, enrich them with
            definitions, context, and AI-powered insights, and present them in a
            way that makes learning natural and effective.
          </p>
        </section>

        <section className="mb-12">
          <h2 className="font-serif text-2xl text-ink mb-4">How It Works</h2>
          <ol className="space-y-4 text-stone-600 leading-relaxed list-decimal list-inside">
            <li>
              <span className="font-semibold text-ink">Curate</span> — We
              select powerful quotes from Lenny&apos;s Podcast episodes featuring
              product leaders, founders, and operators.
            </li>
            <li>
              <span className="font-semibold text-ink">Enrich</span> — Each
              quote is analyzed for vocabulary, translated into Korean, Chinese,
              and Spanish, and enhanced with AI-generated insights.
            </li>
            <li>
              <span className="font-semibold text-ink">Learn</span> — Browse by
              topic, difficulty, or speaker function. Flip cards for
              translations, tap words for definitions, and save your favorites.
            </li>
          </ol>
        </section>
      </div>
    </main>
  );
};

export default AboutPage;
