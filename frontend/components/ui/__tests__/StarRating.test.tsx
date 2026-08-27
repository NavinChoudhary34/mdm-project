import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StarRating } from '../StarRating';

describe('StarRating', () => {
  it('renders 5 stars and the numeric value', () => {
    render(<StarRating value={6} readOnly />);
    expect(screen.getAllByRole('button')).toHaveLength(5);
    expect(screen.getByText('6/10')).toBeInTheDocument();
  });

  it('calls onChange with the score for the clicked star (2 points per star)', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<StarRating value={0} onChange={onChange} />);

    // The 3rd star represents a score of 6 (each star = 2 points).
    await user.click(screen.getByLabelText('Rate 6 out of 10'));

    expect(onChange).toHaveBeenCalledWith(6);
  });

  it('does not respond to clicks when readOnly', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<StarRating value={4} onChange={onChange} readOnly />);

    await user.click(screen.getByLabelText('Rate 8 out of 10'));

    expect(onChange).not.toHaveBeenCalled();
  });
});
