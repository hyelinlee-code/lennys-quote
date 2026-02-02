export interface VocabularyInsight {
  nuance: string;
  synonyms: string[];
  antonyms: string[];
}

export interface Vocabulary {
  word: string;
  definition: string;
  businessContext: string;
  exampleUsage: string;
  insight?: VocabularyInsight;
}

export interface Quote {
  id: string;
  speaker: string;
  role: string;
  company: string;
  speaker_function: string;
  speaker_expertise: string[];
  topic: string;
  topics: string[];
  text: string;
  text_ko: string;
  text_zh: string;
  text_es: string;
  fullContext: string;
  vocabulary: Vocabulary[];
  difficulty_level: string;
  timestamp: string;
}

export type Language = 'en' | 'ko' | 'zh' | 'es';

export interface Filters {
  search: string;
  functions: string[];
  topics: string[];
  difficulties: string[];
}
