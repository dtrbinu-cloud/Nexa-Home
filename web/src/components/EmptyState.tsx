import React from 'react';
import styles from './EmptyState.module.css';

export interface EmptyStateProps {
  icon?: React.ReactNode | React.ComponentType<{ size?: number }>;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) return icon;
    if (typeof icon === 'function' || typeof icon === 'object') {
      const IconComp = icon as React.ComponentType<{ size?: number }>;
      return <IconComp size={28} />;
    }
    return icon as React.ReactNode;
  };

  return (
    <div className={`${styles.container} ${className}`}>
      {icon && <div className={styles.iconCircle}>{renderIcon()}</div>}
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.description}>{description}</p>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
};
