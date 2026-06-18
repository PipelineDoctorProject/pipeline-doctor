// components/layout/Topbar.jsx

import {
  AlertTriangle,
  Bell,
  Brain,
  CheckCircle2,
  ChevronDown,
  Mail,
  MessageSquare,
  Search,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSlackStatus } from "../../api/slack";
import useDashboard from "../../hooks/useDashboard";
import useIncidentsWebSocket from "../../hooks/useIncidentsWebSocket";
import { getIncidents } from "../../store/incidentStore";
import { getModels } from "../../store/modelStore";
import useSelectedModelStore from "../../store/selectedModelStore";

const NOTIFICATION_LIMIT = 8;
const POLL_INTERVAL_MS = 5000;

function isResolved(status) {
  return ["resolved", "closed", "deployed", "promoted"].includes(
    String(status || "").toLowerCase(),
  );
}

function formatNotificationTime(value) {
  if (!value) return "Just now";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Just now";

  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function severityClasses(severity) {
  const normalized = String(severity || "").toLowerCase();

  if (normalized === "critical") {
    return "border-red-200 bg-red-50 text-red-700";
  }

  if (normalized === "high") {
    return "border-orange-200 bg-orange-50 text-orange-700";
  }

  if (normalized === "medium") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }

  return "border-blue-200 bg-blue-50 text-blue-700";
}

