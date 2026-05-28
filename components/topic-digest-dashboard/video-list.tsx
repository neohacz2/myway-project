import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Video {
  id: string;
  url: string;
}

interface Props {
  videos: Video[];
}

export function VideoList({ videos }: Props) {
  const shown = videos.slice(0, 10);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">최근 적재 영상</CardTitle>
          {videos.length > 0 && (
            <span className="text-xs text-muted-foreground">
              전체 {videos.length}개 중 최신 {shown.length}개
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {shown.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-6">
            아직 적재된 영상이 없습니다
          </p>
        ) : (
          <ul className="space-y-2">
            {shown.map((v) => (
              <li key={v.id} className="flex items-center gap-3 py-1.5 border-b last:border-0">
                <a
                  href={v.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm underline underline-offset-2 truncate hover:text-foreground text-muted-foreground"
                >
                  {v.id}
                </a>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
