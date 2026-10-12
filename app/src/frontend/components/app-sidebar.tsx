import { Link, useMatchRoute } from '@tanstack/react-router';
import { AppSidebarHeader } from '@/components/app-sidebar-header';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { useIcon, useTitle } from '@/hooks/use-static-data';

const nav = ['/', '/page-2'] as const;

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon" variant="inset">
      <AppSidebarHeader />
      <SidebarContent className="pt-2">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {nav.map((to) => (
                <NavItem key={to} to={to} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

function NavItem({ to }: { to: (typeof nav)[number] }) {
  const matchRoute = useMatchRoute();
  const title = useTitle(to);
  const icon = useIcon(to);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        render={<Link to={to} />}
        className="data-active:shadow-[inset_3px_0_0_var(--sidebar-primary)]"
        isActive={!!matchRoute({ to })}
        tooltip={title ?? undefined}
      >
        {icon}
        <span>{title}</span>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}
