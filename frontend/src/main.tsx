import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { AppProviders } from '@app/providers';

import './styles/index.css';

const rootEl = document.getElementById('root');
if (!rootEl) throw new Error('#root introuvable dans index.html');

createRoot(rootEl).render(
  <StrictMode>
    <AppProviders />
  </StrictMode>,
);
