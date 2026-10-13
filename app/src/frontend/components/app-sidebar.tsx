import { Link, useMatchRoute } from '@tanstack/react-router';
import type { ReactElement } from 'react';
import { AppSidebarHeader } from '@/components/app-sidebar-header';
import { StatusIcon } from '@/components/status-icon';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import { useIcon, useTitle } from '@/hooks/use-static-data';
import { useRouteStatus } from '@/hooks/use-route-status';
import type { StatusInfo } from '@/hooks/use-status';
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
  const status = useRouteStatus(to);
  const isActive = !!matchRoute({ to });
  const statusIsProblem = status?.status === 'problem';
  const tooltip = status ? `${title} · ${status.label}` : title;

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        render={<Link to={to} />}
        className="relative pl-3"
        isActive={isActive}
        tooltip={tooltip ?? undefined}
      >
        <ActiveIndicator isActive={isActive} />
        <NavIcon icon={icon} statusIsProblem={statusIsProblem} />
        <span className="translate-y-px">{title}</span>
      </SidebarMenuButton>
      <NavStatus status={status} />
    </SidebarMenuItem>
  );
}

function NavIcon({
  icon,
  statusIsProblem,
}: {
  icon: ReactElement | null;
  statusIsProblem: boolean;
}) {
  return (
    <span className="relative flex shrink-0">
      {icon}
      {statusIsProblem && <ProblemDot />}
    </span>
  );
}

function ProblemDot() {
  const isCollapsed = useSidebar().state === 'collapsed';

  return (
    <span
      className={cn(
        'absolute -top-0.75 -right-0.75 size-2 rounded-full bg-destructive',
        'ring-2 ring-sidebar',
        'group-hover/menu-button:ring-sidebar-accent group-data-active/menu-button:ring-sidebar-accent',
        isCollapsed
          ? 'opacity-100 transition-opacity duration-200 ease-linear'
          : 'opacity-0',
      )}
    />
  );
}

function NavStatus({ status }: { status: StatusInfo | null }) {
  if (!status) {
    return null;
  }

  return (
    <SidebarMenuBadge className="[&_svg]:size-4">
      <StatusIcon {...status} />
    </SidebarMenuBadge>
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
