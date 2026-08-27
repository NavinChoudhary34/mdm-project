import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Pagination } from '../Pagination';

describe('Pagination', () => {
  it('renders nothing when there is only one page', () => {
    const { container } = render(
      <Pagination page={1} hasNext={false} hasPrevious={false} onChange={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('disables Prev on the first page and Next on the last page', () => {
    render(<Pagination page={1} hasNext={true} hasPrevious={false} onChange={vi.fn()} totalCount={40} pageSize={20} />);
    expect(screen.getByRole('button', { name: /prev/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /next/i })).toBeEnabled();
  });

  it('calls onChange with page + 1 when Next is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Pagination page={2} hasNext={true} hasPrevious={true} onChange={onChange} totalCount={60} pageSize={20} />);

    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(onChange).toHaveBeenCalledWith(3);

    await user.click(screen.getByRole('button', { name: /prev/i }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it('shows total pages when totalCount is provided', () => {
    render(<Pagination page={2} hasNext={true} hasPrevious={true} onChange={vi.fn()} totalCount={45} pageSize={20} />);
    expect(screen.getByText('Page 2 of 3')).toBeInTheDocument();
  });
});
