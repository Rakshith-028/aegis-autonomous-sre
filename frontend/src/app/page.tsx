"use client";

import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  CircleDot,
  Clock3,
  Flame,
  Gauge,
  HeartPulse,
  Network,
  Play,
  RefreshCw,
  RotateCcw,
  ServerCog,
  ShieldCheck,
  Siren,
  SquareTerminal,
  Zap,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  getIncidents,
  getPostmortems,
  getSystemStatus,
  injectChaos,
  Incident,
  Postmortem,
  RCA,
  runAutonomousCycle,
  SystemStatus,
  WS_URL,
} from "@/lib/api";


type HistoryPoint = {
  time: string;
  latency: number;
  error: number;
  rps: number;
};


type FeedEntry = {
  id: string;
  time: string;
  message: string;
  type:
    | "info"
    | "success"
    | "warning"
    | "danger";
};


const chaosActions = [
  {
    mode: "latency",
    label: "Latency",
    description: "Inject slow request processing",
    icon: Clock3,
  },
  {
    mode: "errors",
    label: "Errors",
    description: "Generate HTTP 500 failures",
    icon: Flame,
  },
  {
    mode: "health-error",
    label: "Health Failure",
    description: "Break service health endpoint",
    icon: Siren,
  },
  {
    mode: "health-slow",
    label: "Service Hang",
    description: "Simulate health timeout",
    icon: AlertTriangle,
  },
];


function cn(
  ...classes: Array<string | false | null | undefined>
) {
  return classes.filter(Boolean).join(" ");
}


function formatNumber(
  value: number | null | undefined,
  digits = 2,
) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(value)
  ) {
    return "--";
  }

  return value.toFixed(digits);
}


function severityClasses(severity: string) {
  switch (severity.toUpperCase()) {
    case "CRITICAL":
      return "border-red-400/25 bg-red-400/10 text-red-300";

    case "HIGH":
      return "border-orange-400/25 bg-orange-400/10 text-orange-300";

    case "MEDIUM":
      return "border-yellow-400/25 bg-yellow-400/10 text-yellow-300";

    case "LOW":
      return "border-sky-400/25 bg-sky-400/10 text-sky-300";

    case "NORMAL":
      return "border-emerald-400/25 bg-emerald-400/10 text-emerald-300";

    default:
      return "border-slate-400/20 bg-slate-400/10 text-slate-300";
  }
}


