import { useEffect, useRef } from "react";

import { useUiStore } from "@/stores/ui-store";

const EVENTS = ["mousemove", "keydown", "click", "scroll", "touchstart"] as const;

interface Options {
  timeoutMs?: number;
  onTimeout: () => void;
}

export function useIdleTimer({ timeoutMs = 60_000, onTimeout }: Options): void {
  const idleModalOpen = useUiStore((s) => s.idleModalOpen);
  const onTimeoutRef = useRef(onTimeout);
  onTimeoutRef.current = onTimeout;

  useEffect(() => {
    if (idleModalOpen) {
      return;
    }

    let timer = window.setTimeout(() => onTimeoutRef.current(), timeoutMs);

    const reset = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => onTimeoutRef.current(), timeoutMs);
    };

    EVENTS.forEach((event) =>
      window.addEventListener(event, reset, { passive: true }),
    );

    return () => {
      window.clearTimeout(timer);
      EVENTS.forEach((event) => window.removeEventListener(event, reset));
    };
  }, [idleModalOpen, timeoutMs]);
}
