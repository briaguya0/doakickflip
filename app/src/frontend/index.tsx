import { createRoot } from 'react-dom/client';
import { App } from './App';

const rootElement = document.getElementById('app');
if (!rootElement) {
  throw new Error('index.html is missing <div id="app">');
}

if (!rootElement.innerHTML) {
  createRoot(rootElement).render(<App />);
}
