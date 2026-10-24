import { afterEach, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

vi.mock('../attendance/AttendanceDashboard', () => ({ default: () => <div>Existing attendance dashboard</div> }));
vi.mock('../attendance/OrganiserLogin', () => ({ default: () => <div>Existing organiser login</div> }));
vi.mock('../registration/RegistrationForm', () => ({ default: () => <div>Public event form</div> }));

afterEach(() => {
  localStorage.clear();
  window.history.replaceState({}, '', '/');
});

it('opens the public registration route without an organiser login', () => {
  window.history.replaceState({}, '', '/register');
  render(<App />);
  expect(screen.getByText('Public event form')).toBeInTheDocument();
});

it('preserves the existing login route', () => {
  render(<App />);
  expect(screen.getByText('Existing organiser login')).toBeInTheDocument();
});

it('preserves the logged-in attendance route', () => {
  localStorage.setItem('organiser_token', 'test-token');
  render(<App />);
  expect(screen.getByText('Existing attendance dashboard')).toBeInTheDocument();
});
