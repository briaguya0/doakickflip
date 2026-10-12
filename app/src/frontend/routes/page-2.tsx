import { NumberCircleTwoIcon } from '@phosphor-icons/react';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/page-2')({
  component: Page2,
  staticData: { title: 'Page 2', icon: <NumberCircleTwoIcon /> },
});

function Page2() {
  return null;
}
