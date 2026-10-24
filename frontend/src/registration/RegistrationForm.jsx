import { useEffect, useRef, useState } from 'react';
import { buildSubmission, fetchActiveEvent, submitRegistration } from './SubmissionHandler';
import ErrorDisplay, { StaleEventNotice } from './ErrorDisplay';
import ConfirmationScreen from './ConfirmationScreen';

const blank = () => ({ name: '', email: '', phone: '' });
const fieldStyle = 'registration-input';

export default function RegistrationForm() {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [revision, setRevision] = useState(0);
  const [teamName, setTeamName] = useState('');
  const [slots, setSlots] = useState([]);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);
  const [confirmation, setConfirmation] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const submitting = useRef(false);
  const formRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchActiveEvent(controller.signal).then((data) => {
      if (controller.signal.aborted) return;
      setEvent(data);
      setSlots(Array.from({ length: data?.max_team_size || 0 }, blank));
      setTeamName('');
    }).catch((err) => {
      if (!controller.signal.aborted) setLoadError(err.message);
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    return () => controller.abort();
  }, [revision]);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const refresh = () => {
    setLoading(true);
    setLoadError('');
    setError(null);
    setRevision((value) => value + 1);
  };
  const closed = !event?.reg_open || (event.reg_close_at && now>= Date.parse(event.reg_close_at));
  const fields = error?.fields || {};

  async function onSubmit(e) {
    e.preventDefault();
    if (closed || error?.stale || submitting.current) return;
    submitting.current = true;
    setPending(true);
    setError(null);
    try {
      const submission = buildSubmission(event, teamName, slots);
      setConfirmation(await submitRegistration(event.slug, submission));
    } catch (err) {
      setError(err);
      // Keep user data intact and move keyboard focus to the first invalid field.
      setTimeout(() => formRef.current?.querySelector('[aria-invalid="true"]')?.focus(), 0);
    } finally {
      submitting.current = false;
      setPending(false);
    }
  }

  if (loading) return <p role="status">Loading event registration…</p>;
  if (loadError) return <div role="alert"><p>{loadError}</p><button onClick={refresh}>Try again</button></div>;
  if (!event) return <section><h1>Registration closed</h1><p>There is no active event accepting registrations right now. Check back soon.</p><button onClick={refresh}>Refresh events</button></section>;
  if (confirmation) return <ConfirmationScreen registration={confirmation} event={event} />;

  return (
    <section>
      <p>The Turing Club · Event registration</p>
      <h1>{event.name}</h1>
      <p>{event.max_team_size === 1 ? 'Register your place. All fields are required.' : `Teams of ${event.min_team_size}–${event.max_team_size}. The first ${event.min_team_size} participant blocks are required.`}</p>
      {closed && <p role="status">Registration is closed for this event.</p>}
      {error?.stale ? <div><StaleEventNotice onRefresh={refresh} /></div> : null}
      <form ref={formRef} onSubmit={onSubmit} noValidate aria-label="Event registration">
        <fieldset disabled={pending || closed || error?.stale}>
          {event.max_team_size> 1 && <div>
            <label htmlFor="team-name">Team name (required)</label>
            <input id="team-name" value={teamName} onChange={(e) => setTeamName(e.target.value)} maxLength={200} required className={fieldStyle} aria-invalid={!!fields.team_name} aria-describedby={fields.team_name ? 'team-error' : undefined} />
            <ErrorDisplay id="team-error" message={fields.team_name} />
          </div>}
          {slots.map((slot, index) => <fieldset key={index}>
            <legend>{index === 0 ? (event.max_team_size === 1 ? 'Your Details' : 'Team Lead') : `Participant ${index + 1}`} <span>· {index < event.min_team_size ? 'Required' : 'Optional'}</span></legend>
            <div className="registration-fields">
              {['name', 'email', 'phone'].map((field) => {
                const key = `participants.${index}.${field}`;
                const id = `participant-${index}-${field}`;
                return <div key={field} className={field === 'name' ? 'registration-full-width' : ''}>
                  <label htmlFor={id}>{field === 'name' ? 'Full name' : field === 'email' ? 'Email address' : 'Phone with country code'}</label>
                  <input id={id} type={field === 'email' ? 'email' : field === 'phone' ? 'tel' : 'text'} value={slot[field]} required={index < event.min_team_size} maxLength={field === 'name' ? 200 : field === 'email' ? 320 : 16} autoComplete={index === 0 ? (field === 'phone' ? 'tel' : field) : 'off'} className={fieldStyle} aria-invalid={!!fields[key]} aria-describedby={fields[key] ? `${id}-error` : field === 'phone' ? `${id}-hint` : undefined} onChange={(e) => setSlots((previous) => previous.map((item, i) => i === index ? { ...item, [field]: e.target.value } : item))} />
                  {field === 'phone' && <p id={`${id}-hint`}>For example, +919876543210</p>}
                  <ErrorDisplay id={`${id}-error`} message={fields[key]} />
                </div>;
              })}
            </div>
          </fieldset>)}
          {event.max_team_size> event.min_team_size && <p>Leave unused optional participant blocks completely blank.</p>}
          {error && !error.stale && <div role="alert"><p>{error.message}</p><ErrorDisplay message={fields.participants || fields.form} /></div>}
          <button type="submit" disabled={pending || closed || error?.stale}>{pending ? 'Submitting…' : 'Register for event'}</button>
        </fieldset>
      </form>
    </section>
  );
}
