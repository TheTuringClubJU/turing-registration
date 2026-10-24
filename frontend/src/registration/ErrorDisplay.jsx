export default function ErrorDisplay({ message, id }) {
  return message ? <p id={id}>{message}</p> : null;
}

export function StaleEventNotice({ onRefresh }) {
  return (
    <div role="alert">
      <p>This event is no longer open for registration.</p>
      <p>Refresh to see the latest event. Your submission was not accepted.</p>
      <button type="button" onClick={onRefresh}>Refresh event</button>
    </div>
  );
}
