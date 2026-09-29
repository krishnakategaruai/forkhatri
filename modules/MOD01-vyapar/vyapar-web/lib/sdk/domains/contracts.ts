// [FE2 — imp-backend-d] Contracts and milestone payments.
//
// A client (the side that pays) and a provider turn an accepted enquiry into
// a contract. Fixed-price contracts are paid milestone by milestone
// (pending → funded/"held" → submitted → released/"paid", or back to
// rejected/"changes requested"); hourly contracts are paid from weekly
// timesheets. Money is a ledger, not escrow: funding goes through the same
// Payment Bridge checkout boosts use, and `sandbox` says when it is the
// development sandbox. Amounts are integer paise, dates ISO 8601.
import { seg, type VyaparClient } from "../client";
import type { Page } from "../types";

export type ContractKind = "fixed" | "hourly";
export type ContractState = "draft" | "proposed" | "active" | "disputed" | "completed" | "cancelled";
export type ContractRole = "client" | "provider";
export type MilestoneState = "pending" | "funded" | "submitted" | "approved" | "released" | "rejected" | "refunded";
export type TimesheetState = "submitted" | "approved" | "paid" | "rejected";
export type DisputeOutcome = "resolved_client" | "resolved_provider" | "closed";

export interface ContractSummary {
  id: string;
  enquiry_id: string;
  opportunity_id: string | null;
  client_member_id: string;
  provider_member_id: string;
  provider_listing_id: string | null;
  title: string;
  kind: ContractKind;
  currency: string;
  total_paise: number;
  state: ContractState;
  my_role: ContractRole | string;
  counterpart_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Milestone {
  id: string;
  title: string;
  description: string | null;
  amount_paise: number;
  due_date: string | null;
  sort: number;
  state: MilestoneState;
  funded_order_id: string | null;
  checkout_url: string | null;
  funded_at: string | null;
  submitted_at: string | null;
  submission_note: string | null;
  approved_at: string | null;
  released_at: string | null;
  rejected_at: string | null;
  reject_note: string | null;
  /** Set while submitted: when silence approves it (14 days after submit). */
  auto_release_at: string | null;
  auto_approve: boolean;
}

export interface LedgerSummary {
  /** held − released − fee − refunded */
  held_paise: number;
  released_paise: number;
  refunded_paise: number;
  fee_paise: number;
}

export interface LedgerEntry {
  id: number;
  milestone_id: string | null;
  entry: "held" | "released" | "refunded" | "fee" | string;
  amount_paise: number;
  payment_order_id: string | null;
  note: string | null;
  created_at: string;
}

export interface Timesheet {
  id: string;
  week_start: string;
  hours: number;
  note: string | null;
  state: TimesheetState;
  reject_note: string | null;
  amount_paise: number;
  milestone_id: string | null;
  submitted_at: string;
  approved_at: string | null;
  paid_at: string | null;
}

export interface ContractDispute {
  id: string;
  contract_id: string;
  milestone_id: string | null;
  opened_by: string;
  reason: string;
  state: string;
  notes: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface ContractEvent {
  id: number;
  milestone_id: string | null;
  /** null = the system acted (payment trigger or the auto-release pass). */
  actor_member_id: string | null;
  type: string;
  data: Record<string, unknown>;
  created_at: string;
}

export interface Contract extends ContractSummary {
  description: string | null;
  hourly_rate_paise: number | null;
  weekly_hours_cap: number | null;
  platform_fee_bps: number;
  proposed_at: string | null;
  accepted_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  cancelled_by: string | null;
  cancel_reason: string | null;
  client_name: string | null;
  provider_name: string | null;
  milestones: Milestone[];
  ledger: LedgerSummary;
  ledger_entries: LedgerEntry[];
  timesheets: Timesheet[];
  disputes: ContractDispute[];
  /** Newest first, capped at 100. */
  events: ContractEvent[];
}

export interface ContractMilestoneInput {
  title: string;
  description?: string | null;
  amount_paise: number;
  due_date?: string | null;
}

export interface ContractCreateInput {
  enquiry_id: string;
  title: string;
  description?: string | null;
  kind?: ContractKind;
  total_paise: number;
  hourly_rate_paise?: number | null;
  weekly_hours_cap?: number | null;
  provider_listing_id?: string | null;
  milestones?: ContractMilestoneInput[];
  /** true: send it to the provider straight away (otherwise it stays a draft). */
  propose?: boolean;
}

export interface Funding {
  milestone_id: string;
  state: MilestoneState | string;
  amount_paise: number;
  payment_order_id: string | null;
  checkout_url: string | null;
  /** true while payments run through the development sandbox. */
  sandbox: boolean;
  /** "gatewayUnavailable" when no checkout could be created; retry later. */
  notice?: string | null;
}

export interface TimesheetInput {
  /** A Monday, "YYYY-MM-DD". */
  week_start: string;
  hours: number;
  note?: string | null;
}

export interface ContractListParams {
  role?: ContractRole | "all";
  state?: ContractState;
  limit?: number;
  cursor?: string | null;
}

export function contractsApi(c: VyaparClient) {
  const base = (id: string) => `/v1/contracts/${seg(id)}`;
  const ms = (id: string, mid: string) => `${base(id)}/milestones/${seg(mid)}`;
  return {
    /** createContract — client only; the enquiry must be accepted */
    create: (body: ContractCreateInput, idempotencyKey?: string) => c.post<Contract>("/v1/contracts", body, { idempotencyKey }),
    /** listMyContracts */
    list: (params: ContractListParams = {}) => c.get<Page<ContractSummary>>("/v1/contracts", { ...params }),
    /** getContract */
    get: (id: string) => c.get<Contract>(base(id)),
    propose: (id: string) => c.post<Contract>(`${base(id)}/propose`),
    accept: (id: string) => c.post<Contract>(`${base(id)}/accept`),
    cancel: (id: string, reason?: string) => c.post<Contract>(`${base(id)}/cancel`, reason ? { reason } : undefined),
    complete: (id: string) => c.post<Contract>(`${base(id)}/complete`),
    addMilestone: (id: string, body: ContractMilestoneInput) => c.post<Contract>(`${base(id)}/milestones`, body),
    updateMilestone: (id: string, mid: string, patch: Partial<ContractMilestoneInput> & { sort?: number }) => c.patch<Contract>(ms(id, mid), patch),
    deleteMilestone: (id: string, mid: string) => c.delete<Contract>(ms(id, mid)),
    /** fundMilestone — returns the checkout to open; the milestone is funded only when the gateway confirms */
    fundMilestone: (id: string, mid: string) => c.post<Funding>(`${ms(id, mid)}/fund`),
    submitMilestone: (id: string, mid: string, note?: string) => c.post<Contract>(`${ms(id, mid)}/submit`, note ? { note } : undefined),
    approveMilestone: (id: string, mid: string) => c.post<Contract>(`${ms(id, mid)}/approve`),
    rejectMilestone: (id: string, mid: string, note: string) => c.post<Contract>(`${ms(id, mid)}/reject`, { note }),
    openDispute: (id: string, reason: string, milestoneId?: string | null) =>
      c.post<Contract>(`${base(id)}/disputes`, { reason, milestone_id: milestoneId ?? undefined }),
    submitTimesheet: (id: string, body: TimesheetInput) => c.post<Contract>(`${base(id)}/timesheets`, body),
    /** approveTimesheet — opens a checkout, like fundMilestone */
    approveTimesheet: (id: string, tid: string) => c.post<Funding>(`${base(id)}/timesheets/${seg(tid)}/approve`),
    rejectTimesheet: (id: string, tid: string, note: string) => c.post<Contract>(`${base(id)}/timesheets/${seg(tid)}/reject`, { note }),
  };
}

export type ContractsApi = ReturnType<typeof contractsApi>;
