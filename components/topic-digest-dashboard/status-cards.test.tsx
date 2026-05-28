import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { StatusCards } from "./status-cards";
import type { DigestState } from "@/lib/digest-state";

const emptyState: DigestState = {
  totalSources: 0,
  sourcesAddedSinceBatch: 0,
  lastPolledAt: null,
  lastBatchAt: null,
  recentVideos: [],
};

describe("StatusCards", () => {
  it("shows total source count", () => {
    render(<StatusCards state={{ ...emptyState, totalSources: 47 }} />);
    expect(screen.getByText("47")).toBeInTheDocument();
  });

  it("shows sources added since batch as '다음 배치까지 N개'", () => {
    render(<StatusCards state={{ ...emptyState, sourcesAddedSinceBatch: 5 }} />);
    expect(screen.getByText(/다음 배치까지 5개/)).toBeInTheDocument();
  });

  it("shows formatted KST last polled at", () => {
    render(<StatusCards state={{ ...emptyState, lastPolledAt: "2026-05-28 09:00" }} />);
    expect(screen.getByText("2026-05-28 09:00")).toBeInTheDocument();
  });

  it("shows formatted KST last batch at", () => {
    render(<StatusCards state={{ ...emptyState, lastBatchAt: "2026-05-23 09:00" }} />);
    expect(screen.getByText("2026-05-23 09:00")).toBeInTheDocument();
  });

  it("shows '—' for null lastPolledAt", () => {
    render(<StatusCards state={emptyState} />);
    // Two "—" placeholders for null timestamps
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(2);
  });

  it("shows '아직 없음' label when both timestamps are null", () => {
    render(<StatusCards state={emptyState} />);
    const labels = screen.getAllByText("아직 없음");
    expect(labels.length).toBeGreaterThanOrEqual(2);
  });
});
