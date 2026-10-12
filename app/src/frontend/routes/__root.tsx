import { createRootRoute, Outlet } from '@tanstack/react-router';
import { AppSidebar } from '@/components/app-sidebar';
import { PageHeader } from '@/components/page-header';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

export const Route = createRootRoute({
  component: RootLayout,
  staticData: { title: null },
});

function RootLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <PageHeader />
        <div className="flex flex-col items-start gap-4 p-8">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
