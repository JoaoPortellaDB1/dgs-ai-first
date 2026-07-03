import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { randomUUID } from "node:crypto";
import { logger } from "../../shared/logger";
import { parseQueryRequest } from "./validator";

/**
 * Query endpoint — T-02.
 * Recebe a pergunta do atendente, valida (Zod) e responde.
 * A busca (T-03) e a geração (T-05) ainda são stub nesta task.
 */
export async function queryHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const correlationId = request.headers.get("x-correlation-id") ?? randomUUID();
  const log = logger.child({ correlationId, invocationId: context.invocationId });

  // JSON malformado não pode derrubar o endpoint com 500 — vira 400 controlado.
  let rawBody: unknown;
  try {
    rawBody = await request.json();
  } catch {
    log.warn("body não é JSON válido");
    return json(400, { error: "Body deve ser JSON válido" }, correlationId);
  }

  const parsed = parseQueryRequest(rawBody);
  if (!parsed.success) {
    log.warn({ issues: parsed.details }, "validação de input falhou");
    return json(400, { error: parsed.error, details: parsed.details }, correlationId);
  }

  // A pergunta pode conter dado do cliente — só em nível debug, nunca em info.
  log.debug({ question: parsed.data.question }, "query recebida");
  log.info({ hasTier: Boolean(parsed.data.clientTier) }, "query válida, processando");

  // Stub — substituído por retrieval + geração nas tasks T-03..T-05.
  return json(
    200,
    {
      answer: null,
      source_document: [],
      confidence: "pending",
      note: "retrieval/geração ainda não implementados (T-03..T-05)",
    },
    correlationId,
  );
}

function json(status: number, body: unknown, correlationId: string): HttpResponseInit {
  return {
    status,
    headers: { "content-type": "application/json", "x-correlation-id": correlationId },
    jsonBody: body,
  };
}

app.http("query", {
  methods: ["POST"],
  authLevel: "function",
  route: "query",
  handler: queryHandler,
});
