import React from 'react';
import { ExternalLink, Heart } from 'lucide-react';

const KudoToLenny: React.FC = () => {
  return (
    <section className="w-full max-w-5xl mx-auto py-16 px-4">
      <div className="border-t border-stone-200 pt-16">
        <div className="bg-stone-900 text-white rounded-2xl p-8 md:p-12 text-center relative overflow-hidden">
          {/* Decorative background */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute top-4 left-8 text-8xl font-serif">&ldquo;</div>
            <div className="absolute bottom-4 right-8 text-8xl font-serif">&rdquo;</div>
          </div>

          <div className="relative z-10">
            <div className="inline-flex items-center gap-1.5 mb-4 text-amber-400">
              <Heart size={16} fill="currentColor" />
              <span className="text-xs font-semibold tracking-wider uppercase">
                A Special Thanks
              </span>
              <Heart size={16} fill="currentColor" />
            </div>

            <h2 className="font-serif text-3xl md:text-4xl mb-4">
              Thank you, Lenny Rachitsky
            </h2>

            <p className="text-stone-300 max-w-2xl mx-auto leading-relaxed mb-3">
              <a
                href="https://www.lennysnewsletter.com/podcast"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-400 hover:text-amber-300 font-semibold transition-colors"
              >
                Lenny's Podcast
              </a>{' '}
              is one of the most valuable resources in the product and tech community.
              Every week, Lenny hosts candid conversations with the sharpest minds in
              tech — sharing hard-won insights on product, growth, leadership, and career.
            </p>

            <p className="text-stone-300 max-w-2xl mx-auto leading-relaxed mb-8">
              LennyLingo exists because of this incredible content. We're deeply grateful
              for the knowledge Lenny and his guests share with the world — and we hope
              this tool helps more people access it, regardless of their native language.
            </p>

            <a
              href="https://www.lennysnewsletter.com/podcast"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-white text-stone-900 px-6 py-3 rounded-lg font-semibold hover:bg-stone-100 transition-colors"
            >
              Listen to Lenny's Podcast
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default KudoToLenny;
