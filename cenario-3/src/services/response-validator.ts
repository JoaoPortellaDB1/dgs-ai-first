import { z } from "zod";
import { logger } from "../shared/logger";

/**
 * Exercício 3.1 — Harness de código: structured output + verificações determinísticas.
 *
 * O prompt (probabilístico) PEDE que o modelo cite a fonte e respeite a exceção de carga
 * perigosa. Isto aqui é a camada DETERMINÍSTICA que GARANTE: se o contrato ou os guardrails
 * não são atendidos, a resposta é BLOQUEADA e substituída por uma mensagem segura — não basta logar.
 */

// Contrato do structured output. `.strict()` rejeita campos extras que o modelo possa inventar.
export const AssistantResponseSchema = z
  .object({
    answer: z.string().min(1),
    source_document: z.array(z.string().min(1)).min(1), // ao menos uma fonte não-vazia
    confidence_score: z.number().min(0).max(1),
  })
  .strict();

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;

export type ValidationResult =
  | { ok: true; response: AssistantResponse }
  | { ok: false; reason: string; safeResponse: SafeResponse };

interface SafeResponse {
  answer: string;
  source_document: string[];
  confidence_score: number;
  blocked: true;
}

const SAFE_RESPONSE: SafeResponse = {
  answer:
    "Não consegui gerar uma resposta confiável para essa pergunta com base na documentação. " +
    "Recomendo escalar para o supervisor.",
  source_document: [],
  confidence_score: 0,
  blocked: true,
};

/** Normaliza para comparação robusta: minúsculas e sem acentos. */
function normalize(text: string): string {
  return text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

/** Detecta menção conjunta a carga perigosa + devolução (cobre devolução/devolver/devolvida). */
function mentionsDangerousReturn(answer: string): boolean {
  const t = normalize(answer);
  return t.includes("carga perigosa") && /devolu[cv]/.test(t);
}

/** Detecta a negativa explícita (a resposta correta é que NÃO pode devolver). */
function containsNegation(answer: string): boolean {
  const t = normalize(answer);
  return [
    "nao pode",
    "nao podem",
    "nao e possivel",
    "nao sao elegiveis",
    "nao e permitid",
    "nao elegiv",
    "impossivel",
  ].some((p) => t.includes(p));
}

function reject(reason: string, details?: unknown): ValidationResult {
  logger.warn({ reason, details }, "resposta do assistente bloqueada pelo harness");
  return { ok: false, reason, safeResponse: SAFE_RESPONSE };
}

/**
 * Valida a resposta do assistente. Ordem: contrato (structured output) → guardrails de conteúdo.
 * Em qualquer falha, BLOQUEIA e devolve a resposta segura.
 */
export function validateAssistantResponse(raw: unknown): ValidationResult {
  // 1. Structured output: a resposta bate com o contrato?
  const parsed = AssistantResponseSchema.safeParse(raw);
  if (!parsed.success) {
    return reject("structured_output_invalido", parsed.error.issues);
  }
  const response = parsed.data;

  // Guardrail 1: fonte obrigatória (o schema já exige, mas a checagem explícita documenta a regra).
  if (response.source_document.length === 0) {
    return reject("sem_source_document");
  }

  // Guardrail 2: carga perigosa + devolução SEM negativa → bloqueia (inversão de regra do POL-001).
  if (mentionsDangerousReturn(response.answer) && !containsNegation(response.answer)) {
    return reject("carga_perigosa_devolucao_sem_negativa");
  }

  return { ok: true, response };
}
