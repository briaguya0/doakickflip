import { IconContext } from '@phosphor-icons/react';
import { SidebarTrigger } from '@/components/ui/sidebar';

export function AppSidebarTrigger() {
  return (
    <IconContext.Provider value={{ weight: 'bold' }}>
      <SidebarTrigger />
    </IconContext.Provider>
  );
}
