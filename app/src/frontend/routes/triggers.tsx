import { LightningIcon } from '@phosphor-icons/react';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/triggers')({
  component: Triggers,
  staticData: { title: 'Triggers', icon: <LightningIcon /> },
});

function Triggers() {
  return null;
}
