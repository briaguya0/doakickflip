import { GearIcon } from '@phosphor-icons/react';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/settings')({
  component: Settings,
  staticData: { title: 'Settings', icon: <GearIcon /> },
});

function Settings() {
  return null;
}
