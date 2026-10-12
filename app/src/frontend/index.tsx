import {
  createHashHistory,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router';
import { createRoot } from 'react-dom/client';
import { routeTree } from './routeTree.gen';

const router = createRouter({ routeTree, history: createHashHistory() });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
  interface StaticDataRouteOption {
    title: string | null;
  }
}

const rootElement = document.getElementById('app');
if (!rootElement) {
  throw new Error('index.html is missing <div id="app">');
}

if (!rootElement.innerHTML) {
  createRoot(rootElement).render(<RouterProvider router={router} />);
}
