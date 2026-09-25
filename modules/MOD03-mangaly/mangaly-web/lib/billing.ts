/* Plans, entitlements and checkout — DEC-V1-031.
 *
 * A plan buys capability in one's own search (more requests a day, who is
 * interested in you, contact requests, the full kundli report, a relationship
 * manager). It never buys a place in anyone's results. The entitlement
 * belongs to the candidate; a parent acting for them (`forCandidate`) reads
 * the candidate's plan. */

import { getJson, postJson, query, type Outcome } from './api';

export type PlanCode = 'FREE' | 'GOLD' | 'ASSISTED';

export type EntitlementFlag =
  | 'daily_requests'
  | 'see_who_shortlisted_you'
  | 'see_who_viewed_you'
  | 'contact_unlock'
  | 'kundli_full_report'
  | 'assisted_matching';

export type Entitlements = Record<EntitlementFlag, boolean | number | null>;

export type PlanTerm = {
  months: number;
  amount_paise: number;
  gst_paise: number;
  total_paise: number;
  label: string;
};

export type Plan = {
  code: PlanCode;
  name: string;
  blurb: string;
  includes: PlanCode | null;
  terms: PlanTerm[];
  entitlements: Entitlements;
  features: string[];
};

export type Catalogue = {
  version: string;
  currency: string;
  gst_rate_bps: number;
  plans: Plan[];
};

export type MyPlan = {
  account_id: string;
  plan_code: PlanCode;
  plan_name: string;
  ends_at: string | null;
  started_at: string | null;
  term_months: number | null;
  auto_renew: boolean;
  cancelled_at: string | null;
  entitlements: Entitlements;
  usage: { requests_sent_today: number; daily_requests: number | null };
};

export type Order = {
  id: string;
  plan_code: PlanCode;
  term_months: number;
  amount_paise: number;
  gst_paise: number;
  total_paise: number;
  currency: string;
  status: 'created' | 'paid' | 'failed' | 'refunded';
  gateway: string;
  gateway_order_id: string | null;
  created_at: string;
  paid_at: string | null;
};

export type Checkout = {
  order: Order;
  /** Razorpay public key; null means the development sandbox. */
  key_id: string | null;
  gateway_order_id: string;
  amount_paise: number;
  currency: string;
  sandbox: boolean;
};

export type Confirmed = { order: Order; plan: MyPlan };

export type InterestedPerson = {
  account_id: string;
  at: string;
  photo_url: string | null;
  age: number | null;
  locality: string | null;
  profession: string | null;
};

export type InterestedList = {
  count: number;
  locked: boolean;
  plan_needed: PlanCode | null;
  people: InterestedPerson[];
};

export type Interested = { shortlisted: InterestedList; viewed: InterestedList };

/** The shape every gated action refuses with (HTTP 402). */
export type UpgradeRequiredDetail = {
  code: 'upgrade_required';
  feature: EntitlementFlag;
  plan_needed: PlanCode;
  used: number | null;
  limit: number | null;
  message: string;
};

export function getCatalogue(): Promise<Catalogue | null> {
  return getJson<Catalogue>('/billing/plans');
}

export function getMyPlan(forCandidate?: string): Promise<MyPlan | null> {
  return getJson<MyPlan>(`/billing/me${query({ for_candidate: forCandidate })}`);
}

export function createOrder(planCode: PlanCode, termMonths: number): Promise<Outcome<Checkout>> {
  return postJson<Checkout>('/billing/orders', { plan_code: planCode, term_months: termMonths });
}

export function confirmOrder(
  orderId: string,
  gatewayPaymentId: string,
  signature: string
): Promise<Outcome<Confirmed>> {
  return postJson<Confirmed>(`/billing/orders/${orderId}/confirm`, {
    gateway_payment_id: gatewayPaymentId,
    signature,
  });
}

/** Development only; the server refuses it once real keys exist. */
export function sandboxPay(orderId: string): Promise<Outcome<Confirmed>> {
  return postJson<Confirmed>(`/billing/dev/pay/${orderId}`);
}

export function cancelAutoRenew(): Promise<Outcome<MyPlan>> {
  return postJson<MyPlan>('/billing/cancel');
}

export function getInterested(forCandidate?: string): Promise<Interested | null> {
  return getJson<Interested>(`/billing/interested${query({ for_candidate: forCandidate })}`);
}

/** ₹ from paise, Indian grouping, no decimals when whole. */
export function formatRupees(paise: number): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: Number.isInteger(rupees) ? 0 : 2,
  }).format(rupees);
}

/* ---------- Razorpay Checkout (loaded only when a real key comes back) ---------- */

type RazorpaySuccess = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

type RazorpayOptions = {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description?: string;
  handler: (response: RazorpaySuccess) => void;
  modal?: { ondismiss?: () => void };
  theme?: { color?: string };
};

type RazorpayWindow = Window & {
  Razorpay?: new (options: RazorpayOptions) => { open: () => void };
};

const CHECKOUT_SRC = 'https://checkout.razorpay.com/v1/checkout.js';

function loadCheckoutScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') return resolve(false);
    if ((window as RazorpayWindow).Razorpay) return resolve(true);
    const existing = document.querySelector(`script[src="${CHECKOUT_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(true));
      existing.addEventListener('error', () => resolve(false));
      return;
    }
    const script = document.createElement('script');
    script.src = CHECKOUT_SRC;
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

/** Opens Razorpay Checkout for a real order and resolves with the payment
 *  proof to send to `confirmOrder`, or null if the person closed it. */
export async function openRazorpayCheckout(
  checkout: Checkout,
  labels: { name: string; description: string; accent: string }
): Promise<{ paymentId: string; signature: string } | null> {
  if (!checkout.key_id) return null;
  const loaded = await loadCheckoutScript();
  const Razorpay = (window as RazorpayWindow).Razorpay;
  if (!loaded || !Razorpay) return null;
  return new Promise((resolve) => {
    const instance = new Razorpay({
      key: checkout.key_id as string,
      amount: checkout.amount_paise,
      currency: checkout.currency,
      order_id: checkout.gateway_order_id,
      name: labels.name,
      description: labels.description,
      theme: { color: labels.accent },
      handler: (r) => resolve({ paymentId: r.razorpay_payment_id, signature: r.razorpay_signature }),
      modal: { ondismiss: () => resolve(null) },
    });
    instance.open();
  });
}
