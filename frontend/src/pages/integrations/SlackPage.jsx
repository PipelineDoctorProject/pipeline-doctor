import { useCallback, useEffect, useMemo, useState } from "react";
import { Link2, MessageSquareShare, RefreshCw, Workflow, Unplug } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";

import {
  disconnectSlack,
  getSlackChannels,
  getSlackConnectUrl,
  getSlackStatus,
  saveSlackDefaultChannel,
} from "../../api/slack";

export default function SlackPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [status, setStatus] = useState(null);
  const [channels, setChannels] = useState([]);
  const [selectedChannelId, setSelectedChannelId] = useState("");
  const [loading, setLoading] = useState(true);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const message = searchParams.get("message");
  const connected = searchParams.get("connected");

  const loadStatus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getSlackStatus();
      setStatus(data);
      setSelectedChannelId(data?.default_channel?.slack_channel_id || "");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load Slack status.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadChannels = useCallback(async () => {
    try {
      setChannelsLoading(true);
      const data = await getSlackChannels();
      setChannels(data.channels || []);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load Slack channels.");
    } finally {
      setChannelsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    if (!message) return;

    if (connected === "1") {
      toast.success(message);
    } else {
      toast.error(message);
    }

    const next = new URLSearchParams(searchParams);
    next.delete("connected");
    next.delete("message");
    setSearchParams(next, { replace: true });
  }, [connected, message, searchParams, setSearchParams]);

  useEffect(() => {
    if (!status?.connected || !status?.can_manage) return;
    loadChannels();
  }, [loadChannels, status?.can_manage, status?.connected]);

  const selectedChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannelId),
    [channels, selectedChannelId],
  );

  async function handleConnect() {
    try {
      const data = await getSlackConnectUrl();
      window.location.href = data.connect_url;
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to start Slack connection.");
    }
  }

  async function handleSaveChannel() {
    if (!selectedChannel) {
      toast.error("Choose a Slack channel first.");
      return;
    }

    try {
      setSaving(true);
      await saveSlackDefaultChannel(selectedChannel.id, selectedChannel.name);
      toast.success("Default Slack channel saved.");
      await loadStatus();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to save Slack channel.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDisconnect() {
    try {
      await disconnectSlack();
      toast.success("Slack disconnected.");
      setChannels([]);
      await loadStatus();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to disconnect Slack.");
    }
  }

  return (
    <div className="space-y-5">
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-4 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-[30px] font-semibold leading-tight text-slate-950">
              Slack Integration
            </h1>
            <p className="mt-2 max-w-[760px] text-[14px] leading-6 text-slate-500">
              Connect one Slack workspace per tenant, then choose the default channel for incident notifications.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadStatus}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              <RefreshCw size={15} />
              Refresh
            </button>
            {status?.can_manage ? (
              <button
                onClick={handleConnect}
                className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
              >
                <Link2 size={15} />
                {status?.connected ? "Reconnect Slack" : "Connect Slack"}
              </button>
            ) : null}
          </div>
        </div>
      </section>

      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center text-[14px] text-slate-500 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          Loading Slack integration...
        </div>
      ) : (
        <>
          <section className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
              <div className="mb-5 flex items-start gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-700">
                  <Workflow size={20} />
                </div>
                <div>
                  <h2 className="text-[18px] font-semibold text-slate-950">Workspace Connection</h2>
                  <p className="mt-1 text-[13px] leading-6 text-slate-500">
                    Slack verifies the installer, validates workspace permissions, and returns a permanent `team.id` plus bot token for this tenant.
                  </p>
                </div>
              </div>

              {!status?.connected ? (
                <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 p-5">
                  <p className="text-[14px] text-slate-700">No Slack workspace is connected yet.</p>
                  <p className="mt-2 text-[13px] text-slate-500">
                    Connect Slack as a workspace admin or owner, approve the requested bot scopes, then return here to select a channel.
                  </p>
                </div>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500">Workspace Name</p>
                    <p className="mt-2 text-[15px] font-semibold text-slate-950">
                      {status.workspace?.slack_team_name}
                    </p>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500">Workspace ID</p>
                    <p className="mt-2 font-mono text-[15px] font-semibold text-slate-950">
                      {status.workspace?.slack_team_id}
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
              <div className="mb-5 flex items-start gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-700">
                  <MessageSquareShare size={20} />
                </div>
                <div>
                  <h2 className="text-[18px] font-semibold text-slate-950">Default Channel</h2>
                  <p className="mt-1 text-[13px] leading-6 text-slate-500">
                    Incidents are delivered to the default Slack channel saved for this tenant.
                  </p>
                </div>
              </div>

              {status?.connected ? (
                <>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500">Current Channel</p>
                    <p className="mt-2 text-[15px] font-semibold text-slate-950">
                      {status.default_channel?.slack_channel_name
                        ? `#${status.default_channel.slack_channel_name}`
                        : "No default channel selected"}
                    </p>
                  </div>

                  {status.can_manage ? (
                    <div className="mt-4 space-y-3">
                      <label className="block text-[12px] font-medium text-slate-500">
                        Select incident channel
                      </label>
                      <select
                        value={selectedChannelId}
                        onChange={(event) => setSelectedChannelId(event.target.value)}
                        className="h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-[14px] text-slate-800 outline-none"
                        disabled={channelsLoading}
                      >
                        <option value="">Choose a channel</option>
                        {channels.map((channel) => (
                          <option key={channel.id} value={channel.id}>
                            #{channel.name}{channel.is_private ? " (private)" : ""}
                          </option>
                        ))}
                      </select>

                      <div className="flex flex-wrap gap-3">
                        <button
                          onClick={handleSaveChannel}
                          disabled={saving || !selectedChannelId}
                          className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
                        >
                          Save Channel
                        </button>
                        <button
                          onClick={handleDisconnect}
                          className="inline-flex h-10 items-center gap-2 rounded-md border border-rose-200 bg-rose-50 px-4 text-[13px] font-semibold text-rose-700 transition hover:bg-rose-100"
                        >
                          <Unplug size={15} />
                          Disconnect
                        </button>
                      </div>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="text-[14px] text-slate-500">
                  Connect Slack first to fetch available channels.
                </p>
              )}
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
            <h2 className="text-[18px] font-semibold text-slate-950">How it works</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              {[
                "Admin starts OAuth from this page.",
                "Slack authenticates the installer and chosen workspace.",
                "OpsSight stores Slack team ID plus bot token for this tenant.",
                "New incidents post to the saved default channel.",
              ].map((item, index) => (
                <div key={item} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                  <div className="mb-3 flex h-7 w-7 items-center justify-center rounded-md bg-white text-[12px] font-semibold text-slate-700 shadow-sm">
                    {index + 1}
                  </div>
                  <p className="text-[13px] leading-6 text-slate-700">{item}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
