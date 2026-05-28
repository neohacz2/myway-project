import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { VideoList } from "./video-list";

const makeVideos = (n: number) =>
  Array.from({ length: n }, (_, i) => ({
    id: `vid${i}`,
    url: `https://www.youtube.com/watch?v=vid${i}`,
  }));

describe("VideoList", () => {
  it("renders empty state message when no videos", () => {
    render(<VideoList videos={[]} />);
    expect(screen.getByText("아직 적재된 영상이 없습니다")).toBeInTheDocument();
  });

  it("renders at most 10 links when 15 videos provided", () => {
    render(<VideoList videos={makeVideos(15)} />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(10);
  });

  it("each link href matches youtube URL pattern", () => {
    render(<VideoList videos={[{ id: "ABC123", url: "https://www.youtube.com/watch?v=ABC123" }]} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "https://www.youtube.com/watch?v=ABC123");
  });

  it("links open in new tab", () => {
    render(<VideoList videos={makeVideos(1)} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("target", "_blank");
  });
});
