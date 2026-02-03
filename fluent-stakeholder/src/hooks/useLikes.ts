import { useState, useCallback } from 'react';

const STORAGE_KEY = 'lennylingo-likes';

function loadLikes(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return new Set(JSON.parse(raw));
  } catch {
    // ignore corrupt data
  }
  return new Set();
}

function saveLikes(likes: Set<string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...likes]));
}

export function useLikes() {
  const [likes, setLikes] = useState<Set<string>>(loadLikes);

  const toggleLike = useCallback((quoteId: string) => {
    setLikes((prev) => {
      const next = new Set(prev);
      if (next.has(quoteId)) {
        next.delete(quoteId);
      } else {
        next.add(quoteId);
      }
      saveLikes(next);
      return next;
    });
  }, []);

  const isLiked = useCallback(
    (quoteId: string) => likes.has(quoteId),
    [likes]
  );

  return { likes, toggleLike, isLiked, likeCount: likes.size };
}
