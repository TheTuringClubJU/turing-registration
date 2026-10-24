import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import RegistrationForm from './RegistrationForm';

const solo = { id: 'event-id', slug: 'example', name: 'Example Workshop', min_team_size: 1, max_team_size: 1, reg_open: true };
const reply = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });

beforeEach(() => vi.stubGlobal('fetch', vi.fn()));

async function open(event = solo) {
  fetch.mockResolvedValueOnce(reply(event));
  render(<RegistrationForm />);
  await screen.findByRole('heading', { name: event.name });
}

function fill(index = 0, email = 'person@example.com') {
  fireEvent.change(screen.getAllByLabelText('Full name')[index], { target: { value: 'Test Person' } });
  fireEvent.change(screen.getAllByLabelText('Email address')[index], { target: { value: email } });
  fireEvent.change(screen.getAllByLabelText('Phone with country code')[index], { target: { value: '+919876543210' } });
}

it('shows a closed state when there is no active event', async () => {
  fetch.mockResolvedValueOnce(reply({}, 404));
  render(<RegistrationForm />);
  expect(await screen.findByRole('heading', { name: 'Registration closed' })).toBeInTheDocument();
  expect(screen.queryByRole('form')).not.toBeInTheDocument();
});

it('offers retry after event fetch failure', async () => {
  fetch.mockRejectedValueOnce(new Error('Network unavailable'));
  render(<RegistrationForm />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Network unavailable');
  fetch.mockResolvedValueOnce(reply(solo));
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
  expect(await screen.findByRole('heading', { name: solo.name })).toBeInTheDocument();
});

it('renders solo details without a team-name field', async () => {
  await open();
  expect(screen.getAllByLabelText('Full name')).toHaveLength(1);
  expect(screen.queryByLabelText(/Team name/)).not.toBeInTheDocument();
});

it('renders every team slot up front with the correct required flags', async () => {
  await open({ ...solo, min_team_size: 2, max_team_size: 4 });
  const names = screen.getAllByLabelText('Full name');
  expect(names).toHaveLength(4);
  expect(names.map((input) => input.required)).toEqual([true, true, false, false]);
  expect(screen.getByLabelText(/Team name/)).toBeRequired();
});

it('disables submissions when reg_open is false', async () => {
  await open({ ...solo, reg_open: false });
  expect(screen.getByRole('button', { name: 'Register for event' })).toBeDisabled();
});

it('disables submissions when the closing time has passed', async () => {
  await open({ ...solo, reg_close_at: new Date(Date.now() - 1000).toISOString() });
  expect(screen.getByRole('button', { name: 'Register for event' })).toBeDisabled();
});

it('keeps client validation local and points to required fields', async () => {
  await open();
  fireEvent.click(screen.getByRole('button', { name: 'Register for event' }));
  expect(await screen.findByText('Enter a name.')).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it('submits normalized participants and displays the backend registration id', async () => {
  await open({ ...solo, min_team_size: 1, max_team_size: 4 });
  fireEvent.change(screen.getByLabelText(/Team name/), { target: { value: '  Byte Builders  ' } });
  fill(0, 'LEAD@EXAMPLE.COM');
  fill(3, 'member@example.com');
  fetch.mockResolvedValueOnce(reply({ id: 'registration-123', status: 'registered' }, 201));
  fireEvent.click(screen.getByRole('button', { name: 'Register for event' }));
  expect(await screen.findByText('registration-123')).toBeInTheDocument();
  const [url, options] = fetch.mock.calls[1];
  expect(url).toBe('/events/example/register');
  const body = JSON.parse(options.body);
  expect(body.team_name).toBe('Byte Builders');
  expect(body.participants).toHaveLength(2);
  expect(body.participants[0].email).toBe('lead@example.com');
  expect(body.participants.map((person) => person.is_team_lead)).toEqual([true, false]);
});

it('maps backend compact participant indexes back to the visible optional slot', async () => {
  await open({ ...solo, max_team_size: 4 });
  fireEvent.change(screen.getByLabelText(/Team name/), { target: { value: 'Team' } });
  fill(); fill(3, 'other@example.com');
  fetch.mockResolvedValueOnce(reply({ detail: [{ loc: ['body', 'participants', 1, 'email'], msg: 'Email rejected' }] }, 422));
  fireEvent.click(screen.getByRole('button', { name: 'Register for event' }));
  expect(await screen.findByText('Email rejected')).toBeInTheDocument();
  expect(screen.getAllByLabelText('Email address')[3]).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getAllByLabelText('Email address')[0]).toHaveValue('person@example.com');
});

it('separates stale-event rejection from duplicate conflicts', async () => {
  await open(); fill();
  fetch.mockResolvedValueOnce(reply({ detail: 'Email already registered for this event' }, 409));
  fireEvent.click(screen.getByRole('button', { name: 'Register for event' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Email already registered');
  expect(screen.queryByRole('button', { name: 'Refresh event' })).not.toBeInTheDocument();
  fetch.mockResolvedValueOnce(reply({ detail: 'Registration for event is closed' }, 409));
  fireEvent.click(screen.getByRole('button', { name: 'Register for event' }));
  expect(await screen.findByRole('button', { name: 'Refresh event' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Register for event' })).toBeDisabled();
});

it('prevents duplicate requests while a submission is pending', async () => {
  await open(); fill();
  let finish;
  fetch.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  const button = screen.getByRole('button', { name: 'Register for event' });
  fireEvent.click(button); fireEvent.click(button);
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole('button', { name: 'Submitting…' })).toBeDisabled();
  finish(reply({ id: 'confirmed' }, 201));
  await screen.findByText('confirmed');
});

it('retains entered data after an uncertain network failure', async () => {
  await open(); fill();
  fetch.mockRejectedValueOnce(new Error('Network failed'));
  fireEvent.click(screen.getByRole('button', { name: 'Register for event' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Check with the organisers');
  expect(screen.getByLabelText('Email address')).toHaveValue('person@example.com');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Register for event' })).toBeEnabled());
});
