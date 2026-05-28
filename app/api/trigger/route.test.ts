import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

const spawnMock = vi.fn();

vi.mock("child_process", () => ({
  default: { spawn: spawnMock },
  spawn: spawnMock,
}));

// import after mock
const { POST } = await import("./route");

function makeSpawnChild(exitCode: number, stderr = "") {
  return {
    stdout: { on: vi.fn() },
    stderr: {
      on: vi.fn((event: string, cb: (d: Buffer) => void) => {
        if (event === "data" && stderr) cb(Buffer.from(stderr));
      }),
    },
    on: vi.fn((event: string, cb: (code: number) => void) => {
      if (event === "close") setTimeout(() => cb(exitCode), 0);
    }),
  };
}

function makeRequest(body: unknown) {
  return new NextRequest("http://localhost/api/trigger", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => spawnMock.mockReset());

describe("POST /api/trigger", () => {
  it("returns 400 for unknown action", async () => {
    const res = await POST(makeRequest({ action: "unknown" }));
    expect(res.status).toBe(400);
  });

  it("returns {ok:true, message:'폴링 완료'} on poll success", async () => {
    spawnMock.mockReturnValue(makeSpawnChild(0));
    const res = await POST(makeRequest({ action: "poll" }));
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(body.message).toBe("폴링 완료");
  });

  it("returns {ok:true, message:'배치 완료'} on batch success", async () => {
    spawnMock.mockReturnValue(makeSpawnChild(0));
    const res = await POST(makeRequest({ action: "batch" }));
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(body.message).toBe("배치 완료");
  });

  it("returns {ok:false} on poll failure (exit code 1)", async () => {
    spawnMock.mockReturnValue(makeSpawnChild(1, "channel error"));
    const res = await POST(makeRequest({ action: "poll" }));
    const body = await res.json();
    expect(body.ok).toBe(false);
    expect(body.message).toMatch(/폴링 실패/);
  });

  it("returns {ok:false} on batch failure", async () => {
    spawnMock.mockReturnValue(makeSpawnChild(1));
    const res = await POST(makeRequest({ action: "batch" }));
    const body = await res.json();
    expect(body.ok).toBe(false);
    expect(body.message).toMatch(/배치 실패/);
  });
});
