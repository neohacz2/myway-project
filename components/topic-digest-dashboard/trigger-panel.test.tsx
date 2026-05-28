import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TriggerPanel } from "./trigger-panel";

const mockRefresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: mockRefresh }),
}));

function mockFetch(ok: boolean, message: string) {
  global.fetch = vi.fn().mockResolvedValueOnce({
    json: async () => ({ ok, message }),
  } as Response);
}

beforeEach(() => {
  vi.clearAllMocks();
  mockRefresh.mockReset();
});

describe("TriggerPanel", () => {
  it("poll 버튼 클릭 직후 disabled + 로딩 텍스트", async () => {
    global.fetch = vi.fn().mockReturnValueOnce(new Promise(() => {})); // never resolves
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 폴링"));
    expect(screen.getByText(/폴링 중/)).toBeInTheDocument();
    expect(screen.getByText(/폴링 중/).closest("button")).toBeDisabled();
  });

  it("poll 성공 시 '폴링 완료' 메시지 표시", async () => {
    mockFetch(true, "폴링 완료");
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 폴링"));
    await waitFor(() => expect(screen.getByText("폴링 완료")).toBeInTheDocument());
  });

  it("poll 실패 시 '폴링 실패' 메시지 표시", async () => {
    mockFetch(false, "폴링 실패: 오류");
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 폴링"));
    await waitFor(() => expect(screen.getByText(/폴링 실패/)).toBeInTheDocument());
  });

  it("batch 버튼 클릭 직후 disabled + 로딩 텍스트", async () => {
    global.fetch = vi.fn().mockReturnValueOnce(new Promise(() => {}));
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 배치"));
    expect(screen.getByText(/배치 중/)).toBeInTheDocument();
    expect(screen.getByText(/배치 중/).closest("button")).toBeDisabled();
  });

  it("batch 성공 시 '배치 완료' 메시지 표시", async () => {
    mockFetch(true, "배치 완료");
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 배치"));
    await waitFor(() => expect(screen.getByText("배치 완료")).toBeInTheDocument());
  });

  it("batch 실패 시 '배치 실패' 메시지 표시", async () => {
    mockFetch(false, "배치 실패: 오류");
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 배치"));
    await waitFor(() => expect(screen.getByText(/배치 실패/)).toBeInTheDocument());
  });

  it("NotebookLM 링크 href + target=_blank", () => {
    render(<TriggerPanel />);
    const link = screen.getByRole("link", { name: /NotebookLM/i });
    expect(link).toHaveAttribute("href", "https://notebooklm.google.com/");
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("poll 실행 중 batch 버튼도 disabled", async () => {
    global.fetch = vi.fn().mockReturnValueOnce(new Promise(() => {}));
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 폴링"));
    const batchBtn = screen.getByText(/지금 배치/).closest("button");
    expect(batchBtn).toBeDisabled();
  });

  it("새로고침 버튼 클릭 시 router.refresh() 호출", () => {
    render(<TriggerPanel />);
    fireEvent.click(screen.getByRole("button", { name: /새로고침/i }));
    expect(mockRefresh).toHaveBeenCalledOnce();
  });

  it("트리거 완료 후 router.refresh() 호출", async () => {
    mockFetch(true, "폴링 완료");
    render(<TriggerPanel />);
    fireEvent.click(screen.getByText("지금 폴링"));
    await waitFor(() => expect(mockRefresh).toHaveBeenCalledOnce());
  });
});
