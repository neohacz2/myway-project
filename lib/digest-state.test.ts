import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { writeFileSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { readDigestState, formatKST } from "./digest-state";

const TMP = join(process.cwd(), "test-tmp-state");

beforeEach(() => mkdirSync(TMP, { recursive: true }));
afterEach(() => rmSync(TMP, { recursive: true, force: true }));

describe("readDigestState", () => {
  it("returns empty state when file does not exist", () => {
    const state = readDigestState(join(TMP, "nonexistent.json"));
    expect(state.totalSources).toBe(0);
    expect(state.sourcesAddedSinceBatch).toBe(0);
    expect(state.lastPolledAt).toBeNull();
    expect(state.lastBatchAt).toBeNull();
    expect(state.recentVideos).toEqual([]);
  });

  it("maps ingested_video_ids length to totalSources", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({ ingested_video_ids: ["a", "b", "c"] }));
    expect(readDigestState(p).totalSources).toBe(3);
  });

  it("maps sources_added_since_last_batch", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({ sources_added_since_last_batch: 5 }));
    expect(readDigestState(p).sourcesAddedSinceBatch).toBe(5);
  });

  it("returns at most 10 recent videos in reverse order", () => {
    const ids = Array.from({ length: 15 }, (_, i) => `vid${i}`);
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({ ingested_video_ids: ids }));
    const { recentVideos } = readDigestState(p);
    expect(recentVideos).toHaveLength(10);
    // most-recent-first: last 10 ids reversed
    expect(recentVideos[0].id).toBe("vid14");
    expect(recentVideos[9].id).toBe("vid5");
  });

  it("builds correct youtube URL for each video", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({ ingested_video_ids: ["ABC123"] }));
    const { recentVideos } = readDigestState(p);
    expect(recentVideos[0].url).toBe("https://www.youtube.com/watch?v=ABC123");
  });

  it("converts last_polled_at UTC ISO to KST formatted string", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({ last_polled_at: "2026-05-28T00:00:00+00:00" }));
    expect(readDigestState(p).lastPolledAt).toBe("2026-05-28 09:00");
  });

  it("converts last_batch_at UTC ISO to KST formatted string", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({ last_batch_at: "2026-05-23T00:00:00+00:00" }));
    expect(readDigestState(p).lastBatchAt).toBe("2026-05-23 09:00");
  });

  it("returns null timestamps when fields absent", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, JSON.stringify({}));
    const state = readDigestState(p);
    expect(state.lastPolledAt).toBeNull();
    expect(state.lastBatchAt).toBeNull();
  });

  it("returns empty state when state.json is malformed", () => {
    const p = join(TMP, "state.json");
    writeFileSync(p, "not valid json{{{");
    const state = readDigestState(p);
    expect(state.totalSources).toBe(0);
    expect(state.recentVideos).toEqual([]);
  });
});

describe("formatKST", () => {
  it("converts UTC midnight to 09:00 KST", () => {
    expect(formatKST("2026-05-28T00:00:00+00:00")).toBe("2026-05-28 09:00");
  });
});
