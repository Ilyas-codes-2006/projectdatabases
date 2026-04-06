import { useCallback, useEffect, useRef, useState } from "react";

export interface Message {
  text: string;
  type: "error" | "success";
}

export function useMessage() {
  const [message, setMessage] = useState<Message | null>(null);
  const timeoutRef = useRef<number | null>(null);

  const clearMessage = useCallback(() => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setMessage(null);
  }, []);

  const showMessage = useCallback((text: string, type: "error" | "success") => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
    }
    setMessage({ text, type });
    timeoutRef.current = window.setTimeout(() => {
      setMessage(null);
      timeoutRef.current = null;
    }, 5000);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return { message, setMessage, clearMessage, showMessage };
}