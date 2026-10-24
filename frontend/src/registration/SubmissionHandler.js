const apiBase = (import.meta.env.VITE_REGISTRATION_API_URL || '').replace(/\/$/, '');

export class RegistrationError extends Error {
  constructor(message, { fields = {}, stale = false } = {}) {
    super(message);
    this.fields = fields;
    this.stale = stale;
  }
}

export async function fetchActiveEvent(signal) {
  const response = await fetch(`${apiBase}/events/active`, { signal });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error('We could not load registrations. Please try again.');
  const event = await response.json();
  if (!event.slug || !Number.isInteger(event.min_team_size) || !Number.isInteger(event.max_team_size)
      || event.min_team_size < 1 || event.max_team_size > 4 || event.min_team_size > event.max_team_size
      || typeof event.reg_open !== 'boolean') {
    throw new Error('Registration details are unavailable. Please contact the organisers.');
  }
  return event;
}

export function buildSubmission(event, teamName, slots) {
  const fields = {};
  const participants = [];
  const indexMap = [];
  const seen = new Set();
  const team = event.max_team_size > 1;
  if (team && !teamName.trim()) fields.team_name = 'Enter your team name.';
  slots.forEach((slot, index) => {
    const participant = {
      name: slot.name.trim(), email: slot.email.trim().toLowerCase(), phone: slot.phone.trim(),
      is_team_lead: index === 0,
    };
    const filled = participant.name || participant.email || participant.phone;
    if (!filled && index >= event.min_team_size) return;
    if (!participant.name) fields[`participants.${index}.name`] = 'Enter a name.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(participant.email)) {
      fields[`participants.${index}.email`] = 'Enter a valid email address.';
    } else if (seen.has(participant.email)) {
      fields[`participants.${index}.email`] = 'Each participant needs a different email.';
    }
    if (!/^\+[1-9][0-9]{7,14}$/.test(participant.phone)) {
      fields[`participants.${index}.phone`] = 'Use a country code, for example +919876543210.';
    }
    seen.add(participant.email);
    indexMap.push(index);
    participants.push(participant);
  });
  if (Object.keys(fields).length) throw new RegistrationError('Please check the highlighted fields.', { fields });
  return { payload: { team_name: team ? teamName.trim() : null, participants }, indexMap };
}

export async function submitRegistration(slug, { payload, indexMap }) {
  let response;
  try {
    response = await fetch(`${apiBase}/events/${encodeURIComponent(slug)}/register`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
  } catch {
    throw new RegistrationError('We could not confirm your submission. Check with the organisers before trying again.');
  }
  const body = await response.json().catch(() => ({}));
  if (response.status === 422 && Array.isArray(body.detail)) {
    const fields = {};
    body.detail.forEach(({ loc = [], msg }) => {
      const path = loc.filter((part) => part !== 'body');
      if (path[0] === 'participants' && Number.isInteger(path[1])) path[1] = indexMap[path[1]] ?? path[1];
      fields[path.join('.') || 'form'] = String(msg || 'Invalid value.');
    });
    throw new RegistrationError('Please check the highlighted fields.', { fields });
  }
  if (!response.ok) {
    const message = typeof body.detail === 'string' ? body.detail : 'Registration could not be completed. Please contact the organisers.';
    const stale = response.status === 404 || (response.status === 409 && /closed|not active|no longer open/i.test(message));
    throw new RegistrationError(message, { stale });
  }
  if (response.status !== 201 || typeof body.id !== 'string') {
    throw new RegistrationError('We could not confirm your registration ID. Please contact the organisers before submitting again.');
  }
  return body;
}
