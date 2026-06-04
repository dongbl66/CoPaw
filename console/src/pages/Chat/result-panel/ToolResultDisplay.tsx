interface ToolResultDisplayProps {
  input?: unknown;
  output?: unknown;
  content?: unknown;
}

function parseToolPayload(value: unknown): unknown {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

export default function ToolResultDisplay({
  output,
  content,
}: ToolResultDisplayProps) {
  const rawPayload = output ?? content ?? "";
  const parsedPayload = parseToolPayload(rawPayload);
  const displayText =
    typeof parsedPayload === "string"
      ? parsedPayload
      : JSON.stringify(parsedPayload, null, 2);

  return (
    <pre
      style={{
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        margin: 0,
      }}
    >
      {displayText}
    </pre>
  );
}
