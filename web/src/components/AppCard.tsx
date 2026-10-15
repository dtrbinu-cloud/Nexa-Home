import React from 'react';
import styles from './AppCard.module.css';

interface AppCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'card' | 'tile' | 'panel';
  active?: boolean;
}

export const AppCard: React.FC<AppCardProps> = ({
  children,
  className = '',
  variant = 'card',
  active = false,
  ...props
}) => {
  let variantClass = styles.card;
  if (variant === 'tile') {
    variantClass = active ? `${styles.tile} ${styles.tileActive}` : styles.tile;
  } else if (variant === 'panel') {
    variantClass = styles.panel;
  }

  return (
    <div className={`${variantClass} ${className}`} {...props}>
      {children}
    </div>
  );
};
