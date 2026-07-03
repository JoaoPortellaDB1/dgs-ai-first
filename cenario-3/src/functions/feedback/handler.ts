import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { randomUUID } from "node:crypto";
import { CosmosClient } from "@azure/cosmos";
import { logger } from "../../shared/logger";
import { FeedbackSchema } from "./validator";

/**
 * Exercício 3.2 — versão reescrita do feedback-handler seguindo o AGENTS.md.
 * Corrige: `as any` → Zod; `console.log` → pino; `require` dinâmico → import estático;
 * attendantEmail (PII) não é logado; cliente Cosmos como singleton de módulo; erro tratado.
 */

// Cliente Cosmos criado uma vez por processo (não a cada request).
const cosmos = new CosmosClient(process.env.COSMOS_CONNECTION_STRING ?? "");
const container = cosmos.database("novatech").container("feedbacks");

export async function feedbackHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const correlationId = request.headers.get("x-correlation-id") ?? randomUUID();
  const log = logger.child({ correlationId, invocationId: context.invocationId });

  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return json(400, { error: "Body deve ser JSON válido" }, correlationId);
  }

  const parsed = FeedbackSchema.safeParse(raw);
  if (!parsed.success) {
    log.warn({ issues: parsed.error.issues }, "feedback inválido");
    return json(400, { error: "Feedback inválido", details: parsed.error.issues }, correlationId);
  }

  const feedback = { ...parsed.data, timestamp: new Date().toISOString() };

  // NUNCA logar attendantEmail (dado pessoal). Só metadados não sensíveis.
  log.info({ queryId: feedback.queryId, rating: feedback.rating }, "feedback recebido");

  try {
    await container.items.create(feedback);
  } catch (err) {
    log.error({ err }, "falha ao persistir feedback");
    return json(500, { error: "Não foi possível registrar o feedback" }, correlationId);
  }

  return json(201, { status: "registrado" }, correlationId);
}

function json(status: number, body: unknown, correlationId: string): HttpResponseInit {
  return {
    status,
    headers: { "content-type": "application/json", "x-correlation-id": correlationId },
    jsonBody: body,
  };
}

app.http("feedback", {
  methods: ["POST"],
  authLevel: "function",
  route: "feedback",
  handler: feedbackHandler,
});
