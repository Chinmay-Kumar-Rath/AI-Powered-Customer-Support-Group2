import React, { useEffect, useState } from "react";
import { api } from "../../api";
import AdminDashboard from "./AdminDashboard";

export default function AdminDashboardContainer() {
  const [stats, setStats] = useState(null);
  const [ragStats, setRagStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    Promise.allSettled([
      api.stats(),
      api.ragStats(),
      api.users({ limit: 500 }),
      api.tickets({ limit: 500 }),
    ]).then((results) => {
      if (!active) return;

      const [statsResult, ragResult, usersResult, ticketsResult] = results;

      if (statsResult.status === "fulfilled") setStats(statsResult.value);
      else setError(statsResult.reason?.message || "Could not load dashboard statistics.");

      if (ragResult.status === "fulfilled") setRagStats(ragResult.value);
      if (usersResult.status === "fulfilled") {
        setUsers(Array.isArray(usersResult.value) ? usersResult.value : []);
      }
      if (ticketsResult.status === "fulfilled") {
        setTickets(Array.isArray(ticketsResult.value) ? ticketsResult.value : []);
      }
    }).finally(() => {
      if (active) setLoading(false);
    });

    return () => { active = false; };
  }, []);

  return (
    <AdminDashboard
      stats={stats}
      ragStats={ragStats}
      users={users}
      tickets={tickets}
      loading={loading}
      error={error}
    />
  );
}

