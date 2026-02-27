import { useEffect, useState } from 'react';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        themeParams?: Record<string, string>;
        initDataUnsafe?: { user?: { id?: number; first_name?: string; username?: string } };
      }
    }
  }
}

export const useTelegram = () => {
  const [webApp] = useState(() => window.Telegram?.WebApp);

  useEffect(() => {
    if (!webApp) return;
    webApp.ready();
    webApp.expand();
    const p = webApp.themeParams ?? {};
    if (p.bg_color) document.documentElement.style.setProperty('--tg-bg', p.bg_color);
    if (p.text_color) document.documentElement.style.setProperty('--tg-text', p.text_color);
    if (p.hint_color) document.documentElement.style.setProperty('--tg-hint', p.hint_color);
    if (p.button_color) document.documentElement.style.setProperty('--tg-btn', p.button_color);
  }, [webApp]);

  return {
    webApp,
    user: webApp?.initDataUnsafe?.user
  };
};
