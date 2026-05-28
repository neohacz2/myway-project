import { readFileSync, existsSync } from "fs";
import { join } from "path";

export interface DigestState {
  totalSources: number;
  sourcesAddedSinceBatch: number;
  lastPolledAt: string | null;
  lastBatchAt: string | null;
  recentVideos: { id: string; url: string }[];
}

export function formatKST(iso: string): string {
  const date = new Date(iso);
  // UTC+9
  const kst = new Date(date.getTime() + 9 * 60 * 60 * 1000);
  const y = kst.getUTCFullYear();
  const m = String(kst.getUTCMonth() + 1).padStart(2, "0");
  const d = String(kst.getUTCDate()).padStart(2, "0");
  const hh = String(kst.getUTCHours()).padStart(2, "0");
  const mm = String(kst.getUTCMinutes()).padStart(2, "0");
  return `${y}-${m}-${d} ${hh}:${mm}`;
}

export function readDigestState(statePath?: string): DigestState {
  const path =
    statePath ??
    process.env.STATE_PATH ??
    join(process.cwd(), "scripts/topic-digest/state.json");

  if (!existsSync(path)) {
    return {
      totalSources: 0,
      sourcesAddedSinceBatch: 0,
      lastPolledAt: null,
      lastBatchAt: null,
      recentVideos: [],
    };
  }

  const raw = JSON.parse(readFileSync(path, "utf-8"));
  const ids: string[] = raw.ingested_video_ids ?? [];
  const recent = ids
    .slice(-10)
    .reverse()
    .map((id) => ({ id, url: `https://www.youtube.com/watch?v=${id}` }));

  return {
    totalSources: ids.length,
    sourcesAddedSinceBatch: raw.sources_added_since_last_batch ?? 0,
    lastPolledAt: raw.last_polled_at ? formatKST(raw.last_polled_at) : null,
    lastBatchAt: raw.last_batch_at ? formatKST(raw.last_batch_at) : null,
    recentVideos: recent,
  };
}
