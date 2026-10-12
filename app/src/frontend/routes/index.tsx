import { GaugeIcon } from '@phosphor-icons/react';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/')({
  component: Dashboard,
  staticData: { title: 'Dashboard', icon: <GaugeIcon /> },
});

function Dashboard() {
  return null;
}
