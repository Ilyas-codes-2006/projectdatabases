import type {Message} from "../hooks/useMessage";

interface Props {
  message: Message | null;
  onClose: () => void;
}

export default function MessageBanner({ message, onClose }: Props) {
  if (!message) return null;
  return (
    <div className={`message-banner ${message.type}`} onClick={onClose}>
      {message.text} <span className="message-close">×</span>
    </div>
  );
}