export default function Topbar() {
  const navigate = useNavigate();
  const { dashboardData } = useDashboard();
  const [models, setModels] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [slackStatus, setSlackStatus] = useState(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [readNotificationIds, setReadNotificationIds] = useState(() => new Set());
  const notificationRef = useRef(null);
  const {
    isLive: incidentsFeedLive,
    lastMessage: lastIncidentMessage,
    connect: connectIncidentsFeed,
    disconnect: disconnectIncidentsFeed,
  } = useIncidentsWebSocket();
  const selectedModelId = useSelectedModelStore((state) => state.selectedModelId);
  const setSelectedModelId = useSelectedModelStore((state) => state.setSelectedModelId);
  const hydrateSelectionScope = useSelectedModelStore(
    (state) => state.hydrateSelectionScope,
  );

  const user = dashboardData?.user;
  const workspace = dashboardData?.workspace;
  const selectedModel = useMemo(
    () => models.find((model) => String(model.id) === String(selectedModelId)),
    [models, selectedModelId],
  );
  const notificationStorageKey = useMemo(() => {
    if (!workspace?.tenant_id || !user?.id) return null;
    return `opssight:read-incident-notifications:${workspace.tenant_id}:${user.id}`;
  }, [workspace?.tenant_id, user?.id]);

  const incidentNotifications = useMemo(
    () =>
      [...incidents]
        .sort((first, second) => {
          const firstTime = new Date(first.created_at || 0).getTime();
          const secondTime = new Date(second.created_at || 0).getTime();
          return secondTime - firstTime;
        })
        .slice(0, NOTIFICATION_LIMIT)
        .map((incident) => {
          const notificationId = `incident:${incident.group_id || incident.id}`;
          const title =
            incident.group_title ||
            incident.title ||
            `Incident on run #${incident.run_id || "unknown"}`;
          const summary =
            incident.group_summary ||
            incident.description ||
            incident.guidance?.cause ||
            "A monitoring signal crossed the incident threshold.";

          return {
            ...incident,
            notificationId,
            title,
            summary,
          };
        }),
    [incidents],
  );

  const unreadCount = useMemo(
    () =>
      incidentNotifications.filter(
        (incident) =>
          !isResolved(incident.status) &&
          !readNotificationIds.has(incident.notificationId),
      ).length,
    [incidentNotifications, readNotificationIds],
  );

  const slackDeliveryLabel = slackStatus?.default_channel?.slack_channel_name
    ? `Slack #${slackStatus.default_channel.slack_channel_name}`
    : slackStatus?.connected
      ? "Slack channel not selected"
      : "Slack not connected";

  const persistReadNotifications = useCallback(
    (nextReadSet) => {
      setReadNotificationIds(nextReadSet);

      if (!notificationStorageKey) return;

      window.localStorage.setItem(
        notificationStorageKey,
        JSON.stringify([...nextReadSet]),
      );
    },
    [notificationStorageKey],
  );

  const markAllNotificationsRead = useCallback(() => {
    const nextReadSet = new Set(readNotificationIds);
    incidentNotifications.forEach((incident) => {
      nextReadSet.add(incident.notificationId);
    });
    persistReadNotifications(nextReadSet);
  }, [incidentNotifications, persistReadNotifications, readNotificationIds]);

  const loadNotificationData = useCallback(async () => {
    try {
      const [incidentData, nextSlackStatus] = await Promise.all([
        getIncidents(selectedModelId),
        getSlackStatus().catch(() => null),
      ]);

      setIncidents(Array.isArray(incidentData) ? incidentData : []);
      setSlackStatus(nextSlackStatus);
    } catch (error) {
      console.log(error);
    }
  }, [selectedModelId]);

  useEffect(() => {
    const scope = workspace?.tenant_id
      ? `${workspace.tenant_id}:${user?.id || "anonymous"}`
      : null;
    hydrateSelectionScope(scope);
  }, [workspace?.tenant_id, user?.id, hydrateSelectionScope]);

  useEffect(() => {
    let isMounted = true;

    getModels()
      .then((data) => {
        if (!isMounted) return;
        const nextModels = data || [];
        setModels(nextModels);

        if (
          selectedModelId !== "all" &&
          !nextModels.some((model) => String(model.id) === String(selectedModelId))
        ) {
          setSelectedModelId("all");
        }
      })
      .catch((error) => console.log(error));

    return () => {
      isMounted = false;
    };
  }, [selectedModelId, setSelectedModelId]);

  useEffect(() => {
    if (!notificationStorageKey) {
      setReadNotificationIds(new Set());
      return;
    }

    try {
      const stored = JSON.parse(
        window.localStorage.getItem(notificationStorageKey) || "[]",
      );
      setReadNotificationIds(new Set(Array.isArray(stored) ? stored : []));
    } catch {
      setReadNotificationIds(new Set());
    }
  }, [notificationStorageKey]);

  useEffect(() => {
    loadNotificationData();
    const intervalId = window.setInterval(loadNotificationData, POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [loadNotificationData]);

  useEffect(() => {
    connectIncidentsFeed();
    return () => disconnectIncidentsFeed();
  }, [connectIncidentsFeed, disconnectIncidentsFeed]);

  useEffect(() => {
    if (!lastIncidentMessage) return;
    if (!["incident_created", "incident_updated"].includes(lastIncidentMessage.event)) {
      return;
    }

    loadNotificationData();
  }, [lastIncidentMessage, loadNotificationData]);

  useEffect(() => {
    if (!notificationsOpen) return;

    const handleOutsideClick = (event) => {
      if (!notificationRef.current?.contains(event.target)) {
        setNotificationsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [notificationsOpen]);
  
  return (
    <header className="flex h-[80px] items-center justify-between border-b border-black/[0.05] bg-white/80 px-8 backdrop-blur-xl">
      {/* LEFT */}
      <div></div>

      {/* RIGHT */}
      <div className="flex items-center gap-4">
        <label className="flex h-[46px] min-w-[260px] items-center gap-3 rounded-2xl border border-black/[0.05] bg-[#f7f8fb] px-4 text-[13px] text-gray-500">
          <Brain size={16} className="shrink-0 text-gray-400" />
          <select
            value={selectedModelId}
            onChange={(event) => setSelectedModelId(event.target.value)}
            className="h-full min-w-0 flex-1 bg-transparent text-[14px] font-medium text-[#111827] outline-none"
            title="Select model context"
          >
            <option value="all">All models</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name || model.mlflow_model_name || `Model ${model.id}`} v{model.version || "-"}
              </option>
            ))}
          </select>
        </label>

        {/* SEARCH */}
        <div className="relative">
          <Search
            size={16}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
          />

          <input
            type="text"
            placeholder="Search..."
            className="h-[46px] w-[260px] rounded-2xl border border-black/[0.05] bg-[#f7f8fb] pl-11 pr-4 text-[14px] text-[#111827] outline-none placeholder:text-gray-400 focus:border-[#3563ff]/30"
          />
        </div>

        {/* NOTIFICATIONS */}
        <div ref={notificationRef} className="relative">
          <button
            type="button"
            onClick={() => setNotificationsOpen((isOpen) => !isOpen)}
            className="relative flex h-[46px] w-[46px] items-center justify-center rounded-2xl border border-black/[0.05] bg-[#f7f8fb] text-gray-500 transition hover:text-[#111827]"
            aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}
          >
            <Bell size={18} />

            {unreadCount > 0 ? (
              <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white shadow-sm">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            ) : (
              <span className="absolute right-3 top-3 h-2 w-2 rounded-full bg-emerald-400" />
            )}
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 z-50 mt-3 w-[390px] overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_24px_70px_rgba(15,23,42,0.18)]">
              <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[14px] font-bold text-slate-950">Notifications</p>
                    <p className="mt-1 text-[12px] text-slate-500">
                      {incidentsFeedLive ? "Live incident feed connected" : "Refreshing periodically"}
                    </p>
                  </div>

                  {incidentNotifications.length > 0 && (
                    <button
                      type="button"
                      onClick={markAllNotificationsRead}
                      className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-semibold text-slate-600 transition hover:border-blue-200 hover:text-blue-600"
                    >
                      Mark read
                    </button>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 ring-1 ring-slate-200">
                    <Mail size={12} />
                    Email enabled
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 ring-1 ring-slate-200">
                    <MessageSquare size={12} />
                    {slackDeliveryLabel}
                  </span>
                </div>
              </div>

              <div className="max-h-[420px] overflow-y-auto p-3">
                {incidentNotifications.length === 0 ? (
                  <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center">
                    <CheckCircle2 size={24} className="text-emerald-500" />
                    <p className="mt-3 text-[13px] font-semibold text-slate-900">
                      No incident notifications
                    </p>
                    <p className="mt-1 text-[12px] leading-5 text-slate-500">
                      New incidents will appear here with email and Slack delivery status.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {incidentNotifications.map((incident) => {
                      const unread = !readNotificationIds.has(incident.notificationId);

                      return (
                        <button
                          key={incident.notificationId}
                          type="button"
                          onClick={() => {
                            const nextReadSet = new Set(readNotificationIds);
                            nextReadSet.add(incident.notificationId);
                            persistReadNotifications(nextReadSet);
                            setNotificationsOpen(false);
                            navigate("/incidents");
                          }}
                          className="w-full rounded-2xl border border-slate-100 bg-white p-3 text-left transition hover:border-blue-200 hover:bg-blue-50/40"
                        >
                          <div className="flex items-start gap-3">
                            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                              <AlertTriangle size={16} />
                            </div>

                            <div className="min-w-0 flex-1">
                              <div className="flex items-center justify-between gap-2">
                                <p className="truncate text-[13px] font-bold text-slate-950">
                                  {incident.title}
                                </p>
                                {unread && (
                                  <span className="h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                                )}
                              </div>

                              <p className="mt-1 max-h-10 overflow-hidden text-[12px] leading-5 text-slate-500">
                                {incident.summary}
                              </p>

                              <div className="mt-3 flex flex-wrap items-center gap-2">
                                <span
                                  className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${severityClasses(
                                    incident.severity,
                                  )}`}
                                >
                                  {incident.severity || "Incident"}
                                </span>
                                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                                  Run #{incident.run_id || "-"}
                                </span>
                                <span className="text-[10px] font-medium text-slate-400">
                                  {formatNotificationTime(incident.created_at)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="border-t border-slate-100 bg-slate-50/80 p-3">
                <button
                  type="button"
                  onClick={() => {
                    setNotificationsOpen(false);
                    navigate("/incidents");
                  }}
                  className="flex w-full items-center justify-center rounded-2xl bg-[#0b2a4a] px-4 py-2.5 text-[12px] font-bold text-white transition hover:bg-[#13385f]"
                >
                  View all incidents
                </button>
              </div>
            </div>
          )}
        </div>

        {/* PROFILE */}
        <button className="flex items-center gap-3 rounded-2xl border border-black/[0.05] bg-[#f7f8fb] px-4 py-2 transition hover:bg-white">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#3563ff] text-[13px] font-semibold text-white">
            S
          </div>

          <div className="text-left">
            <p className="text-[13px] font-medium text-[#111827]">{workspace?.workspace_name}</p>

            <p className="max-w-[140px] truncate text-[11px] text-gray-500">
              {selectedModel ? selectedModel.name : "All models"}
            </p>
          </div>

          <ChevronDown size={16} className="text-gray-400" />
        </button>
      </div>
    </header>
  );
}
