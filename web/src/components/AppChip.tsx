import React from 'react';
import styles from './AppChip.module.css';

interface AppChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export const AppChip: React.FC<AppChipProps> = ({
  children,
  active = false,
  className = '',
  ...props
}) => {
  return (
    <button
      type="button"
      className={`${styles.chip} ${active ? styles.active : ''} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
