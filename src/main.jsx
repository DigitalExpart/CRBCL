import React from 'react'
import ReactDOM from 'react-dom/client'
import App from '@/App.jsx'
import '@/index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <App />
)

// Conditionally register application shell service worker when feature flag is enabled
if (typeof window !== 'undefined' && 'serviceWorker' in navigator && import.meta.env.VITE_CRBCL_OFFLINE_WEB_ENABLED === 'true') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('CRBCL ServiceWorker registration skipped:', err);
    });
  });
}
