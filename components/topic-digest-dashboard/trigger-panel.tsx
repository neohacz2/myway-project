"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Action = "poll" | "batch";

interface TriggerResult {
  ok: boolean;
  message: string;
}

export function TriggerPanel() {
  const router = useRouter();
  const [running, setRunning] = useState<Action | null>(null);
  const [result, setResult] = useState<TriggerResult | null>(null);

  async function trigger(action: Action) {
    setRunning(action);
    setResult(null);
    try {
      const res = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const data: TriggerResult = await res.json();
      setResult(data);
    } catch {
      setResult({ ok: false, message: `${action === "poll" ? "폴링" : "배치"} 실패: 네트워크 오류` });
    } finally {
      setRunning(null);
      router.refresh();
    }
  }

  const busy = running !== null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">수동 실행</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Button
            size="sm"
            disabled={busy}
            onClick={() => trigger("poll")}
          >
            {running === "poll" ? "폴링 중…" : "지금 폴링"}
          </Button>

          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => trigger("batch")}
          >
            {running === "batch" ? "배치 중…" : "지금 배치"}
          </Button>

          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            onClick={() => router.refresh()}
            aria-label="새로고침"
          >
            새로고침
          </Button>

          <a
            href="https://notebooklm.google.com/"
            target="_blank"
            rel="noreferrer"
            className="text-sm underline underline-offset-2 text-muted-foreground hover:text-foreground"
          >
            NotebookLM 열기
          </a>
        </div>

        {result && (
          <Badge variant={result.ok ? "default" : "destructive"}>
            {result.message}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}
