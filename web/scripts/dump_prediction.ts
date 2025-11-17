import { POST as predictHandler } from "@/app/api/predict/route";

interface Args {
  homeTeam: string;
  awayTeam: string;
  season?: string;
}

function parseArgs(argv: string[]): Args {
  const args: Record<string, string> = {};
  for (let i = 0; i < argv.length; i += 1) {
    const part = argv[i];
    if (part.startsWith("--")) {
      const key = part.slice(2);
      const value = argv[i + 1];
      args[key] = value;
      i += 1;
    }
  }
  if (!args.home || !args.away) {
    throw new Error("Usage: ts-node dump_prediction.ts --home <team> --away <team> [--season <season>]");
  }
  return { homeTeam: args.home, awayTeam: args.away, season: args.season };
}

async function main() {
  const { homeTeam, awayTeam, season } = parseArgs(process.argv.slice(2));
  const body = JSON.stringify({ homeTeam, awayTeam, season });
  const response = await predictHandler(
    new Request("http://localhost/api/predict", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    }),
  );
  const json = await response.json();
  console.log(JSON.stringify(json, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
