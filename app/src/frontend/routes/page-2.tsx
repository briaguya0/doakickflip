import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/page-2')({
  component: Page2,
});

function Page2() {
  return <h2 className="text-3xl font-bold">Page 2</h2>;
}
