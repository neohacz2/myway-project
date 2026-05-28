import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DigestState } from "@/lib/digest-state";

interface Props {
  state: DigestState;
}

export function StatusCards({ state }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            총 적재 영상
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{state.totalSources}</p>
          <p className="text-xs text-muted-foreground mt-1">누적 source 수</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            다음 배치
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{state.sourcesAddedSinceBatch}</p>
          <p className="text-xs text-muted-foreground mt-1">
            다음 배치까지 {state.sourcesAddedSinceBatch}개
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            마지막 폴링
          </CardTitle>
        </CardHeader>
        <CardContent>
          {state.lastPolledAt ? (
            <p className="text-sm font-semibold">{state.lastPolledAt}</p>
          ) : (
            <>
              <p className="text-sm font-semibold">—</p>
              <p className="text-xs text-muted-foreground mt-1">아직 없음</p>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            마지막 배치
          </CardTitle>
        </CardHeader>
        <CardContent>
          {state.lastBatchAt ? (
            <p className="text-sm font-semibold">{state.lastBatchAt}</p>
          ) : (
            <>
              <p className="text-sm font-semibold">—</p>
              <p className="text-xs text-muted-foreground mt-1">아직 없음</p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
