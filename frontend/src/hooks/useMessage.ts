import { useState } from "react";

export interface Message {
  text: string;
  type: "error" | "success";
}

export function useMessage() {
  const [message, setMessage] = useState<Message | null>(null);
  const clearMessage = () => setMessage(null);
  const showMessage = (text: string, type: "error" | "success") => setMessage({ text, type });
  return { message, setMessage, clearMessage, showMessage };
}