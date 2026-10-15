import React from 'react';
import styles from './AppSwitch.module.css';

export interface AppSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  id?: string;
  label?: string;
  'aria-label'?: string;
  ariaLabel?: string;
}

export const AppSwitch: React.FC<AppSwitchProps> = ({
  checked,
  onChange,
  disabled = false,
  id,
  label,
  'aria-label': ariaLabelProp,
  ariaLabel,
}) => {
  const switchId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
  const effectiveAriaLabel = ariaLabel || ariaLabelProp || label;

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!disabled) {
      onChange(!checked);
    }
  };

  return (
    <label
      htmlFor={switchId}
      className={`${styles.switchLabel} ${checked ? styles.checked : ''} ${disabled ? styles.disabled : ''}`}
      onClick={handleClick}
    >
      <input
        type="checkbox"
        id={switchId}
        checked={checked}
        disabled={disabled}
        readOnly
        className={styles.hiddenCheckbox}
        aria-label={effectiveAriaLabel}
      />
      <span className={styles.switchTrack}>
        <span className={styles.switchKnob} />
      </span>
      {label && <span>{label}</span>}
    </label>
  );
};
