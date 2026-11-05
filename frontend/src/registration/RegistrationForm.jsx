import { useEffect, useRef, useState } from 'react';
import { buildSubmission, fetchActiveEvent, submitRegistration } from './SubmissionHandler';
import ErrorDisplay, { StaleEventNotice } from './ErrorDisplay';
import ConfirmationScreen from './ConfirmationScreen';

const blank = () => ({ name: '', email: '', phone: '', usn: '' });
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
  const [verified, setVerified] = useState(false);
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
  const closed = !event?.reg_open || (event.reg_close_at && now >= Date.parse(event.reg_close_at));
  const fields = error?.fields || {};

  async function onSubmit(e) {
    e.preventDefault();
    if (closed || error?.stale || submitting.current || !verified) return;
    submitting.current = true;
    setPending(true);
    setError(null);
    try {
      const submission = buildSubmission(event, teamName, slots);
      setConfirmation(await submitRegistration(event.slug, submission));
    } catch (err) {
      setError(err);
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

  const isSolo = event.max_team_size === 1;
  const mandatoryTeammates = Math.max(0, event.min_team_size - 1);

  return (
    <section>
      <p style={{ letterSpacing: '0.08em', textTransform: 'uppercase', fontSize: '12px', color: '#86868b' }}>
        The Turing Club · Event Registration
      </p>
      <h1>{event.name}</h1>

      <p style={{ fontSize: '15px', color: '#e5e5ea', lineHeight: '1.6', margin: '8px 0 24px' }}>
        {isSolo
          ? 'Individual Event. Please fill in your details below to confirm your entry pass.'
          : (
            <span>
              <strong>Team Size: {event.min_team_size} to {event.max_team_size} members.</strong> Complete details for your Team Lead and at least {mandatoryTeammates} teammate{mandatoryTeammates > 1 ? 's' : ''} to register (other than the Team Lead, {mandatoryTeammates} teammate is mandatory). Additional member slots are optional.
            </span>
          )
        }
      </p>

      {closed && <p role="status">Registration is closed for this event.</p>}
      {error?.stale ? <div><StaleEventNotice onRefresh={refresh} /></div> : null}

      <form ref={formRef} onSubmit={onSubmit} noValidate aria-label="Event registration">
        <fieldset disabled={pending || closed || error?.stale}>
          {!isSolo && (
            <div style={{ marginBottom: '24px' }}>
              <label htmlFor="team-name">Team Name (Required)</label>
              <input
                id="team-name"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                maxLength={200}
                required
                placeholder="e.g. Binary Beasts"
                className={fieldStyle}
                aria-invalid={!!fields.team_name}
                aria-describedby={fields.team_name ? 'team-error' : undefined}
              />
              <ErrorDisplay id="team-error" message={fields.team_name} />
            </div>
          )}

          {slots.map((slot, index) => {
            const isLead = index === 0;
            const isMandatory = index < event.min_team_size;
            const cardTitle = isLead
              ? (isSolo ? 'Your Details' : 'Team Lead (Primary Contact)')
              : `Team Member ${index + 1}`;
            const badgeLabel = isMandatory ? 'Mandatory' : 'Optional';

            return (
              <fieldset key={index} style={{ marginBottom: '24px' }}>
                <legend>
                  {cardTitle}{' '}
                  <span style={{ fontSize: '12px', opacity: 0.85 }}>
                    · {badgeLabel}
                  </span>
                </legend>

                {isLead && !isSolo && (
                  <p style={{ fontSize: '12px', color: '#86868b', margin: '-4px 0 16px' }}>
                    The entry pass and check-in QR code will be delivered to this email.
                  </p>
                )}

                <div className="registration-fields">
                  {['name', 'email', 'phone', 'usn'].map((field) => {
                    const key = `participants.${index}.${field}`;
                    const id = `participant-${index}-${field}`;
                    const labelText = field === 'name'
                      ? 'Full Name'
                      : field === 'email'
                        ? 'Email Address'
                        : field === 'phone'
                          ? 'Phone with Country Code'
                          : 'USN / Application Number';

                    return (
                      <div key={field} className={field === 'name' ? 'registration-full-width' : ''}>
                        <label htmlFor={id}>{labelText}</label>
                        <input
                          id={id}
                          type={field === 'email' ? 'email' : field === 'phone' ? 'tel' : 'text'}
                          value={slot[field]}
                          required={isMandatory}
                          maxLength={field === 'name' ? 200 : field === 'email' ? 320 : field === 'phone' ? 16 : 50}
                          placeholder={field === 'usn' ? 'e.g. JUUG25LBTECH31055' : undefined}
                          autoComplete={isLead ? (field === 'phone' ? 'tel' : field === 'name' ? 'name' : field === 'email' ? 'email' : 'off') : 'off'}
                          className={fieldStyle}
                          aria-invalid={!!fields[key]}
                          aria-describedby={fields[key] ? `${id}-error` : field === 'phone' ? `${id}-hint` : undefined}
                          onChange={(e) => setSlots((previous) => previous.map((item, i) => i === index ? { ...item, [field]: e.target.value } : item))}
                        />
                        {field === 'phone' && <p id={`${id}-hint`}>For example, +919876543210</p>}
                        <ErrorDisplay id={`${id}-error`} message={fields[key]} />
                      </div>
                    );
                  })}
                </div>
              </fieldset>
            );
          })}

          {event.max_team_size > event.min_team_size && (
            <div style={{
              background: '#161617',
              border: '1px solid #2c2c2e',
              borderRadius: '8px',
              padding: '12px 16px',
              margin: '20px 0 24px',
              fontSize: '13px',
              color: '#d1d1d6',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>💡</span>
              <span><strong>Tip:</strong> If your team has fewer members, simply leave the extra member sections empty.</span>
            </div>
          )}

          {/* Verification & Accuracy Checkbox */}
          <div style={{
            background: '#1c1c1e',
            border: '1px solid #3a3a3c',
            borderRadius: '10px',
            padding: '16px',
            margin: '24px 0'
          }}>
            <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                id="verify-details"
                checked={verified}
                onChange={(e) => setVerified(e.target.checked)}
                style={{ width: '18px', height: '18px', marginTop: '3px', cursor: 'pointer', accentColor: '#2997ff' }}
                required
              />
              <span style={{ fontSize: '13px', lineHeight: '1.5', color: '#ffffff' }}>
                <strong>I have verified that all entered details are accurate.</strong>
                <span style={{ display: 'block', color: '#a1a1a6', fontSize: '12px', marginTop: '4px' }}>
                  Please double-check your email addresses and USNs. Your entry pass and check-in QR code will be delivered exclusively to the Team Lead's email address.
                </span>
              </span>
            </label>
          </div>

          {error && !error.stale && (
            <div role="alert" style={{ marginBottom: '16px' }}>
              <p>{error.message}</p>
              <ErrorDisplay message={fields.participants || fields.form} />
            </div>
          )}

          <button
            type="submit"
            disabled={pending || closed || error?.stale || !verified}
            style={{
              opacity: (!verified || pending || closed) ? 0.6 : 1,
              cursor: (!verified || pending || closed) ? 'not-allowed' : 'pointer'
            }}
          >
            {pending ? 'Submitting…' : 'Register for event'}
          </button>
        </fieldset>
      </form>
    </section>
  );
}
