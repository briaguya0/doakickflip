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
  useSidebar,
} from '@/components/ui/sidebar';
import { useIcon, useTitle } from '@/hooks/use-static-data';
import { cn } from '@/lib/utils';

const nav = ['/', '/triggers', '/twitch', '/settings'] as const;

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
  const isActive = !!matchRoute({ to });

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        render={<Link to={to} />}
        className="relative pl-3"
        isActive={isActive}
        tooltip={title ?? undefined}
      >
        <ActiveIndicator isActive={isActive} />
        {icon}
        <span className="translate-y-px">{title}</span>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}

const layer =
  'absolute inset-0 rounded-md transition-opacity duration-200 ease-linear';

function ActiveIndicator({ isActive }: { isActive: boolean }) {
  const isCollapsed = useSidebar().state === 'collapsed';
  const showBar = isActive && !isCollapsed;
  const showOutline = isActive && isCollapsed;

  return (
    <>
      <span
        className={cn(
          layer,
          'shadow-[inset_3px_0_0_var(--sidebar-primary)]',
          showBar ? 'opacity-100' : 'opacity-0',
        )}
      />
      <span
        className={cn(
          layer,
          'inset-ring-sidebar-primary inset-ring',
          showOutline ? 'opacity-100' : 'opacity-0',
        )}
      />
    </>
  );
}
