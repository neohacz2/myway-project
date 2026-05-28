import { spawn } from "child_process";
import { join } from "path";
import { NextRequest, NextResponse } from "next/server";

const LABELS: Record<string, { ok: string; fail: string }> = {
  poll: { ok: "폴링 완료", fail: "폴링 실패" },
  batch: { ok: "배치 완료", fail: "배치 실패" },
};

export async function POST(req: NextRequest) {
  let action: string;
  try {
    const body = await req.json();
    action = body?.action;
  } catch {
    return NextResponse.json({ ok: false, message: "잘못된 요청 형식" }, { status: 400 });
  }

  if (!LABELS[action]) {
    return NextResponse.json({ ok: false, message: "알 수 없는 action" }, { status: 400 });
  }

  const cwd =
    process.env.TOPIC_DIGEST_DIR ??
    join(process.cwd(), "scripts/topic-digest");

  const result = await runPython(["run", "python", "-m", `topic_digest.${action}`], cwd);
  const label = LABELS[action];

  if (result.code === 0) {
    return NextResponse.json({ ok: true, message: label.ok });
  }

  return NextResponse.json({
    ok: false,
    message: `${label.fail}: ${result.stderr.trim() || "exit code " + result.code}`,
  });
}

function runPython(
  args: string[],
  cwd: string
): Promise<{ code: number; stderr: string }> {
  return new Promise((resolve) => {
    let stderr = "";
    const child = spawn("uv", args, { cwd });
    child.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
    child.on("error", (err: Error) => resolve({ code: 1, stderr: err.message }));
    child.on("close", (code: number | null) => resolve({ code: code ?? 1, stderr }));
  });
}
