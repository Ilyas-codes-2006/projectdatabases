import { createContext, useContext, useState, type ReactNode } from "react";

export interface Message {
  text: string;
  type: "error" | "success";
}

interface MessageContextType {
  message: Message | null;
  showMessage: (text: string, type: "error" | "success") => void;
  clearMessage: () => void;
}

const MessageContext = createContext<MessageContextType | null>(null);

export function MessageProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<Message | null>(null);

  const showMessage = (text: string, type: "error" | "success") =>
    setMessage({ text, type });

  const clearMessage = () => setMessage(null);

  return (
    <MessageContext.Provider value={{ message, showMessage, clearMessage }}>
      {children}
    </MessageContext.Provider>
  );
}

export function useMessageContext() {
  const ctx = useContext(MessageContext);
  if (!ctx) throw new Error("useMessageContext must be used within MessageProvider");
  return ctx;
}