import { readDigestState } from "@/lib/digest-state";
import { StatusCards } from "@/components/topic-digest-dashboard/status-cards";

export default function DashboardPage() {
  const state = readDigestState();
  return (
    <main className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Topic Digest</h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI 에이전트 / LLM 일반 · YouTube 자동 적재 파이프라인
          </p>
        </div>
      </div>
      <StatusCards state={state} />
      {/* VideoList and TriggerPanel added in Task 2 and 4 */}
    </main>
  );
}
