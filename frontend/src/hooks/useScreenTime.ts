import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { HeartbeatResponse } from "../lib/types";

const HEARTBEAT_INTERVAL_MS = 60 * 1000;   // 60 seconds

export function useScreenTime() {
  const [todayMinutes, setTodayMinutes] = useState(0);
  const [limitMinutes, setLimitMinutes] = useState(60);
  const [limitReached, setLimitReached] = useState(false);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<number | null>(null);

  async function sendHeartbeat() {
    try {
      const res = await api.post<HeartbeatResponse>("/api/v1/screen-time/heartbeat");
      setTodayMinutes(Math.floor(res.today_total_seconds / 60));
      setLimitMinutes(Math.floor(res.limit_seconds / 60));
      setLimitReached(res.limit_reached);
    } catch {
      // silent — heartbeat failures shouldn't crash the UI
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Initial heartbeat on mount
    sendHeartbeat();

    // Then every 60s while the tab is visible
    intervalRef.current = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        sendHeartbeat();
      }
    }, HEARTBEAT_INTERVAL_MS);

    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
    };
  }, []);

  return { todayMinutes, limitMinutes, limitReached, loading, sendHeartbeat };
}