function MetricCard({
  title,
  value,
  suffix,
  detail,
  icon: Icon,
  tone,
}: {
  title: string;
  value: string;
  suffix?: string;
  detail: string;
  icon: React.ElementType;
  tone:
    | "cyan"
    | "green"
    | "yellow"
    | "red"
    | "purple";
}) {
  const tones = {
    cyan: {
      text: "text-cyan-300",
      box: "bg-cyan-400/10 border-cyan-400/15",
    },
    green: {
      text: "text-emerald-300",
      box: "bg-emerald-400/10 border-emerald-400/15",
    },
    yellow: {
      text: "text-yellow-300",
      box: "bg-yellow-400/10 border-yellow-400/15",
    },
    red: {
      text: "text-red-300",
      box: "bg-red-400/10 border-red-400/15",
    },
    purple: {
      text: "text-violet-300",
      box: "bg-violet-400/10 border-violet-400/15",
    },
  };

  const styles = tones[tone];

  return (
    <div
      className={cn(
        "glass metric-glow rounded-2xl p-5",
        styles.text,
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
            {title}
          </p>

          <div className="mt-3 flex items-end gap-1.5">
            <span className="text-3xl font-semibold tracking-tight text-slate-100">
              {value}
            </span>

            {suffix && (
              <span className="mb-1 text-sm text-slate-500">
                {suffix}
              </span>
            )}
          </div>
        </div>

        <div
          className={cn(
            "rounded-xl border p-2.5",
            styles.box,
          )}
        >
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        {detail}
      </p>
    </div>
  );
}


export default function Home() {
  const [status, setStatus] =
    useState<SystemStatus | null>(null);

  const [incidents, setIncidents] =
    useState<Incident[]>([]);

  const [postmortems, setPostmortems] =
    useState<Postmortem[]>([]);

  const [history, setHistory] =
    useState<HistoryPoint[]>([]);

  const [feed, setFeed] =
    useState<FeedEntry[]>([]);

  const [connected, setConnected] =
    useState(false);

  const [loading, setLoading] =
    useState(true);

  const [cycleRunning, setCycleRunning] =
    useState(false);

  const [chaosRunning, setChaosRunning] =
    useState<string | null>(null);

  const socketRef =
    useRef<WebSocket | null>(null);

  const addFeed = useCallback(
    (
      message: string,
      type: FeedEntry["type"] = "info",
    ) => {
      const now = new Date();

      setFeed((current) => [
        {
          id: `${now.getTime()}-${Math.random()}`,
          time: now.toLocaleTimeString(),
          message,
          type,
        },
        ...current,
      ].slice(0, 20));
    },
    [],
  );


  const refreshSideData = useCallback(
    async () => {
      try {
        const [
          incidentData,
          postmortemData,
        ] = await Promise.all([
          getIncidents(),
          getPostmortems(),
        ]);

        setIncidents(incidentData);
        setPostmortems(postmortemData);
      } catch {
        addFeed(
          "Unable to refresh incident history.",
          "warning",
        );
      }
    },
    [addFeed],
  );


  const applyLiveStatus = useCallback(
    (nextStatus: SystemStatus) => {
      setStatus(nextStatus);

      const latency =
        nextStatus.evidence.metrics.latency.value ??
        0;

      const errorRate =
        nextStatus.evidence.metrics.error_rate.value ??
        0;

      const rps =
        nextStatus.evidence.metrics.request_rate.value ??
        0;

      setHistory((current) => [
        ...current,
        {
          time: new Date().toLocaleTimeString(
            [],
            {
              minute: "2-digit",
              second: "2-digit",
            },
          ),
          latency: latency * 1000,
          error: errorRate * 100,
          rps,
        },
      ].slice(-30));
    },
    [],
  );


  useEffect(() => {
    async function initialLoad() {
      try {
        const [
          initialStatus,
          initialIncidents,
          initialPostmortems,
        ] = await Promise.all([
          getSystemStatus(),
          getIncidents(),
          getPostmortems(),
        ]);

        applyLiveStatus(initialStatus);
        setIncidents(initialIncidents);
        setPostmortems(initialPostmortems);

        addFeed(
          "Control plane synchronized.",
          "success",
        );
      } catch {
        addFeed(
          "AEGIS API is currently unreachable.",
          "danger",
        );
      } finally {
        setLoading(false);
      }
    }

    initialLoad();
  }, [addFeed, applyLiveStatus]);


  useEffect(() => {
    let reconnectTimer:
      | ReturnType<typeof setTimeout>
      | undefined;

    let intentionalClose = false;

    function connect() {
      const socket = new WebSocket(WS_URL);

      socketRef.current = socket;

      socket.onopen = () => {
        setConnected(true);

        addFeed(
          "Live telemetry channel connected.",
          "success",
        );
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(
            event.data,
          );

          if (
            payload.type === "SYSTEM_UPDATE"
          ) {
            applyLiveStatus({
              system: "AEGIS",
              service: payload.service,
              evidence: payload.evidence,
              rca: payload.rca,
              active_incidents:
                payload.active_incidents ?? [],
            });
          }
        } catch {
          addFeed(
            "Malformed live telemetry payload.",
            "warning",
          );
        }
      };

      socket.onerror = () => {
        setConnected(false);
      };

      socket.onclose = () => {
        setConnected(false);

        if (!intentionalClose) {
          reconnectTimer = setTimeout(
            connect,
            2000,
          );
        }
      };
    }

    connect();

    return () => {
      intentionalClose = true;

      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }

      socketRef.current?.close();
    };
  }, [
    addFeed,
    applyLiveStatus,
  ]);


  const rca: RCA | null =
    status?.rca ?? null;

  const evidence =
    status?.evidence ?? null;

  const requestRate =
    evidence?.metrics.request_rate.value ?? 0;

  const errorRate =
    evidence?.metrics.error_rate.value ?? 0;

  const latency =
    evidence?.metrics.latency.value ?? 0;

  const healthy =
    Boolean(
      evidence?.health.reachable &&
      evidence?.health.status_code === 200 &&
      rca?.root_cause ===
        "NO_ACTIVE_FAILURE",
    );

  const activeIncidentCount =
    status?.active_incidents.length ?? 0;


  const confidencePercent =
    Math.round(
      (rca?.confidence ?? 0) * 100,
    );


  const latestLogs = useMemo(
    () =>
      evidence?.logs
        ?.slice(-8)
        .reverse() ?? [],
    [evidence],
  );


  async function handleRunCycle() {
    setCycleRunning(true);

    addFeed(
      "Autonomous SRE cycle initiated.",
      "info",
    );

    try {
      const result =
        await runAutonomousCycle();

      const cycleStatus =
        String(
          result.status ?? "COMPLETE",
        );

      if (
        cycleStatus === "RECOVERED" ||
        cycleStatus === "HEALTHY"
      ) {
        addFeed(
          `Autonomous cycle finished: ${cycleStatus}.`,
          "success",
        );
      } else {
        addFeed(
          `Autonomous cycle finished: ${cycleStatus}.`,
          "warning",
        );
      }

      const fresh =
        await getSystemStatus();

      applyLiveStatus(fresh);

      await refreshSideData();
    } catch (error) {
      addFeed(
        error instanceof Error
          ? error.message
          : "Autonomous cycle failed.",
        "danger",
      );
    } finally {
      setCycleRunning(false);
    }
  }


  async function handleChaos(
    mode: string,
  ) {
    setChaosRunning(mode);

    addFeed(
      `Chaos injection requested: ${mode}.`,
      "warning",
    );

    try {
      await injectChaos(mode);

      addFeed(
        `Chaos active: ${mode}.`,
        "warning",
      );
    } catch (error) {
      addFeed(
        error instanceof Error
          ? error.message
          : "Chaos injection failed.",
        "danger",
      );
    } finally {
      setChaosRunning(null);
    }
  }


  async function handleReset() {
    setChaosRunning("reset");

    try {
      await injectChaos("reset");

      addFeed(
        "Chaos environment reset.",
        "success",
      );

      const fresh =
        await getSystemStatus();

      applyLiveStatus(fresh);
    } catch {
      addFeed(
        "Chaos reset failed.",
        "danger",
      );
    } finally {
      setChaosRunning(null);
    }
  }


  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-[1700px]">

        <header className="glass mb-5 flex flex-col gap-5 rounded-2xl px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="relative flex h-11 w-11 items-center justify-center rounded-xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-300">
              <ShieldCheck className="h-6 w-6" />

              <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-cyan-300" />
            </div>

            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-lg font-semibold tracking-[0.22em] text-slate-100">
                  AEGIS
                </h1>

                <span className="rounded border border-slate-700 bg-slate-900/80 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-slate-500">
                  CONTROL PLANE
                </span>
              </div>

              <p className="mt-1 text-xs text-slate-500">
                Autonomous SRE orchestration and self-healing infrastructure
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-black/20 px-3 py-2">
              <span
                className={cn(
                  "status-pulse h-1.5 w-1.5 rounded-full",
                  connected
                    ? "bg-emerald-400"
                    : "bg-red-400",
                )}
              />

              <span className="text-xs text-slate-400">
                {connected
                  ? "Live telemetry"
                  : "Reconnecting"}
              </span>
            </div>

            <button
              onClick={handleRunCycle}
              disabled={cycleRunning}
              className="flex items-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-300/15 disabled:cursor-wait disabled:opacity-50"
            >
              {cycleRunning ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}

              {cycleRunning
                ? "AEGIS reasoning..."
                : "Run autonomous cycle"}
            </button>
          </div>
        </header>


        <section className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <MetricCard
            title="Service State"
            value={
              loading
                ? "--"
                : healthy
                ? "Healthy"
                : "Degraded"
            }
            detail={
              healthy
                ? "Orders service operational"
                : "AEGIS attention required"
            }
            icon={HeartPulse}
            tone={
              healthy
                ? "green"
                : "red"
            }
          />

          <MetricCard
            title="Request Rate"
            value={formatNumber(
              requestRate,
              2,
            )}
            suffix="req/s"
            detail="Prometheus live throughput"
            icon={Activity}
            tone="cyan"
          />

          <MetricCard
            title="Error Rate"
            value={formatNumber(
              errorRate * 100,
              2,
            )}
            suffix="%"
            detail="HTTP 5xx traffic"
            icon={AlertTriangle}
            tone={
              errorRate >= 0.2
                ? "red"
                : "green"
            }
          />

          <MetricCard
            title="Latency"
            value={formatNumber(
              latency * 1000,
              0,
            )}
            suffix="ms"
            detail="Average request-path latency"
            icon={Gauge}
            tone={
              latency >= 1
                ? "yellow"
                : "purple"
            }
          />

          <MetricCard
            title="Active Incidents"
            value={String(
              activeIncidentCount,
            )}
            detail="Current unresolved failures"
            icon={Siren}
            tone={
              activeIncidentCount > 0
                ? "red"
                : "green"
            }
          />
        </section>


        <section className="grid grid-cols-1 gap-5 xl:grid-cols-[1.6fr_1fr]">

          <div className="space-y-5">

            <div className="glass scanline rounded-2xl p-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Live telemetry
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Application latency over the latest telemetry window
                  </p>
                </div>

                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <CircleDot className="h-3 w-3 text-cyan-300" />
                  Prometheus
                </div>
              </div>

              <div className="h-[260px]">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <AreaChart data={history}>
                    <defs>
                      <linearGradient
                        id="latencyFill"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#39d0ff"
                          stopOpacity={0.22}
                        />
                        <stop
                          offset="100%"
                          stopColor="#39d0ff"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>

                    <CartesianGrid
                      stroke="rgba(148,163,184,0.08)"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="time"
                      tick={{
                        fill: "#586475",
                        fontSize: 10,
                      }}
                      axisLine={false}
                      tickLine={false}
                    />

                    <YAxis
                      tick={{
                        fill: "#586475",
                        fontSize: 10,
                      }}
                      axisLine={false}
                      tickLine={false}
                      width={38}
                    />

                    <Tooltip
                      contentStyle={{
                        background:
                          "rgba(7,10,15,.96)",
                        border:
                          "1px solid rgba(148,163,184,.16)",
                        borderRadius: "12px",
                        fontSize: "12px",
                      }}
                      labelStyle={{
                        color: "#94a3b8",
                      }}
                    />

                    <Area
                      type="monotone"
                      dataKey="latency"
                      name="Latency ms"
                      stroke="#39d0ff"
                      fill="url(#latencyFill)"
                      strokeWidth={2}
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>


            <div className="glass rounded-2xl p-5">
              <div className="mb-5 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <BrainCircuit className="h-4 w-4 text-violet-300" />

                    <h2 className="text-sm font-semibold text-slate-200">
                      Root Cause Intelligence
                    </h2>
                  </div>

                  <p className="mt-1 text-xs text-slate-500">
                    Deterministic evidence-driven diagnosis
                  </p>
                </div>

                {rca && (
                  <span
                    className={cn(
                      "rounded-lg border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider",
                      severityClasses(
                        rca.severity,
                      ),
                    )}
                  >
                    {rca.severity}
                  </span>
                )}
              </div>

              <div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
                <div className="rounded-xl border border-slate-800/80 bg-black/15 p-4">
                  <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">
                    Current diagnosis
                  </p>

                  <h3 className="mt-3 break-words text-lg font-semibold text-slate-100">
                    {rca?.root_cause ??
                      "WAITING_FOR_TELEMETRY"}
                  </h3>

                  <div className="mt-5">
                    <div className="mb-2 flex items-center justify-between text-xs">
                      <span className="text-slate-500">
                        RCA confidence
                      </span>

                      <span className="font-medium text-cyan-300">
                        {confidencePercent}%
                      </span>
                    </div>

                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-900">
                      <div
                        className="h-full rounded-full bg-cyan-300 transition-all duration-500"
                        style={{
                          width:
                            `${confidencePercent}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="mt-5 border-t border-slate-800/80 pt-4">
                    <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">
                      Recommended action
                    </p>

                    <div className="mt-2 flex items-center gap-2 text-sm text-slate-300">
                      <Zap className="h-4 w-4 text-yellow-300" />

                      {rca?.recommended_action ??
                        "NONE"}
                    </div>
                  </div>
                </div>

                <div>
                  <p className="mb-3 text-[10px] uppercase tracking-[0.18em] text-slate-600">
                    Evidence chain
                  </p>

                  <div className="space-y-2">
                    {rca?.reasoning?.length ? (
                      rca.reasoning.map(
                        (reason, index) => (
                          <div
                            key={`${reason}-${index}`}
                            className="flex gap-3 rounded-xl border border-slate-800/70 bg-black/10 px-3 py-3"
                          >
                            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-cyan-400/20 bg-cyan-400/10 text-[9px] font-semibold text-cyan-300">
                              {index + 1}
                            </div>

                            <p className="text-xs leading-5 text-slate-400">
                              {reason}
                            </p>
                          </div>
                        ),
                      )
                    ) : (
                      <p className="text-xs text-slate-600">
                        No RCA evidence available yet.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>


            <div className="glass rounded-2xl p-5">
              <div className="mb-5 flex items-center gap-2">
                <Network className="h-4 w-4 text-cyan-300" />

                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Autonomous recovery pipeline
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Closed-loop SRE decision architecture
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 md:grid-cols-6">
                {[
                  ["01", "Observe"],
                  ["02", "Detect"],
                  ["03", "Diagnose"],
                  ["04", "Decide"],
                  ["05", "Heal"],
                  ["06", "Verify"],
                ].map(
                  ([number, label], index) => (
                    <div
                      key={label}
                      className="relative rounded-xl border border-slate-800 bg-black/15 px-3 py-4"
                    >
                      <span className="text-[9px] font-medium tracking-widest text-slate-700">
                        {number}
                      </span>

                      <p className="mt-2 text-xs font-medium text-slate-300">
                        {label}
                      </p>

                      {index < 5 && (
                        <span className="absolute -right-[7px] top-1/2 z-10 hidden h-px w-3 bg-cyan-400/30 md:block" />
                      )}
                    </div>
                  ),
                )}
              </div>
            </div>


            <div className="glass rounded-2xl p-5">
              <div className="mb-5 flex items-center gap-2">
                <SquareTerminal className="h-4 w-4 text-emerald-300" />

                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Runtime logs
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Latest service-level evidence
                  </p>
                </div>
              </div>

              <div className="max-h-[280px] overflow-auto rounded-xl border border-slate-800 bg-black/30 p-4 font-mono">
                {latestLogs.length > 0 ? (
                  latestLogs.map(
                    (line, index) => (
                      <div
                        key={`${line}-${index}`}
                        className="mb-2 flex gap-3 text-[11px] leading-5"
                      >
                        <span className="select-none text-slate-700">
                          {String(
                            index + 1,
                          ).padStart(2, "0")}
                        </span>

                        <span className="break-all text-slate-400">
                          {line}
                        </span>
                      </div>
                    ),
                  )
                ) : (
                  <p className="text-xs text-slate-600">
                    Waiting for runtime logs...
                  </p>
                )}
              </div>
            </div>
          </div>


          <aside className="space-y-5">

            <div className="glass rounded-2xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Chaos Laboratory
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Controlled failure injection
                  </p>
                </div>

                <Flame className="h-4 w-4 text-orange-300" />
              </div>

              <div className="space-y-2">
                {chaosActions.map(
                  ({
                    mode,
                    label,
                    description,
                    icon: Icon,
                  }) => (
                    <button
                      key={mode}
                      onClick={() =>
                        handleChaos(mode)
                      }
                      disabled={
                        chaosRunning !== null
                      }
                      className="group flex w-full items-center justify-between rounded-xl border border-slate-800 bg-black/15 px-3 py-3 text-left transition hover:border-orange-400/20 hover:bg-orange-400/[0.04] disabled:opacity-50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg border border-slate-800 bg-slate-900 p-2 text-slate-500 transition group-hover:text-orange-300">
                          <Icon className="h-4 w-4" />
                        </div>

                        <div>
                          <p className="text-xs font-medium text-slate-300">
                            {label}
                          </p>

                          <p className="mt-0.5 text-[10px] text-slate-600">
                            {description}
                          </p>
                        </div>
                      </div>

                      <Zap className="h-3.5 w-3.5 text-slate-700 group-hover:text-orange-300" />
                    </button>
                  ),
                )}

                <button
                  onClick={handleReset}
                  disabled={
                    chaosRunning !== null
                  }
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-400/15 bg-emerald-400/[0.05] px-3 py-2.5 text-xs font-medium text-emerald-300 transition hover:bg-emerald-400/10 disabled:opacity-50"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Reset environment
                </button>
              </div>
            </div>


            <div className="glass rounded-2xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Incident timeline
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Latest autonomous detections
                  </p>
                </div>

                <span className="text-[10px] text-slate-600">
                  {incidents.length} total
                </span>
              </div>

              <div className="max-h-[390px] space-y-3 overflow-auto pr-1">
                {incidents
                  .slice(0, 8)
                  .map((incident) => (
                    <div
                      key={incident.id}
                      className="relative border-l border-slate-800 pl-4"
                    >
                      <span
                        className={cn(
                          "absolute -left-[4.5px] top-1.5 h-2 w-2 rounded-full",
                          incident.status ===
                            "RESOLVED"
                            ? "bg-emerald-400"
                            : "bg-red-400",
                        )}
                      />

                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-medium text-slate-300">
                          {incident.failure_type}
                        </p>

                        <span
                          className={cn(
                            "rounded px-1.5 py-0.5 text-[8px] font-bold tracking-wider",
                            incident.status ===
                              "RESOLVED"
                              ? "bg-emerald-400/10 text-emerald-300"
                              : "bg-red-400/10 text-red-300",
                          )}
                        >
                          {incident.status}
                        </span>
                      </div>

                      <p className="mt-1 text-[10px] text-slate-600">
                        {incident.id}
                      </p>

                      <p className="mt-2 line-clamp-2 text-[10px] leading-4 text-slate-500">
                        {incident.reason}
                      </p>

                      <p className="mt-2 text-[9px] text-slate-700">
                        {new Date(
                          incident.started_at,
                        ).toLocaleString()}
                      </p>
                    </div>
                  ))}

                {incidents.length === 0 && (
                  <p className="text-xs text-slate-600">
                    No incidents recorded.
                  </p>
                )}
              </div>
            </div>


            <div className="glass rounded-2xl p-5">
              <div className="mb-4 flex items-center gap-2">
                <ServerCog className="h-4 w-4 text-violet-300" />

                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Autonomous action feed
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Live control-plane events
                  </p>
                </div>
              </div>

              <div className="max-h-[300px] space-y-2 overflow-auto">
                {feed.map((entry) => (
                  <div
                    key={entry.id}
                    className="flex gap-3 rounded-xl border border-slate-800/70 bg-black/10 px-3 py-2.5"
                  >
                    <span
                      className={cn(
                        "mt-1 h-1.5 w-1.5 shrink-0 rounded-full",
                        entry.type ===
                          "success"
                          ? "bg-emerald-400"
                          : entry.type ===
                            "warning"
                          ? "bg-yellow-400"
                          : entry.type ===
                            "danger"
                          ? "bg-red-400"
                          : "bg-cyan-400",
                      )}
                    />

                    <div className="min-w-0">
                      <p className="text-[10px] leading-4 text-slate-400">
                        {entry.message}
                      </p>

                      <p className="mt-1 text-[9px] text-slate-700">
                        {entry.time}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>


            <div className="glass rounded-2xl p-5">
              <div className="mb-4 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-300" />

                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Postmortems
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Verified recovery records
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                {postmortems
                  .slice(0, 4)
                  .map((item) => (
                    <div
                      key={item.incident_id}
                      className="rounded-xl border border-slate-800/80 bg-black/15 p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="truncate text-[11px] font-medium text-slate-300">
                          {
                            item
                              .root_cause_analysis
                              .root_cause
                          }
                        </p>

                        <span className="text-[9px] text-emerald-300">
                          VERIFIED
                        </span>
                      </div>

                      <p className="mt-2 text-[10px] leading-4 text-slate-600">
                        {item.summary}
                      </p>
                    </div>
                  ))}

                {postmortems.length === 0 && (
                  <p className="text-xs text-slate-600">
                    No postmortems generated yet.
                  </p>
                )}
              </div>
            </div>
          </aside>
        </section>


        <footer className="mt-5 flex flex-col gap-2 border-t border-slate-900 py-5 text-[10px] text-slate-700 sm:flex-row sm:items-center sm:justify-between">
          <span>
            AEGIS Autonomous SRE Control Plane
          </span>

          <span>
            Prometheus · Docker · FastAPI · Rule-based RCA · Policy Engine · Recovery Verification
          </span>
        </footer>
      </div>
    </main>
  );
}
