import { useEffect, useId, useRef, useState } from 'react';

export interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface DropdownSelectProps {
  label: string;
  ariaLabel: string;
  value: string;
  options: DropdownOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  title?: string;
  tutorialTarget?: string;
}

export function DropdownSelect({
  label,
  ariaLabel,
  value,
  options,
  onChange,
  disabled = false,
  title,
  tutorialTarget,
}: DropdownSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const listboxId = useId();

  const selectedOption = options.find(option => option.value === value);
  const optionId = (index: number) => `${listboxId}-option-${index}`;

  useEffect(() => {
    if (!isOpen) return;

    const handlePointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && highlightedIndex >= 0) {
      listRef.current
        ?.querySelector(`#${CSS.escape(optionId(highlightedIndex))}`)
        ?.scrollIntoView?.({ block: 'nearest' });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, highlightedIndex]);

  const findEnabled = (from: number, step: 1 | -1) => {
    for (let i = from; i >= 0 && i < options.length; i += step) {
      if (!options[i].disabled) return i;
    }
    return -1;
  };

  const openMenu = () => {
    const selectedIndex = options.findIndex(option => option.value === value);
    setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : findEnabled(0, 1));
    setIsOpen(true);
  };

  const closeMenu = () => {
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const selectOption = (option: DropdownOption) => {
    if (option.disabled) return;
    onChange(option.value);
    closeMenu();
  };

  const moveHighlight = (step: 1 | -1) => {
    const start = highlightedIndex < 0
      ? (step === 1 ? 0 : options.length - 1)
      : highlightedIndex + step;
    const next = findEnabled(start, step);
    if (next >= 0) setHighlightedIndex(next);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (!isOpen) {
      if (['Enter', ' ', 'ArrowDown', 'ArrowUp'].includes(event.key)) {
        event.preventDefault();
        openMenu();
      }
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        moveHighlight(1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        moveHighlight(-1);
        break;
      case 'Home':
        event.preventDefault();
        setHighlightedIndex(findEnabled(0, 1));
        break;
      case 'End':
        event.preventDefault();
        setHighlightedIndex(findEnabled(options.length - 1, -1));
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (highlightedIndex >= 0) selectOption(options[highlightedIndex]);
        break;
      case 'Escape':
        event.preventDefault();
        closeMenu();
        break;
      case 'Tab':
        closeMenu();
        break;
    }
  };

  return (
    <div
      ref={containerRef}
      className={`model-selector${isOpen ? ' open' : ''}`}
      title={title}
      data-tutorial-target={tutorialTarget}
    >
      <span className="model-selector-label">{label}</span>
      <button
        type="button"
        className="model-select"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        aria-activedescendant={isOpen && highlightedIndex >= 0 ? optionId(highlightedIndex) : undefined}
        disabled={disabled}
        onClick={() => (isOpen ? closeMenu() : openMenu())}
        onKeyDown={handleKeyDown}
      >
        {selectedOption?.label ?? ''}
      </button>
      {isOpen && (
        <ul ref={listRef} id={listboxId} className="select-menu" role="listbox" aria-label={ariaLabel}>
          {options.map((option, index) => (
            <li
              key={option.value}
              id={optionId(index)}
              role="option"
              aria-selected={option.value === value}
              aria-disabled={option.disabled || undefined}
              className={
                `select-menu-option${index === highlightedIndex ? ' highlighted' : ''}${option.disabled ? ' disabled' : ''}`
              }
              onPointerDown={(event) => event.preventDefault()}
              onClick={() => selectOption(option)}
              onMouseEnter={() => !option.disabled && setHighlightedIndex(index)}
            >
              <span className="select-menu-check" aria-hidden="true">
                {option.value === value ? '✓' : ''}
              </span>
              <span className="select-menu-text">{option.label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
