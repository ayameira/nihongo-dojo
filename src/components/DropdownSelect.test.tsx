import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DropdownSelect } from './DropdownSelect';

const options = [
  { value: 'ja', label: 'Japanese' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French', disabled: true },
  { value: 'ko', label: 'Korean' },
];

const renderDropdown = (props: Partial<React.ComponentProps<typeof DropdownSelect>> = {}) => {
  const onChange = vi.fn();
  render(
    <DropdownSelect
      label="Language"
      ariaLabel="Target language"
      value="ja"
      options={options}
      onChange={onChange}
      {...props}
    />
  );
  return { onChange };
};

describe('DropdownSelect', () => {
  it('shows the selected option label on the trigger', () => {
    renderDropdown();

    expect(screen.getByRole('button', { name: 'Target language' })).toHaveTextContent('Japanese');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('opens the menu on click and lists all options', async () => {
    const user = userEvent.setup();
    renderDropdown();

    await user.click(screen.getByRole('button', { name: 'Target language' }));

    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(screen.getAllByRole('option')).toHaveLength(4);
    expect(screen.getByRole('option', { name: /Japanese/ })).toHaveAttribute('aria-selected', 'true');
  });

  it('selects an option on click and closes the menu', async () => {
    const user = userEvent.setup();
    const { onChange } = renderDropdown();

    await user.click(screen.getByRole('button', { name: 'Target language' }));
    await user.click(screen.getByRole('option', { name: /Spanish/ }));

    expect(onChange).toHaveBeenCalledWith('es');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('ignores clicks on disabled options', async () => {
    const user = userEvent.setup();
    const { onChange } = renderDropdown();

    await user.click(screen.getByRole('button', { name: 'Target language' }));
    await user.click(screen.getByRole('option', { name: /French/ }));

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole('listbox')).toBeInTheDocument();
  });

  it('supports keyboard navigation, skipping disabled options', async () => {
    const user = userEvent.setup();
    const { onChange } = renderDropdown();

    const trigger = screen.getByRole('button', { name: 'Target language' });
    trigger.focus();
    await user.keyboard('{Enter}{ArrowDown}{ArrowDown}{Enter}');

    // From Japanese, down twice lands on Korean because French is disabled
    expect(onChange).toHaveBeenCalledWith('ko');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('closes on Escape without selecting', async () => {
    const user = userEvent.setup();
    const { onChange } = renderDropdown();

    await user.click(screen.getByRole('button', { name: 'Target language' }));
    await user.keyboard('{Escape}');

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('closes when clicking outside', async () => {
    const user = userEvent.setup();
    renderDropdown();

    await user.click(screen.getByRole('button', { name: 'Target language' }));
    await user.click(document.body);

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
