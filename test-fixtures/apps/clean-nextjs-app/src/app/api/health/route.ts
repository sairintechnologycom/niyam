// Health check endpoint for monitoring
export async function GET() {
  // route: /health
  return new Response("OK", { status: 200 });
}
