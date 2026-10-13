import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  createHashHistory,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router';
import type { ReactElement } from 'react';
import { createRoot } from 'react-dom/client';
import { routeTree } from './routeTree.gen';

const queryClient = new QueryClient();
const router = createRouter({ routeTree, history: createHashHistory() });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
  interface StaticDataRouteOption {
    title: string | null;
    icon: ReactElement | null;
  }
}

const rootElement = document.getElementById('app');
if (!rootElement) {
  throw new Error('index.html is missing <div id="app">');
}

if (!rootElement.innerHTML) {
  createRoot(rootElement).render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}
