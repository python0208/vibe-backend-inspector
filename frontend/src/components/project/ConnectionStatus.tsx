interface ConnectionStatusProps {
  label: string;
  state: "idle" | "checking" | "success" | "error";
  message?: string;
}

export function ConnectionStatus({ label, state, message }: ConnectionStatusProps) {
  return (
    <div className={`connection-status ${state}`}>
      <div>
        <span>{label}</span>
        {message ? <p>{message}</p> : null}
      </div>
      <strong>{state}</strong>
    </div>
  );
}
