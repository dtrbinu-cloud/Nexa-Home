import React from 'react';
import styles from './AppBadge.module.css';

interface AppBadgeProps {
  children: React.ReactNode;
  variant?: 'ok' | 'warn' | 'danger' | 'accent' | 'neutral';
  withDot?: boolean;
  className?: string;
}

export const AppBadge: React.FC<AppBadgeProps> = ({
  children,
  variant = 'neutral',
  withDot = true,
  className = '',
}) => {
  const variantClass = styles[variant] || styles.neutral;

  return (
    <span className={`${styles.badge} ${variantClass} ${className}`}>
      {withDot && <span className={styles.dot} />}
      <span>{children}</span>
    </span>
  );
};
