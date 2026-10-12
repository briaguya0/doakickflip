import { createRootRoute, Outlet } from '@tanstack/react-router';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex flex-col items-start gap-4 p-8">
        <SidebarTrigger />
        <Outlet />
      </main>
    </SidebarProvider>
  );
}
