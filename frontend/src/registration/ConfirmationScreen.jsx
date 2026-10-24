export default function ConfirmationScreen({ registration, event }) {
  return (
    <section role="status">
      <p>REGISTRATION SAVED</p>
      <h1>You're registered.</h1>
      <p>Your place at {event.name} is registered. Keep this ID for event check-in.</p>
      <p>Registration ID</p>
      <p>{registration.id}</p>
      <p>Check your inbox for any confirmation from the organisers.</p>
      <a href="/">Organiser login</a>
    </section>
  );
}
