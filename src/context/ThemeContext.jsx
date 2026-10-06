import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from '@/api';

const THEME_STORAGE_KEY = 'crbcl_theme_preferences';

export const VALID_ACCENTS = [
  { key: 'crbcl', label: 'CRBCL Crimson (Default)', color: '#8B2626', bgHsl: '4 60% 38%' },
  { key: 'burgundy', label: 'Deep Burgundy', color: '#821D30', bgHsl: '348 60% 32%' },
  { key: 'earth', label: 'Warm Earth & Clay', color: '#9E4A22', bgHsl: '24 65% 38%' },
  { key: 'forest', label: 'Evergreen & Sage', color: '#267344', bgHsl: '145 50% 30%' },
  { key: 'prairie', label: 'Prairie Sun & Gold', color: '#A57313', bgHsl: '38 80% 36%' },
  { key: 'ocean', label: 'Deep River Blue', color: '#245C99', bgHsl: '215 65% 40%' },
  { key: 'teal', label: 'Boreal Spruce Teal', color: '#217A6C', bgHsl: '174 60% 32%' },
  { key: 'neutral', label: 'Refined Slate', color: '#485669', bgHsl: '220 20% 35%' },
];

export const DEFAULT_PREFERENCES = {
  theme_mode: 'system', // 'light' | 'dark' | 'system'
  accent_theme: 'crbcl',
  density: 'comfortable', // 'comfortable' | 'compact'
  sidebar_collapsed: false,
  card_radius: 'rounded', // 'rounded' | 'subtle'
  reduced_motion: false,
  high_contrast: false,
  default_landing_dashboard: null,
};

function getStoredPreferences() {
  try {
    const raw = localStorage.getItem(THEME_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_PREFERENCES, ...parsed };
    }
  } catch (e) {
    console.warn('Failed to parse stored theme preferences:', e);
  }
  return { ...DEFAULT_PREFERENCES };
}

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [preferences, setPreferences] = useState(getStoredPreferences);
  const [systemIsDark, setSystemIsDark] = useState(() => {
    return typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [isSyncing, setIsSyncing] = useState(false);

  // Monitor system dark mode changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => setSystemIsDark(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Compute active dark mode state
  const isDark = preferences.theme_mode === 'dark' || (preferences.theme_mode === 'system' && systemIsDark);

  // Apply DOM classes immediately whenever preferences or system dark changes
  useEffect(() => {
    const root = document.documentElement;

    // Dark mode
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Accent theme
    VALID_ACCENTS.forEach(({ key }) => root.classList.remove(`theme-${key}`));
    const validKey = VALID_ACCENTS.some((a) => a.key === preferences.accent_theme)
      ? preferences.accent_theme
      : 'crbcl';
    root.classList.add(`theme-${validKey}`);

    // Density
    if (preferences.density === 'compact') {
      root.classList.add('density-compact');
    } else {
      root.classList.remove('density-compact');
    }

    // Radius
    root.classList.remove('radius-rounded', 'radius-subtle');
    root.classList.add(`radius-${preferences.card_radius === 'subtle' ? 'subtle' : 'rounded'}`);

    // High contrast
    if (preferences.high_contrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Reduced motion
    if (preferences.reduced_motion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }

    // Persist to local storage
    try {
      localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(preferences));
    } catch (e) {
      console.warn('Failed to save theme preferences to localStorage:', e);
    }
  }, [preferences, isDark]);

  // Pull server-authoritative preferences on mount or auth refresh
  const syncWithServer = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/users/me/preferences');
      if (res && res.appearance) {
        setPreferences((prev) => ({
          ...prev,
          ...res.appearance,
        }));
      }
    } catch {
      // Not authenticated or offline, local preferences remain active
    }
  }, []);

  useEffect(() => {
    syncWithServer();
  }, [syncWithServer]);

  // Update preferences with immediate local application and backend persistence
  const updatePreferences = useCallback(async (partial) => {
    let updated;
    setPreferences((prev) => {
      updated = { ...prev, ...partial };
      return updated;
    });

    setIsSyncing(true);
    try {
      await api.put('/api/v1/users/me/preferences', {
        appearance: {
          theme_mode: updated.theme_mode,
          accent_theme: updated.accent_theme,
          density: updated.density,
          sidebar_collapsed: updated.sidebar_collapsed,
          card_radius: updated.card_radius,
          reduced_motion: updated.reduced_motion,
          high_contrast: updated.high_contrast,
          default_landing_dashboard: updated.default_landing_dashboard || null,
        },
      });
      return { success: true };
    } catch (err) {
      console.warn('Failed to persist preferences to server:', err);
      return { success: false, error: err };
    } finally {
      setIsSyncing(false);
    }
  }, []);

  // Reset to CRBCL Defaults
  const resetToDefaults = useCallback(async () => {
    return await updatePreferences(DEFAULT_PREFERENCES);
  }, [updatePreferences]);

  const value = {
    preferences,
    isDark,
    isSyncing,
    updatePreferences,
    resetToDefaults,
    syncWithServer,
    // Convenience setters
    setThemeMode: (mode) => updatePreferences({ theme_mode: mode }),
    setAccentTheme: (accent) => updatePreferences({ accent_theme: accent }),
    setDensity: (density) => updatePreferences({ density }),
    setSidebarCollapsed: (collapsed) => updatePreferences({ sidebar_collapsed: collapsed }),
    setCardRadius: (radius) => updatePreferences({ card_radius: radius }),
    setReducedMotion: (reduced) => updatePreferences({ reduced_motion: reduced }),
    setHighContrast: (contrast) => updatePreferences({ high_contrast: contrast }),
    setDefaultLandingDashboard: (path) => updatePreferences({ default_landing_dashboard: path }),
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
