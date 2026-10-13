import {
  CheckCircleIcon,
  SpinnerGapIcon,
  WarningCircleIcon,
} from '@phosphor-icons/react';
import type { StatusInfo } from '@/hooks/use-status';

export function StatusIcon({ status, label }: StatusInfo) {
  switch (status) {
    case 'ok':
      return (
        <CheckCircleIcon
          weight="fill"
          className="text-success"
          aria-label={label}
        />
      );
    case 'pending':
      return (
        <SpinnerGapIcon
          weight="fill"
          className="text-info"
          aria-label={label}
        />
      );
    case 'problem':
      return (
        <WarningCircleIcon
          weight="fill"
          className="text-destructive"
          aria-label={label}
        />
      );
  }
}
