import React from 'react';
import styles from './AppButton.module.css';

interface AppButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'danger' | 'ghost';
  iconOnly?: boolean;
}

export const AppButton: React.FC<AppButtonProps> = ({
  children,
  className = '',
  variant = 'primary',
  iconOnly = false,
  ...props
}) => {
  const variantClass = styles[variant] || styles.primary;
  const iconClass = iconOnly ? styles.iconOnly : '';

  return (
    <button className={`${styles.btn} ${variantClass} ${iconClass} ${className}`} {...props}>
      {children}
    </button>
  );
};
