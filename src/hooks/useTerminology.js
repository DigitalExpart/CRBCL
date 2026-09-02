import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

// Approved cultural dictionary fallbacks (Approved CRBCL terminology structure)
const CULTURAL_FALLBACK_DICTIONARY = {
  'relationship.mother': 'Nikāwiy (Mother)',
  'relationship.father': 'Nōhtāwiy (Father)',
  'relationship.grandmother': 'Nōhkom (Grandmother)',
  'relationship.grandfather': 'Nimōsom (Grandfather)',
  'relationship.child': 'Awāsis (Child)',
  'program.sacred_wolf': 'Sacred Wolf Lodge (Miyowāwisin)',
  'dept.prevention': 'Prevention & Healing Services',
  'dept.post_majority': 'Post-Majority Youth Empowerment',
};

export function useTerminology() {
  const [translations, setTranslations] = useState(CULTURAL_FALLBACK_DICTIONARY);
  const [language, setLanguage] = useState(localStorage.getItem('crbcl_user_lang') || 'en');

  useEffect(() => {
    async function loadTranslations() {
      try {
        const res = await api.get('/lookups/translations');
        if (res && Array.isArray(res)) {
          const mapped = { ...CULTURAL_FALLBACK_DICTIONARY };
          res.forEach(item => {
            if (item.key && item.translation) {
              mapped[item.key] = item.translation;
            }
          });
          setTranslations(mapped);
        }
      } catch (err) {
        // Fallback to approved dictionary
      }
    }
    loadTranslations();
  }, []);

  const t = useCallback((key, fallback) => {
    if (language === 'cr' && translations[key]) {
      return translations[key];
    }
    return fallback || translations[key] || key;
  }, [language, translations]);

  const changeLanguage = (newLang) => {
    setLanguage(newLang);
    localStorage.setItem('crbcl_user_lang', newLang);
  };

  return { t, language, changeLanguage, translations };
}
